# Marketing API Connectors

The `connectors` package defines one extraction workflow for Google Ads, Meta Ads and TikTok Ads. It supports date windows, page tokens, normalized campaign metrics, exponential retry, HTTP 429/5xx handling, `Retry-After`, response/request metadata, last watermark, raw JSONL landing and redacted errors.

Vendor classes translate representative payloads into `account_id`, campaign/ad-group identifiers, event date, impressions, clicks, spend, conversions and conversion value. Unit tests use local HTTP transports. Vendor execution requires account authorization and API-version checks before use.

Errors are classified as configuration, malformed payload, exhausted retry or redacted request failures. Access/developer tokens are never included in result metadata or exception messages.
