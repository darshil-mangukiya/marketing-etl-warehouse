# FastAPI Source Simulator

This service turns generated paid-media partitions into real paginated REST endpoints.

## Run

Install the pinned project dependencies first. The simulator uses FastAPI `0.133.x` and Starlette `1.3.x`.

```bash
python3 -m pip install -r requirements.txt
uvicorn api_simulator.main:app --reload --port 8000
```

Use the bearer token from `MOCK_API_TOKEN`, or the default local token:

```bash
curl -H "Authorization: Bearer local-dev-token" \
  "http://localhost:8000/v1/google_ads/records?page_size=1000"
```

## Features

- Token authentication.
- Cursor-style pagination through `page_token`.
- `updated_after` watermark filtering.
- Optional `failure_rate` query parameter for retry testing.
- Rate-limit and request-id response headers.
- Shared generated source manifest, so API and file ingestion use the same data contracts.

## Tests

```bash
python3 -m pytest tests/test_api_simulator.py -q
```
