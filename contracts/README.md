# Source Data Contracts

`source_contracts.yml` declares source ownership, ingestion method, primary keys, watermarks, freshness expectations, rejected-row thresholds, required columns, and key business rules.

Run contract checks against raw lake files:

```bash
python3 -B ingestion/data_contracts.py
```

Outputs:

- `data/quality_reports/contracts/contract_check_results.json`
- `data/quality_reports/contracts/contract_check_results.csv`
