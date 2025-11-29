># Fraud Score Aggregation Formula

This document specifies the fraud score aggregation formula used in the RealEstatesAntiFraud system.

## Overview

The fraud detection system uses a **weighted aggregation formula** to combine signals from multiple detection plugins into a single fraud score.

## Formula Specification

### Weighted Score Calculation

```
fraud_score = (Σ(plugin_score_i × weight_i)) / (Σ weight_i) × 100

where:
- plugin_score_i = detection score from plugin i (0.0 to 1.0)
- weight_i = importance weight of plugin i (0.0 to 1.0)
- Final fraud_score is scaled to 0-100 range
```

### Implementation Details

1. **Weight Normalization**: Weights are automatically normalized to sum to 1.0
   - Prevents issues when weights don't sum to exactly 1.0
   - Allows flexible weight configuration

2. **Confidence Filtering**: Only signals above confidence threshold are included
   - Default threshold: 0.5
   - Configurable per orchestrator instance
   - Low-confidence signals are excluded from scoring

3. **Concurrent Execution**: All plugins run concurrently
   - Uses `asyncio.gather()` for parallel execution
   - Significantly faster than sequential execution
   - Failed plugins don't block others

## Risk Level Classification

The fraud score is mapped to three risk levels as specified in ARCHITECTURE.md:

| Risk Level   | Score Range | Action Recommendation           |
|--------------|-------------|---------------------------------|
| **safe**     | 0 - 29      | No action needed                |
| **suspicious** | 30 - 69   | Manual review recommended       |
| **fraud**    | 70 - 100    | Block listing, investigate user |

### Classification Formula

```python
def determine_risk_level(score: float) -> str:
    if score < 30.0:
        return "safe"
    elif score < 70.0:
        return "suspicious"
    else:  # score >= 70.0
        return "fraud"
```

## Edge Cases

### No Plugins Registered
- **Behavior**: Returns score of 0.0, risk level "safe"
- **Rationale**: No evidence of fraud without detection plugins

### All Plugins Disabled
- **Behavior**: Same as no plugins - score 0.0, risk "safe"
- **Rationale**: System shouldn't assume fraud without active detection

### All Signals Below Confidence Threshold
- **Behavior**: Score based on plugin overall scores, signals filtered from output
- **Rationale**: Low-confidence signals shouldn't influence display, but plugin-level scores are still aggregated

### Plugin Errors
- **Behavior**: Failed plugins are skipped, scoring continues with remaining plugins
- **Rationale**: One plugin failure shouldn't crash entire analysis
- **Logging**: Errors are logged with full traceback for debugging

## Performance Characteristics

Based on benchmarks in `test_risk_scoring_benchmarks.py`:

- **Single Plugin (fast)**: ~1.2ms mean latency
- **5 Plugins (concurrent)**: ~11ms mean latency (not 50ms sequential!)
- **20 Plugins (concurrent)**: ~23ms mean latency
- **No Plugins (edge case)**: <0.01ms mean latency

### Concurrency Benefits

With 5 plugins at 10ms each:
- **Sequential**: 50ms total
- **Concurrent**: ~11ms total
- **Speedup**: ~4.5x

## Example Scenarios

### Scenario 1: High Fraud Score

```python
Plugin A (price detector):   score=0.9, weight=0.6
Plugin B (location detector): score=0.8, weight=0.4

fraud_score = (0.9 × 0.6 + 0.8 × 0.4) / (0.6 + 0.4) × 100
            = (0.54 + 0.32) / 1.0 × 100
            = 86.0

risk_level = "fraud"  # >= 70
```

### Scenario 2: Mixed Signals

```python
Plugin A (price detector):    score=0.9, weight=0.6
Plugin B (location detector):  score=0.2, weight=0.4

fraud_score = (0.9 × 0.6 + 0.2 × 0.4) / (0.6 + 0.4) × 100
            = (0.54 + 0.08) / 1.0 × 100
            = 62.0

risk_level = "suspicious"  # 30-69 range
```

### Scenario 3: Low Risk

```python
Plugin A (price detector):   score=0.1, weight=0.5
Plugin B (photo detector):   score=0.2, weight=0.5

fraud_score = (0.1 × 0.5 + 0.2 × 0.5) / (0.5 + 0.5) × 100
            = (0.05 + 0.10) / 1.0 × 100
            = 15.0

risk_level = "safe"  # < 30
```

## Confidence Weighting

Each risk signal has a confidence value (0.0-1.0) indicating the plugin's certainty:

```python
signal = RiskSignal(
    signal_type="price_anomaly",
    score=0.9,              # High fraud indicator
    confidence=0.95,        # Very confident
    reason="Price 80% below market average"
)
```

Overall confidence is computed as weighted average of signal confidences:

```
overall_confidence = Σ(signal.confidence × plugin_weight) / Σ(plugin_weight)
```

## Future Enhancements

### Adaptive Weighting
- Adjust plugin weights based on historical accuracy
- Increase weight of plugins with high precision
- Decrease weight of plugins with false positives

### Ensemble Methods
- Support for voting-based aggregation (majority vote)
- Cascading detection (high-priority plugins first)
- Confidence-weighted voting

### Machine Learning Integration
- Train meta-model on plugin outputs
- Learn optimal weights from labeled data
- Detect and adapt to fraud pattern shifts

## References

- Main implementation: `core/fraud/risk_scoring_orchestrator.py`
- Architecture spec: `ARCHITECTURE.md` (lines 445-462)
- Unit tests: `tests/unit/test_risk_scoring_orchestrator.py`
- Benchmarks: `tests/unit/test_risk_scoring_benchmarks.py`
