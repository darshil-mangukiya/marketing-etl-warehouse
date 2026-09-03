# P2 Interview Guide

## What problem were you solving?

Marketing data arrived across generated paid-media, web, CRM, conversion, and target domains with inconsistent identifiers and metric definitions. The project creates a governed path to ROI, funnel, attribution, target, scenario, and quality decisions—and demonstrates how an analyst communicates those results.

## Why did you use dbt?

dbt makes transformations, dependencies, grains, tests, documentation, and adapter-specific behavior explicit. It separates reusable facts and dimensions from reporting marts and lets the same governed logic support local DuckDB, PostgreSQL, and bounded BigQuery paths.

## Why DuckDB + PostgreSQL + BigQuery?

DuckDB provides a fast, reproducible local validation path. PostgreSQL exercises relational warehouse and operational controls. BigQuery supports the bounded cloud and real portfolio-site GA4 path. They are purposeful execution profiles, not duplicate technologies added for keyword coverage.

## How did you validate data?

Validation spans source contracts, accepted/rejected separation, freshness and watermarks, dbt tests, attribution reconciliation, source-to-BI controls, semantic regression, and artifact checks. Recommendations can be held when trust controls fail.

## How does attribution work?

The project compares first touch, last touch, linear, U-shaped, position-based, and time-decay allocation. A sensitivity analysis tests both rank and attributed-revenue range. These models allocate observed revenue; they do not estimate causal incrementality.

## How did you prevent bad recommendations?

Action logic exposes thresholds, reasons, supporting metrics, and metrics to monitor. A DATA QUALITY HOLD can override performance actions. The P2 2.0 trust investigation also found that source-level failures do not automatically cascade through the campaign-ID hold rule, so the modeled recommendation is a manual release hold pending reconciliation.

## How did you handle ambiguous stakeholder requests?

Each modeled request captures the original question, decision need, clarifying questions, metric definition, comparison, grain, data-quality threshold, analytical restatement, and required output. The lifecycle is request → clarification → definition → validation → analysis → finding → recommendation → follow-up.

## Give an example of an ad-hoc analysis.

For the modeled VP Marketing request, I quantified paid-social attributed ROAS and ranked campaign contributions to the break-even shortfall. Paid social showed 0.03x attributed ROAS, but the two largest campaign shortfalls represented only 24.0% of the total. The defensible recommendation was a portfolio-wide measurement and campaign review—not a one-campaign fix or an automatic budget cut.

## What would you productionize differently?

I would enforce stronger channel and campaign conformance before marts, propagate source-level quality states into every downstream action, implement cohort-aware funnel timing, add deployment-specific observability and access controls, and connect real vendor accounts only through approved credentials and change controls.

## What is real vs synthetic?

Marketing business inputs and performance outputs are generated/synthetic. The bounded portfolio-site GA4 telemetry exported daily to BigQuery is real project-site data and remains separate. No real customer, ad-performance, stakeholder-adoption, realized-impact, or production-operation claim is made.

## What would you improve next?

The highest-value next step is not another technology. It is tighter conformance and release governance: resolve cross-channel joins, make source quality cascade into action holds, add cohort-aware funnel views, and test recommendations on a controlled, approved real-data path if one becomes available.
