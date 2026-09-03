# Ops Utilities

Operational helpers:

- `alerting.py`: JSONL alert emitter used by Airflow callbacks.
- `scorecard.py`: combines quality, GE, contracts, catalog, benchmark, and local quality gate outputs into an operational scorecard.

Run:

```bash
python3 -B ops/scorecard.py
```
