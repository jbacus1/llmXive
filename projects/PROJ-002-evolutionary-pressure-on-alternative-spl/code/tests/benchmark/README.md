# Benchmark Test Suite

## Overview

This benchmark test suite measures the performance of the Evolutionary Pressure
Analysis Pipeline to ensure it meets the throughput requirements specified in
plan.md.

## Requirements

- Python 3.11+
- pytest
- pytest-benchmark (optional, for detailed benchmarking)

## Installation

```bash
cd code
pip install pytest pytest-benchmark
```

## Running Benchmarks

### Run All Benchmarks

```bash
pytest tests/benchmark/ -v
```

### Run Only Benchmarks (Skip Regular Tests)

```bash
pytest tests/benchmark/ --benchmark-only -v
```

### Run with Custom Iterations

```bash
pytest tests/benchmark/ --benchmark-iterations=5 -v
```

### Run Specific Benchmark

```bash
pytest tests/benchmark/ -k alignment_throughput -v
```

## Performance Thresholds

| Benchmark | Threshold | Description |
|-----------|-----------|-------------|
| Alignment Throughput | >10M reads/min | Per plan.md requirement |
| PSI Calculation | <5s per sample | Per spec requirements |
| Differential Splicing | <60s per comparison | Per spec requirements |
| Memory Usage | <4GB peak | System constraint |
| Full Pipeline | <5 minutes | End-to-end requirement |

## Benchmark Results

Results are saved to `tests/benchmark/benchmark_results.json` after each run.

```json
{
  "summary": {
    "total_benchmarks": 5,
    "passed": 5,
    "failed": 0,
    "timestamp": "2024-01-15 10:30:00"
  },
  "results": [...]
}
```

## CI Integration

Add to CI pipeline:

```yaml
- name: Run Performance Benchmarks
  run: |
    cd code
    pytest tests/benchmark/ --benchmark-only
```

## Notes

- Benchmarks use simulated data for consistent measurements
- Actual production benchmarks should use representative real data
- Results should be compared against baseline_metrics.json for regression detection
- Failed benchmarks will cause CI pipeline to fail
