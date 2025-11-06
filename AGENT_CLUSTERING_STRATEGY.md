# Agent Clustering Strategy: Reducing API Calls by 95%+

## The Core Idea

Instead of querying the LLM for **each individual agent**, cluster similar agents and make **one API call per cluster**, then apply the decision to all members.

## Potential Impact

```
Current:  200,000 API calls per 50-cycle simulation
Clustered: 2,000-5,000 API calls per 50-cycle simulation
Reduction: 95-98%
```

## Implementation Strategy by Decision Type

### 1. Bank Credit Decisions (83% of calls → Target for biggest savings)

#### Current Approach
```python
# 3,318 calls per cycle
for each firm_loan_request:
    for each bank:
        decision = bank.credit_decision(firm, leverage, loan_request)
        # Individual LLM call for this specific firm-bank pair
```

#### Clustered Approach
```python
# Cluster firms by credit profile
clusters = cluster_by_features(loan_requests, features=[
    'leverage_bucket',      # Round to 0.5: [0-0.5, 0.5-1.0, 1.0-1.5, ...]
    'firm_size_bucket',     # Small/Medium/Large based on assets
    'productivity_bucket',  # Low/Medium/High based on phi
    'sector'               # Tradable vs Non-tradable
])

# One API call per cluster
for cluster_id, firms_in_cluster in clusters.items():
    # Describe cluster characteristics
    cluster_profile = {
        "num_firms": len(firms_in_cluster),
        "avg_leverage": mean([f.leverage for f in firms_in_cluster]),
        "leverage_range": [min(...), max(...)],
        "avg_productivity": mean([f.phi for f in firms_in_cluster]),
        "sector": cluster_id.sector,
        "representative_firm": firms_in_cluster[0]  # Or median firm
    }

    # Single LLM call for entire cluster
    cluster_decision = llm.decide_bank_credit_policy(cluster_profile)
    # Returns: approval_threshold, interest_rate_formula, credit_limit_formula

    # Apply to all firms in cluster
    for firm in firms_in_cluster:
        individual_decision = apply_policy(cluster_decision, firm.specific_values)
```

**Impact**: 3,318 calls → ~50-100 calls per cycle (97% reduction)

**Clustering dimensions**:
- **Leverage buckets**: [0-1], [1-2], [2-3], [3-4], [4+] → 5 buckets
- **Firm size**: Small/Medium/Large → 3 buckets
- **Sector**: Tradable/Non-tradable → 2 buckets
- **Total clusters**: 5 × 3 × 2 = **30 clusters** (vs 3,318 individual calls)

### 2. Firm Pricing Decisions (8% of calls)

#### Clustered Approach
```python
# Cluster firms by market conditions
clusters = cluster_by_features(firms, features=[
    'inventory_level_bucket',    # High/Normal/Low relative to target
    'demand_trend_bucket',        # Rising/Stable/Falling
    'competition_bucket',         # High/Medium/Low
    'cost_pressure_bucket'        # Rising/Stable/Falling
])

# One API call per cluster (~20-40 clusters)
for cluster_id, firms_in_cluster in clusters.items():
    cluster_context = {
        "market_condition": describe_cluster(firms_in_cluster),
        "representative_firm": get_median_firm(firms_in_cluster)
    }

    # Single LLM call
    pricing_strategy = llm.decide_firm_pricing_strategy(cluster_context)
    # Returns: direction_rule, price_step_formula, confidence

    # Apply to each firm with their specific values
    for firm in firms_in_cluster:
        decision = apply_pricing_strategy(pricing_strategy, firm)
```

**Impact**: 320 calls → ~30-40 calls per cycle (88% reduction)

### 3. Wage Decisions (9% of calls)

#### Clustered Approach
```python
# Cluster by labor market segment
worker_clusters = cluster_by_features(workers, features=[
    'employment_history_bucket',   # Stable/Unstable/Unemployed
    'wage_level_bucket',          # Below/At/Above market
    'country'                     # Country 0 or 1
])

firm_wage_clusters = cluster_by_features(firms_with_vacancies, features=[
    'vacancy_pressure_bucket',    # High/Medium/Low vacancies
    'fill_rate_bucket',          # Easy/Normal/Hard to fill
    'country'
])

# One API call per cluster
for cluster in all_wage_clusters:
    wage_policy = llm.decide_wage_policy(cluster.context)
    for agent in cluster.agents:
        apply_wage_policy(wage_policy, agent)
```

**Impact**: 361 calls → ~20-30 calls per cycle (92% reduction)

## Prompt Design for Clustered Decisions

### Example: Bank Credit Cluster Prompt

```
You are a Credit Risk Officer evaluating a cluster of loan applications.

CLUSTER PROFILE:
- Number of firms: 127
- Sector: Non-tradable goods
- Leverage range: 2.0 - 2.8 (avg: 2.4)
- Productivity range: 0.85 - 1.15 (avg: 1.02)
- Loan amounts: $5K - $50K (avg: $18K)

REPRESENTATIVE FIRM (median of cluster):
- Current assets: $45K
- Current debt: $108K (leverage = 2.4)
- Productivity (phi): 1.05
- Recent profitability: Break-even
- Credit history: 2 existing creditors, no defaults

MARKET CONTEXT:
- Unemployment rate: 5.2%
- Average sector productivity: 1.00
- Credit market tightness: Moderate

Please provide a CREDIT POLICY for this cluster:

1. Approval criteria (as boolean formula or threshold)
2. Interest rate formula (as function of leverage, productivity, etc.)
3. Credit limit formula (maximum loan as % of firm assets)
4. Risk assessment confidence (0-1)

The policy will be applied to all 127 firms in this cluster, with their
specific values substituted into your formulas.

Respond as JSON:
{
  "approve_if": "leverage < 3.0 AND productivity > 0.9",
  "interest_rate_formula": "base_rate + 0.5 * (leverage - 2.0) + 0.3 * (1.0 - productivity)",
  "credit_limit_pct": 0.25,
  "confidence": 0.82,
  "risk_analysis": "2-3 sentence explanation"
}
```

## Implementation Plan

### Phase 1: Add Clustering Infrastructure (1-2 hours)

Create `code/llm_clustering.py`:

```python
class AgentClusterer:
    def __init__(self, feature_buckets):
        """
        feature_buckets = {
            'leverage': [0, 1, 2, 3, 4, float('inf')],
            'size': ['small', 'medium', 'large']
        }
        """
        self.feature_buckets = feature_buckets

    def cluster_agents(self, agents, feature_extractors):
        """
        agents: list of agent objects
        feature_extractors: dict of {feature_name: lambda agent: value}

        Returns: dict of {cluster_id: [agents]}
        """
        clusters = defaultdict(list)

        for agent in agents:
            cluster_key = self._get_cluster_key(agent, feature_extractors)
            clusters[cluster_key].append(agent)

        return clusters

    def _get_cluster_key(self, agent, extractors):
        """Create cluster ID from bucketed features."""
        key_parts = []
        for feature_name, extractor in extractors.items():
            value = extractor(agent)
            bucket = self._bucketize(value, feature_name)
            key_parts.append(f"{feature_name}={bucket}")
        return "|".join(sorted(key_parts))

    def get_cluster_summary(self, cluster_agents, extractors):
        """Generate summary statistics for LLM prompt."""
        return {
            "count": len(cluster_agents),
            "features": {
                name: {
                    "min": min(extractor(a) for a in cluster_agents),
                    "max": max(extractor(a) for a in cluster_agents),
                    "avg": mean(extractor(a) for a in cluster_agents),
                }
                for name, extractor in extractors.items()
            },
            "representative": self._get_representative(cluster_agents, extractors)
        }
```

### Phase 2: Modify Bank Credit Decision (tools/decider/server.py)

Add new endpoint `/decide/bank_cluster`:

```python
@app.route('/decide/bank_cluster', methods=['POST'])
def decide_bank_credit_cluster():
    """
    Accepts cluster of similar loan requests.
    Returns policy that can be applied to all.
    """
    payload = request.get_json()

    # New prompt template for clusters
    prompt = BANK_CLUSTER_PROMPT.build_user(payload)

    # LLM returns policy formulas, not individual decisions
    response = openrouter_adapter.chat_completion(...)

    policy = {
        "approval_formula": response["approve_if"],
        "interest_rate_formula": response["interest_rate_formula"],
        "credit_limit_pct": response["credit_limit_pct"],
        "confidence": response["confidence"]
    }

    return jsonify(policy)
```

### Phase 3: Update Matching Credit (code/matchingCredit.py)

```python
def matchCreditOpen(self, McountryFirm, McountryBank, McountryCentralBank):
    """Modified to use clustering."""

    # Extract all loan requests
    loan_requests = self._collect_loan_requests(McountryFirm)

    # Cluster by credit profile
    clusterer = AgentClusterer(feature_buckets={
        'leverage': [0, 1, 2, 3, 4, 999],
        'productivity': [0, 0.8, 1.0, 1.2, 999],
        'sector': ['tradable', 'non_tradable']
    })

    clusters = clusterer.cluster_agents(
        loan_requests,
        feature_extractors={
            'leverage': lambda req: req['leverage'],
            'productivity': lambda req: req['firm'].phi,
            'sector': lambda req: req['firm'].tradable
        }
    )

    # Process each cluster
    for cluster_id, requests in clusters.items():
        # Build cluster payload
        cluster_payload = clusterer.get_cluster_summary(requests, ...)

        # Single LLM call for entire cluster
        policy, error = client.decide_bank_cluster(cluster_payload)

        if error:
            # Fall back to deterministic for this cluster
            for req in requests:
                self._apply_deterministic_credit(req)
        else:
            # Apply policy to each request
            for req in requests:
                decision = self._apply_credit_policy(policy, req)
                self._process_loan(req, decision)
```

### Phase 4: Add Policy Application Logic

```python
def _apply_credit_policy(self, policy, loan_request):
    """
    Evaluates policy formulas with specific firm values.

    policy = {
        "approval_formula": "leverage < 3.0 AND productivity > 0.9",
        "interest_rate_formula": "0.05 + 0.5 * (leverage - 2.0)",
        "credit_limit_pct": 0.25
    }
    """
    firm = loan_request['firm']
    leverage = loan_request['leverage']

    # Safe evaluation of approval formula
    approved = self._eval_boolean_formula(
        policy['approval_formula'],
        context={
            'leverage': leverage,
            'productivity': firm.phi,
            'assets': firm.A
        }
    )

    # Calculate interest rate from formula
    interest_rate = self._eval_numeric_formula(
        policy['interest_rate_formula'],
        context={
            'leverage': leverage,
            'productivity': firm.phi,
            'base_rate': 0.05
        }
    )

    # Calculate credit limit
    credit_limit = firm.A * policy['credit_limit_pct']

    return {
        'approve': approved,
        'interest_rate': interest_rate,
        'credit_limit': credit_limit,
        'probability': policy.get('confidence', 0.8)
    }

def _eval_boolean_formula(self, formula_str, context):
    """
    Safely evaluate boolean expressions like:
    "leverage < 3.0 AND productivity > 0.9"
    """
    # Parse and evaluate with safe operators only
    # Could use pyparsing or simple AST evaluation
    # For security, whitelist operators: <, >, <=, >=, ==, AND, OR, NOT
    pass

def _eval_numeric_formula(self, formula_str, context):
    """
    Safely evaluate numeric expressions like:
    "0.05 + 0.5 * (leverage - 2.0)"
    """
    # Similar safe evaluation with whitelisted operators: +, -, *, /, ()
    pass
```

## Testing Strategy

### Unit Test: Verify Clustering

```python
def test_bank_credit_clustering():
    # Create 100 synthetic firms with known characteristics
    firms = [
        create_firm(leverage=2.3, phi=1.0, sector='tradable'),
        create_firm(leverage=2.4, phi=1.1, sector='tradable'),
        # ... should cluster together
        create_firm(leverage=4.5, phi=0.8, sector='non_tradable'),
        # ... should be in different cluster
    ]

    clusterer = AgentClusterer(...)
    clusters = clusterer.cluster_agents(firms, ...)

    # Verify similar firms are clustered
    assert len(clusters) == expected_num_clusters
    assert all(cluster_is_homogeneous(c) for c in clusters.values())
```

### Integration Test: Compare Outcomes

```python
def test_clustered_vs_individual_decisions():
    """
    Run 2-cycle simulation twice:
    1. Individual LLM calls
    2. Clustered LLM calls

    Compare: final GDP, unemployment, firm survival
    Should be similar (within 5% difference)
    """
    para1 = Parameter()
    para1.use_llm_clustering = False  # Individual
    result1 = run_simulation(para1)

    para2 = Parameter()
    para2.use_llm_clustering = True   # Clustered
    result2 = run_simulation(para2)

    assert abs(result1.GDP - result2.GDP) / result1.GDP < 0.05
```

## Economic Validity Considerations

### Advantages
1. **Faster execution**: 95% fewer API calls
2. **More consistent**: Similar firms get similar treatment
3. **Policy-oriented**: LLM provides general policies (more realistic than case-by-case)
4. **Robust**: Less sensitive to prompt variations

### Disadvantages
1. **Loss of granularity**: Can't capture truly unique firm situations
2. **Clustering artifacts**: Firms near bucket boundaries may behave strangely
3. **Formula evaluation**: Requires safe expression parsing

### Mitigation Strategies
1. **Hybrid approach**: Use clustering for 90% of routine decisions, individual LLM for outliers
2. **Adaptive buckets**: Adjust bucket sizes based on cluster heterogeneity
3. **Validation**: Compare clustered vs individual approaches on small simulations

## Estimated Development Time

| Task | Time | Priority |
|------|------|----------|
| AgentClusterer class | 2 hours | High |
| Bank cluster endpoint | 2 hours | High |
| Cluster prompt templates | 1 hour | High |
| Policy application logic | 3 hours | High |
| Safe formula evaluation | 2 hours | Medium |
| matchingCredit integration | 2 hours | High |
| Testing & validation | 3 hours | High |
| Firm/wage clustering | 2 hours | Medium |
| **TOTAL** | **17 hours** | |

## Expected Outcome

**Before clustering**:
- 50 cycles = 200,000 API calls
- OpenRouter rate limit = 56 hours runtime
- Frequent timeouts and failures

**After clustering**:
- 50 cycles = ~3,000-5,000 API calls (95-98% reduction)
- OpenRouter rate limit = ~1-2 hours runtime
- Reliable execution
- Similar economic outcomes (validated)

This makes large-scale LLM-enhanced simulations **practical and affordable**!
