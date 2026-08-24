# Data Quality Addendum

The existing framework covers contracts, duplicates, dates, negative/null spend, impossible click/conversion relationships, attribution gaps, rejected rows, source health and release gates. GA4 adds accepted-event, 0/1 indicator, non-negative revenue and purchase-only revenue rules. Connector/cloud tests cover missing configuration, malformed/empty responses, retries, rate limits, metadata and redacted authentication failures.

Critical errors create rejected records and can quarantine a batch. Warnings remain visible for investigation. The source generator intentionally creates invalid rows to exercise rejection handling; the configured threshold determines whether the batch proceeds.
