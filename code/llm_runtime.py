# -*- coding: utf-8 -*-
"""Shared LLM runtime context for the Python 2 simulation."""

from __future__ import absolute_import

try:
    from llm_bridge_client import LLMBridgeClient
except ImportError:  # pragma: no cover - package import fallback
    from .llm_bridge_client import LLMBridgeClient

_CONTEXT = {
    'parameter': None,
    'client': None,
    'counters': {},
}

_COUNTER_TEMPLATE = {
    'calls': 0,
    'fallbacks': 0,
    'timeouts': 0,
}

_GUARD_PRESET_FACTORS = {
    'baseline': 1.0,
    'tight': 0.5,
    'loose': 1.5,
}

_BANK_GUARD_EPSILON = {
    'baseline': 1e-6,
    'tight': 0.0,
    'loose': 1e-6,
}


def configure(parameter):
    """Register the active ``Parameter`` instance for downstream hooks."""

    _CONTEXT['parameter'] = parameter
    _CONTEXT['client'] = None
    _CONTEXT['counters'] = {}


def get_parameter():
    return _CONTEXT.get('parameter')


def get_client():
    parameter = get_parameter()
    if not parameter:
        return None
    client = _CONTEXT.get('client')
    if client is None:
        timeout = parameter.llm_timeout_ms or 0
        timeout = float(timeout) / 1000.0
        client = LLMBridgeClient(parameter.llm_server_url, timeout=timeout)
        _CONTEXT['client'] = client
    return client


def firm_enabled():
    parameter = get_parameter()
    return bool(parameter and parameter.use_llm_firm_pricing)


def bank_enabled():
    parameter = get_parameter()
    return bool(parameter and parameter.use_llm_bank_credit)


def wage_enabled():
    parameter = get_parameter()
    return bool(parameter and parameter.use_llm_wage)


def log_fallback(block, reason, detail=None):
    _register_fallback(block, reason)
    message = '[LLM %s] fallback: %s' % (block, reason)
    if detail:
        message = message + ' (%s)' % detail
    print message


def log_llm_call(block):
    _ensure_block_counter(block)['calls'] += 1


def reset_counters(block=None):
    if block is None:
        _CONTEXT['counters'] = {}
        return
    counters = _CONTEXT.get('counters')
    if counters is None:
        _CONTEXT['counters'] = {}
        counters = _CONTEXT['counters']
    counters[str(block)] = _COUNTER_TEMPLATE.copy()


def ensure_counter(block):
    return _ensure_block_counter(block)


def get_counters_snapshot():
    counters = _CONTEXT.get('counters') or {}
    snapshot = {}
    for block, values in counters.items():
        if values is None:
            continue
        snapshot[block] = values.copy()
    return snapshot


def get_firm_guard_caps():
    """Return effective guard caps for firm price/expectation decisions."""

    parameter = get_parameter()
    if parameter:
        custom = getattr(parameter, 'firm_guard_caps', None)
        if isinstance(custom, dict):
            return _sanitise_firm_caps(custom)

    preset = 'baseline'
    if parameter:
        preset = _resolve_guard_preset(parameter, 'firm_guard_preset')
    factor = _GUARD_PRESET_FACTORS.get(preset, 1.0)
    base = {
        'max_price_step': 0.04,
        'max_expectation_bias': 0.04,
    }
    return _scale_caps(base, factor)


def get_wage_guard_caps():
    """Return guard caps for wage decisions shared by workers and firms."""

    parameter = get_parameter()

    if parameter:
        custom = getattr(parameter, 'wage_guard_caps', None)
        if isinstance(custom, dict):
            return _sanitise_wage_caps(custom, parameter)

    base_delta = _default_wage_delta(parameter)

    preset = 'baseline'
    if parameter:
        preset = _resolve_guard_preset(parameter, 'wage_guard_preset')
    factor = _GUARD_PRESET_FACTORS.get(preset, 1.0)

    return {
        'max_wage_step': base_delta * factor,
    }


def get_bank_guard_config():
    """Return spread guard bounds (bps) and epsilon."""

    base_min = 50.0
    base_max = 500.0
    parameter = get_parameter()

    if parameter:
        custom_bounds = getattr(parameter, 'bank_guard_bounds', None)
        bounds = _sanitise_bank_bounds(custom_bounds)
        if bounds is not None:
            base_min, base_max = bounds

    preset = 'baseline'
    if parameter:
        preset = _resolve_guard_preset(parameter, 'bank_guard_preset')
    factor = _GUARD_PRESET_FACTORS.get(preset, 1.0)

    min_bps = base_min
    if preset == 'tight':
        min_bps = base_min + 50.0

    window = max(0.0, base_max - base_min)
    max_bps = min_bps + window * factor
    if max_bps < min_bps:
        max_bps = min_bps

    epsilon = _BANK_GUARD_EPSILON.get(preset, 1e-6)
    if parameter:
        custom_eps = getattr(parameter, 'bank_guard_epsilon', None)
        try:
            if custom_eps is not None:
                epsilon = max(0.0, float(custom_eps))
        except (TypeError, ValueError):
            pass

    return {
        'min_bps': min_bps,
        'max_bps': max_bps,
        'epsilon': epsilon,
    }


def _resolve_guard_preset(parameter, attribute):
    value = getattr(parameter, attribute, None)
    if value:
        return _normalise_preset(value)
    fallback = getattr(parameter, 'llm_guard_preset', None)
    if fallback:
        return _normalise_preset(fallback)
    return 'baseline'


def _normalise_preset(value):
    text = str(value).strip().lower()
    if text in _GUARD_PRESET_FACTORS:
        return text
    return 'baseline'


def _scale_caps(base_caps, factor):
    scaled = {}
    for key, value in base_caps.items():
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        scaled[key] = max(0.0, numeric * factor)
    return scaled


def _sanitise_firm_caps(custom):
    if not isinstance(custom, dict):
        return {
            'max_price_step': 0.04,
            'max_expectation_bias': 0.04,
        }

    caps = {}
    for key in ('max_price_step', 'max_expectation_bias'):
        value = custom.get(key)
        if value is None:
            continue
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        if numeric < 0.0:
            numeric = 0.0
        caps[key] = numeric
    if 'max_price_step' not in caps:
        caps['max_price_step'] = 0.04
    if 'max_expectation_bias' not in caps:
        caps['max_expectation_bias'] = 0.04
    return caps


def _sanitise_wage_caps(custom, parameter):
    base_delta = _default_wage_delta(parameter)

    if not isinstance(custom, dict):
        return {
            'max_wage_step': base_delta,
        }

    value = custom.get('max_wage_step')
    if value is None:
        return {
            'max_wage_step': base_delta,
        }

    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = base_delta

    if numeric < 0.0:
        numeric = 0.0

    return {
        'max_wage_step': numeric,
    }


def _default_wage_delta(parameter):
    base = 0.04
    if parameter:
        try:
            base = float(getattr(parameter, 'delta', base))
        except (TypeError, ValueError):
            base = 0.04
    if base < 0.0:
        base = 0.0
    return base


def _sanitise_bank_bounds(value):
    if not value:
        return None
    try:
        minimum, maximum = value
        minimum = float(minimum)
        maximum = float(maximum)
    except (TypeError, ValueError, IndexError):
        return None
    if minimum < 0.0:
        minimum = 0.0
    if maximum < 0.0:
        maximum = 0.0
    if maximum < minimum:
        minimum, maximum = maximum, minimum
    return (minimum, maximum)


def _ensure_block_counter(block):
    counters = _CONTEXT.get('counters')
    if counters is None:
        counters = {}
        _CONTEXT['counters'] = counters
    key = str(block)
    current = counters.get(key)
    if current is None:
        current = _COUNTER_TEMPLATE.copy()
        counters[key] = current
    return current


def _register_fallback(block, reason):
    counter = _ensure_block_counter(block)
    counter['fallbacks'] += 1
    if str(reason) == 'timeout':
        counter['timeouts'] += 1


__all__ = [
    'configure',
    'get_client',
    'get_parameter',
    'firm_enabled',
    'bank_enabled',
    'wage_enabled',
    'log_fallback',
    'log_llm_call',
    'reset_counters',
    'ensure_counter',
    'get_counters_snapshot',
    'get_firm_guard_caps',
    'get_wage_guard_caps',
    'get_bank_guard_config',
]
