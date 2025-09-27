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
}


def configure(parameter):
    """Register the active ``Parameter`` instance for downstream hooks."""

    _CONTEXT['parameter'] = parameter
    _CONTEXT['client'] = None


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


def log_fallback(block, reason, detail=None):
    message = '[LLM %s] fallback: %s' % (block, reason)
    if detail:
        message = message + ' (%s)' % detail
    print message


__all__ = ['configure', 'get_client', 'get_parameter', 'firm_enabled', 'log_fallback']
