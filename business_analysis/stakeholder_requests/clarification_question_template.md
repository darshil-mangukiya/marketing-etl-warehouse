# Clarification Questions for a Modeled Business Request

Use only the questions needed to turn an ambiguous request into a testable analytical definition.

## Decision

1. What decision will this analysis inform?
2. Is the expected output a diagnosis, prioritization, what-if scenario, or approval recommendation?
3. Who has authority to act, and what remains human-reviewed?

## Metric and scope

4. Which governed metric definition should be used?
5. What period, region, channel, campaign, product, or cohort is in scope?
6. What comparison is defensible: prior period, target, benchmark, or sensitivity range?
7. What grain must be preserved to avoid double counting?

## Trust and interpretation

8. Which quality, freshness, mapping, rejection, and reconciliation checks must pass?
9. What evidence would require a DATA QUALITY HOLD?
10. Which statements are observations, which are interpretations, and which are recommendations?
11. What alternative explanation could make the conclusion wrong?

## Delivery

12. What must be in the concise stakeholder response?
13. What supporting table, chart, SQL/Python, and provenance are required?
