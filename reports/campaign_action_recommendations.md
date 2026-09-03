# Campaign Action Recommendations

## Business Purpose

This output translates campaign ROI, spend, conversion, target, attribution, and data-quality signals into deterministic campaign recommendations. It is designed for analyst review and stakeholder discussion, not automated budget execution.

## Fields

Key fields include campaign ID/name, channel, platform, spend, attributed revenue, ROAS, campaign ROI %, CAC, conversion rate, lead-to-customer rate, budget pacing %, target attainment %, attribution coverage %, data-quality flag, recommended action, action priority, and action reason.

## Scoring Logic

- **Scale**: strong ROAS, healthy conversion rate, and budget pacing not excessive.
- **Pause**: high spend, weak ROAS, and weak conversion rate.
- **Reallocate Budget**: target attainment is low while performance is efficient.
- **Improve Funnel Quality**: traffic exists but conversion quality is weak.
- **Investigate Attribution Gap**: conversions exist but attribution coverage is weak.
- **Fix Data Quality Issue**: validation or source-health flags are present.
- **Monitor**: mixed performance or no urgent signal.

## Current Recommendation Mix

{'Reallocate Budget': 150, 'Improve Funnel Quality': 65, 'Pause': 29, 'Monitor': 6}

## Review Scope

The logic uses generated local marts and deterministic thresholds. Analyst review remains part of the operating pattern before budget changes.
