# Benchmarks

Run a full local pipeline benchmark:

```bash
python3 -B benchmarks/pipeline_benchmark.py
```

Run an API load test while the FastAPI simulator is running:

```bash
uvicorn api_simulator.main:app --port 8000
python3 -B benchmarks/api_load_test.py --requests 50 --concurrency 8
```

Outputs are written to `benchmarks/results/`.
