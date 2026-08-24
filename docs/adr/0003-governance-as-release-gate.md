# ADR 0003: Governance as a BI Release Gate

## Status

Accepted

## Context

Executive dashboards can be technically correct but still unsafe to publish if source health, KPI ownership, privacy rules, or attribution reconciliation are unclear.

## Decision

Treat governance artifacts as part of the release process. Generate a data product scorecard, certified KPI governance mart, classification catalog, access policy matrix, retention policy matrix, and release packet.

## Consequences

- Dashboard trust is backed by release evidence.
- BI releases have evidence beyond screenshots.
- Privacy and access assumptions are visible even in a local-only implementation.
