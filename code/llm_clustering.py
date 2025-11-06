# -*- coding: utf-8 -*-
"""
Agent clustering for reducing LLM API calls.

Instead of querying the LLM for each individual agent, cluster similar agents
and make ONE API call per cluster, then apply the policy to all members.

Expected impact: 95-98% reduction in API calls (200K → 3K-5K)
"""

from __future__ import division
from collections import defaultdict


class AgentClusterer(object):
    """Clusters agents by similar characteristics to reduce API calls."""

    def __init__(self, feature_buckets):
        """
        Initialize clusterer with feature bucket definitions.

        Args:
            feature_buckets: dict mapping feature names to bucket boundaries
                Example: {
                    'leverage': [0, 1, 2, 3, 4, 999],      # Creates 5 buckets
                    'productivity': [0, 0.8, 1.0, 1.2, 999],
                    'sector': ['tradable', 'non_tradable']  # Categorical
                }
        """
        self.feature_buckets = feature_buckets

    def cluster_agents(self, agents, feature_extractors):
        """
        Cluster agents by their feature values.

        Args:
            agents: list of agent objects (firms, banks, workers, etc.)
            feature_extractors: dict of {feature_name: function(agent) -> value}
                Example: {
                    'leverage': lambda firm: firm.debt / firm.A,
                    'productivity': lambda firm: firm.phi,
                    'sector': lambda firm: 'tradable' if firm.tradable else 'non_tradable'
                }

        Returns:
            dict of {cluster_key: [agent_objects]}
        """
        clusters = defaultdict(list)

        for agent in agents:
            cluster_key = self._get_cluster_key(agent, feature_extractors)
            clusters[cluster_key].append(agent)

        return dict(clusters)

    def _get_cluster_key(self, agent, extractors):
        """
        Generate unique cluster identifier for an agent.

        Returns string like: "leverage=2-3|productivity=0.8-1.0|sector=tradable"
        """
        key_parts = []

        for feature_name, extractor in sorted(extractors.items()):
            try:
                value = extractor(agent)
                bucket = self._bucketize(value, feature_name)
                key_parts.append('%s=%s' % (feature_name, bucket))
            except (AttributeError, KeyError, TypeError, ZeroDivisionError):
                # If feature extraction fails, use "unknown" bucket
                key_parts.append('%s=unknown' % feature_name)

        return '|'.join(key_parts)

    def _bucketize(self, value, feature_name):
        """
        Convert a feature value to its bucket label.

        For numeric features: returns range like "2-3"
        For categorical: returns the value itself
        """
        buckets = self.feature_buckets.get(feature_name, [])

        if not buckets:
            # No buckets defined, return value as-is
            return str(value)

        # Categorical feature (list of strings)
        if isinstance(buckets, list) and len(buckets) > 0 and isinstance(buckets[0], str):
            if value in buckets:
                return str(value)
            else:
                return 'other'

        # Numeric feature (list of boundary values)
        if isinstance(value, (int, float)):
            for i in range(len(buckets) - 1):
                if buckets[i] <= value < buckets[i + 1]:
                    lower = buckets[i]
                    upper = buckets[i + 1]
                    if upper == float('inf') or upper == 999:
                        return '%s+' % lower
                    else:
                        return '%s-%s' % (lower, upper)

        # Fallback
        return 'unknown'

    def get_cluster_summary(self, cluster_agents, extractors):
        """
        Generate summary statistics for a cluster (for LLM prompt).

        Args:
            cluster_agents: list of agents in this cluster
            extractors: dict of {feature_name: extractor_function}

        Returns:
            dict with cluster statistics
        """
        if not cluster_agents:
            return {'count': 0, 'features': {}}

        features_summary = {}

        for feature_name, extractor in extractors.items():
            try:
                values = []
                for agent in cluster_agents:
                    try:
                        val = extractor(agent)
                        if isinstance(val, (int, float)):
                            values.append(float(val))
                    except:
                        pass

                if values:
                    features_summary[feature_name] = {
                        'min': min(values),
                        'max': max(values),
                        'avg': sum(values) / len(values),
                        'count': len(values)
                    }
            except:
                pass

        # Get representative agent (median by first feature)
        representative = None
        if cluster_agents:
            representative = cluster_agents[len(cluster_agents) // 2]

        return {
            'count': len(cluster_agents),
            'features': features_summary,
            'representative': representative,
            'cluster_key': self._get_cluster_key(cluster_agents[0], extractors) if cluster_agents else None
        }


class PolicyEvaluator(object):
    """
    Evaluates policy formulas returned by LLM against specific agent values.

    Example:
        policy = {
            "approval_formula": "leverage < 3.0 AND productivity > 0.9",
            "interest_rate_formula": "0.05 + 0.5 * (leverage - 2.0)",
            "credit_limit_pct": 0.25
        }

        evaluator = PolicyEvaluator()
        decision = evaluator.apply_credit_policy(policy, firm_values)
    """

    def apply_credit_policy(self, policy, context):
        """
        Apply LLM credit policy to specific firm values.

        Args:
            policy: dict with 'approval_formula', 'interest_rate_formula', etc.
            context: dict with specific values like {'leverage': 2.3, 'productivity': 1.05}

        Returns:
            dict with 'approve', 'interest_rate', 'credit_limit', 'probability'
        """
        # Evaluate approval (boolean formula)
        approved = True  # Default to approve if formula missing
        if 'approval_formula' in policy:
            try:
                approved = self._eval_boolean(policy['approval_formula'], context)
            except:
                # If evaluation fails, use baseline logic
                approved = context.get('leverage', 999) < 4.0

        # Calculate interest rate (numeric formula)
        interest_rate = context.get('base_rate', 0.05)
        if 'interest_rate_formula' in policy:
            try:
                interest_rate = self._eval_numeric(policy['interest_rate_formula'], context)
            except:
                # Fallback: base + leverage premium
                interest_rate = 0.05 + 0.01 * context.get('leverage', 2.0)

        # Credit limit
        credit_limit = context.get('assets', 0) * policy.get('credit_limit_pct', 0.25)

        return {
            'approve': approved,
            'interest_rate': max(0.0, min(0.5, interest_rate)),  # Clamp 0-50%
            'credit_limit': max(0.0, credit_limit),
            'probability': policy.get('confidence', 0.8)
        }

    def _eval_boolean(self, formula, context):
        """
        Safely evaluate boolean formula like "leverage < 3.0 AND productivity > 0.9"

        Uses a whitelist of safe operators only.
        """
        # Simple implementation: string substitution + eval with safety checks
        # Production version should use proper parser (pyparsing, ast, etc.)

        formula = str(formula)

        # Substitute variables
        for key, value in context.items():
            # Replace variable name with its value
            formula = formula.replace(key, str(value))

        # Replace logical operators with Python equivalents
        formula = formula.replace(' AND ', ' and ')
        formula = formula.replace(' OR ', ' or ')
        formula = formula.replace(' NOT ', ' not ')

        # Safety check: only allow whitelisted characters
        allowed = set('0123456789.<>=()andortnue -+*/.')
        if not all(c in allowed or c.isspace() for c in formula.lower()):
            raise ValueError('Unsafe formula: contains non-whitelisted characters')

        try:
            # Evaluate in restricted namespace
            result = eval(formula, {"__builtins__": {}}, {})
            return bool(result)
        except:
            # If evaluation fails, return False (reject)
            return False

    def _eval_numeric(self, formula, context):
        """
        Safely evaluate numeric formula like "0.05 + 0.5 * (leverage - 2.0)"

        Returns float result.
        """
        formula = str(formula)

        # Substitute variables with their values
        for key, value in context.items():
            formula = formula.replace(key, str(value))

        # Safety check
        allowed = set('0123456789.()+-*/ ')
        if not all(c in allowed for c in formula):
            raise ValueError('Unsafe formula: contains non-whitelisted characters')

        try:
            # Evaluate in restricted namespace
            result = eval(formula, {"__builtins__": {}}, {})
            return float(result)
        except:
            # If evaluation fails, return default
            return context.get('base_rate', 0.05)


# Example usage and testing
if __name__ == '__main__':
    # Create mock firm objects
    class MockFirm(object):
        def __init__(self, ide, A, debt, phi, tradable):
            self.ide = ide
            self.A = A
            self.debt = debt
            self.phi = phi
            self.tradable = tradable

    # Create 10 test firms
    firms = [
        MockFirm('F0', 100, 200, 1.0, True),   # leverage=2.0, productive, tradable
        MockFirm('F1', 100, 220, 1.05, True),  # Similar to F0
        MockFirm('F2', 100, 240, 0.95, True),  # Similar to F0
        MockFirm('F3', 50, 300, 0.7, False),   # High leverage, low productivity
        MockFirm('F4', 50, 280, 0.75, False),  # Similar to F3
        MockFirm('F5', 200, 100, 1.3, True),   # Low leverage, high productivity
        MockFirm('F6', 180, 120, 1.25, True),  # Similar to F5
        MockFirm('F7', 180, 110, 1.28, True),  # Similar to F5
        MockFirm('F8', 90, 450, 0.8, False),   # Very high leverage
        MockFirm('F9', 95, 500, 0.75, False),  # Very high leverage
    ]

    # Define clustering
    clusterer = AgentClusterer(feature_buckets={
        'leverage': [0, 1, 2, 3, 4, 999],
        'productivity': [0, 0.8, 1.0, 1.2, 999],
        'sector': ['tradable', 'non_tradable']
    })

    # Define feature extractors
    extractors = {
        'leverage': lambda f: f.debt / f.A if f.A > 0 else 999,
        'productivity': lambda f: f.phi,
        'sector': lambda f: 'tradable' if f.tradable else 'non_tradable'
    }

    # Cluster firms
    clusters = clusterer.cluster_agents(firms, extractors)

    print 'Clustered %d firms into %d clusters:' % (len(firms), len(clusters))
    for cluster_key, cluster_firms in clusters.items():
        summary = clusterer.get_cluster_summary(cluster_firms, extractors)
        print ''
        print 'Cluster: %s' % cluster_key
        print '  Count: %d firms' % summary['count']
        for feature, stats in summary['features'].items():
            print '  %s: %.2f (range: %.2f - %.2f)' % (
                feature, stats['avg'], stats['min'], stats['max']
            )

    print ''
    print 'Without clustering: would need %d LLM calls' % len(firms)
    print 'With clustering: need only %d LLM calls' % len(clusters)
    print 'Reduction: %.1f%%' % (100.0 * (1 - len(clusters) / float(len(firms))))

    # Test policy evaluator
    print ''
    print 'Testing policy evaluator:'
    evaluator = PolicyEvaluator()

    policy = {
        'approval_formula': 'leverage < 3.0 and productivity > 0.9',
        'interest_rate_formula': '0.05 + 0.01 * leverage',
        'credit_limit_pct': 0.25,
        'confidence': 0.85
    }

    for firm in firms[:3]:
        context = {
            'leverage': firm.debt / firm.A if firm.A > 0 else 999,
            'productivity': firm.phi,
            'assets': firm.A,
            'base_rate': 0.05
        }
        decision = evaluator.apply_credit_policy(policy, context)
        print 'Firm %s: leverage=%.1f phi=%.2f -> approve=%s rate=%.3f' % (
            firm.ide, context['leverage'], context['productivity'],
            decision['approve'], decision['interest_rate']
        )
