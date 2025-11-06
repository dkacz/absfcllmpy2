# Integration Tests for OpenRouter Live LLM

## Overview

The integration tests in `test_openrouter_integration.py` make **real API calls** to OpenRouter to validate end-to-end functionality of the LLM decision-making system.

## Prerequisites

Set the OpenRouter API key as an environment variable:

```bash
export OPENROUTER_API_KEY="sk-or-v1-..."
```

## Running the Tests

### Run all integration tests

```bash
python -m unittest tests.test_openrouter_integration -v
```

### Run individual tests

```bash
# Test API connectivity and credit info
python -m unittest tests.test_openrouter_integration.OpenRouterIntegrationTests.test_01_key_info -v

# Test firm pricing decisions
python -m unittest tests.test_openrouter_integration.OpenRouterIntegrationTests.test_02_firm_pricing_decision -v

# Test bank credit decisions
python -m unittest tests.test_openrouter_integration.OpenRouterIntegrationTests.test_03_bank_credit_decision -v

# Test wage adjustment decisions
python -m unittest tests.test_openrouter_integration.OpenRouterIntegrationTests.test_04_wage_decision -v
```

## Test Coverage

The integration tests validate:

1. **API Connectivity** (`test_01_key_info`)
   - Fetches API key information
   - Checks credit balance and usage limits
   - Verifies basic HTTP connectivity

2. **Firm Pricing Decisions** (`test_02_firm_pricing_decision`)
   - Makes real LLM calls for pricing decisions
   - Validates JSON response structure
   - Checks decision fields: direction, price_step, expectation_bias, confidence
   - Verifies guard constraints are respected

3. **Bank Credit Decisions** (`test_03_bank_credit_decision`)
   - Makes real LLM calls for credit approval decisions
   - Validates approval logic and credit terms
   - Checks fields: approve, credit_limit_ratio, spread_bps
   - Verifies numerical constraints (ratios 0-1, valid spreads)

4. **Wage Adjustment Decisions** (`test_04_wage_decision`)
   - Makes real LLM calls for wage decisions
   - Validates wage adjustment logic
   - Checks fields: direction, wage_step, confidence
   - Verifies wage constraints are respected

## Model Configuration

**Current model:** `google/gemini-2.5-flash-lite`
- Fast and cost-effective
- Reliable connectivity through OpenRouter
- Uses JSON object mode (not structured outputs)

To use a different model, edit `TEST_MODEL` in `test_openrouter_integration.py`:

```python
TEST_MODEL = "your-model-slug"
```

## API Usage

The full test suite makes **4 API calls total**:
- 1 call to `/key` endpoint (no tokens)
- 3 calls to `/chat/completions` endpoint (~900-1000 tokens total)

**Estimated cost:** < $0.01 USD per full test run

## Expected Test Output

```
Note: google/gemini-2.5-flash-lite doesn't support structured outputs, will use json_object mode

  Credit balance: $None
  Usage: N/A/N/A

  Decision: hold, step: 0.000, confidence: 0.90
  Tokens: 211 prompt, 86 completion
  Elapsed: 554.1ms

  Approve: True, limit: 0.20, spread: 100bps
  Tokens: 266 prompt, 119 completion

  Direction: raise, step: 0.040
  Tokens: 169 prompt, 101 completion

test_01_key_info ... ok
test_02_firm_pricing_decision ... ok
test_03_bank_credit_decision ... ok
test_04_wage_decision ... ok

----------------------------------------------------------------------
Ran 4 tests in 2.422s

OK
```

## Troubleshooting

### Tests are skipped

If you see "skipped 'OPENROUTER_API_KEY not set'", ensure the environment variable is set:

```bash
export OPENROUTER_API_KEY="your-key-here"
```

### Rate limiting (HTTP 429)

If tests fail with 429 errors, wait 10-30 seconds between test runs. The tests include built-in delays to avoid rate limits.

### Model unavailable (HTTP 404/503)

If a specific model is unavailable:
1. Check the model slug at https://openrouter.ai/models
2. Update `TEST_MODEL` in the test file
3. Ensure the model supports JSON output mode

### SSL/TLS errors

OpenRouter occasionally has connectivity issues with certain model backends. If you see SSL certificate errors:
1. Wait a few minutes and retry
2. Try a different model (see alternative models in test file)
3. Check OpenRouter status at their platform

## Comparison with Unit Tests

| Feature | Unit Tests (`test_decider_server_live.py`) | Integration Tests (`test_openrouter_integration.py`) |
|---------|------------------------------------------|--------------------------------------------------|
| API Calls | No (mocked with `DummyAdapter`) | Yes (real OpenRouter API) |
| Speed | Very fast (~0.1s) | Moderate (~2-3s) |
| Cost | Free | Small (~$0.01) |
| Coverage | Adapter logic, error handling, retries | End-to-end LLM responses |
| CI/CD | Run on every commit | Run periodically or on-demand |

Both test suites are complementary and serve different purposes.
