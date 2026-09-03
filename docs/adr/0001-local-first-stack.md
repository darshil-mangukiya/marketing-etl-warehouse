# ADR 0001: Local-First Stack

## Status

Accepted

## Context

The project needs to demonstrate production-style data engineering and BI design while remaining runnable without paid cloud accounts.

## Decision

Use a local-first stack with Python, PostgreSQL, Airflow, dbt, Docker Compose, local S3-style folders, generated source data, and static evidence artifacts.

## Consequences

- Reviewers can run the project locally.
- The design stays portable by keeping source contracts, orchestration logic, warehouse SQL, and dbt models separated from local runtime assumptions.
- Some production services are represented by scaffolds rather than live managed cloud resources.
