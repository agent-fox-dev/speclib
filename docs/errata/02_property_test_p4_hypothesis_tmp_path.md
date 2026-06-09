# Erratum: TS-02-P4 Property Test Hypothesis Fixture Reuse

**Spec:** 02_campaign_session
**Test:** `test_ts02_p4_property_create_atomic`
**Status:** Known issue

## Issue

The property test `test_ts02_p4_property_create_atomic` uses a fixed
subdirectory name (`tmp_path / "test_campaign"`) across all Hypothesis
examples. Because the test uses `suppress_health_check=
[HealthCheck.function_scoped_fixture]`, `tmp_path` is the same directory
for all examples within a single test invocation.

On the second Hypothesis example, `Campaign.create` correctly detects the
existing `campaign.yaml` from the first example and raises `CampaignError`
(per 02-REQ-1.2), failing the test.

## Root Cause

The test spec pseudocode (TS-02-P4) assumes each iteration receives a
fresh temporary directory, but the Hypothesis + pytest `tmp_path` fixture
interaction reuses the same directory. Compare with TS-02-P3, which
correctly uses unique subdirectory names (`f"camp_{n}"`).

## Fix

The test should use unique subdirectory names per example. For example:

```python
path = tmp_path / f"test_campaign_{abs(hash((name, desc)))}"
```

## Impact

The implementation is correct per 02-REQ-1.2. This is a test fixture
interaction issue, not an implementation defect.
