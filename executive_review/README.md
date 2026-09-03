# Marketing Monthly Business Review

The 10-slide PowerPoint converts the six modeled ad-hoc requests into a management review focused on what happened, why it matters, what should be reviewed next, and what evidence can block release.

- [PowerPoint](Marketing_Monthly_Business_Review.pptx)
- [Two-minute executive brief](EXECUTIVE_ANALYTICS_BRIEF.md)
- [Validation report](validation_report.json)
- Reproducible source: `build_deck.mjs`
- Governed metric snapshot: `data/deck_metrics.json`

All business performance data is generated/synthetic. The bounded real portfolio-site GA4 path remains separate and is not used in this review. The deck does not claim causal lift, realized impact, actual stakeholder approval, live ad execution, Power BI Service deployment, or production operation.

## Rebuild

The deck source uses the bundled `@oai/artifact-tool` presentation runtime. From an environment where that package is available:

```bash
node executive_review/build_deck.mjs
```

The analysis pack must be regenerated first so `data/deck_metrics.json` and the request result files remain synchronized.

## Validate

```bash
python3 -B analytics_requests/build_analysis_pack.py
python3 -B executive_review/validate_deck.py
```

All 10 slides were rendered and inspected through the artifact renderer, and generated layout bounds passed. An Office-compatible renderer was unavailable in the current sandbox, so opening the final file in desktop PowerPoint remains the isolated manual visual check.
