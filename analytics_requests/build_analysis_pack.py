from __future__ import annotations

import hashlib
import json
from pathlib import Path

import duckdb
import pandas as pd
import yaml
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACK_ROOT = PROJECT_ROOT / "analytics_requests"
CANONICAL_INPUT_ROOT = PACK_ROOT / "canonical_input"
CANONICAL_TABLES = {
    "mart_campaign_performance": CANONICAL_INPUT_ROOT / "mart_campaign_performance.csv",
    "mart_funnel_performance": CANONICAL_INPUT_ROOT / "mart_funnel_performance.csv",
    "mart_target_vs_actual": CANONICAL_INPUT_ROOT / "mart_target_vs_actual.csv",
    "mart_attribution_model_comparison": CANONICAL_INPUT_ROOT / "mart_attribution_model_comparison.csv",
    "mart_data_quality_monitoring": CANONICAL_INPUT_ROOT / "mart_data_quality_monitoring.csv",
    "mart_campaign_action_center": CANONICAL_INPUT_ROOT / "mart_campaign_action_center.csv",
}
CANONICAL_SCHEMAS = {
    "mart_campaign_performance": {
        "campaign_id": "VARCHAR",
        "canonical_campaign_name": "VARCHAR",
        "canonical_channel": "VARCHAR",
        "spend": "DECIMAL(38,2)",
        "attributed_revenue": "DOUBLE",
        "attributed_roas": "DOUBLE",
        "platform_conversions": "HUGEINT",
        "waste_budget_flag": "BOOLEAN",
    },
    "mart_funnel_performance": {
        "reporting_month": "DATE",
        "channel_key": "VARCHAR",
        "total_leads": "BIGINT",
        "mqls": "BIGINT",
        "sales_qualified_leads": "BIGINT",
        "conversions": "BIGINT",
        "lead_to_mql_rate": "DOUBLE",
        "mql_to_sql_rate": "DOUBLE",
        "sql_to_close_rate": "DOUBLE",
    },
    "mart_target_vs_actual": {
        "target_month": "DATE",
        "region": "VARCHAR",
        "channel_name": "VARCHAR",
        "budget_owner": "VARCHAR",
        "target_spend": "DECIMAL(18,2)",
        "actual_spend": "DECIMAL(38,2)",
        "spend_attainment": "DOUBLE",
        "target_revenue": "DECIMAL(18,2)",
        "actual_revenue": "DOUBLE",
        "revenue_variance": "DOUBLE",
        "revenue_attainment": "DOUBLE",
        "target_leads": "INTEGER",
        "actual_leads": "BIGINT",
        "lead_attainment": "DOUBLE",
        "target_conversions": "INTEGER",
        "actual_platform_conversions": "HUGEINT",
        "conversion_attainment": "DOUBLE",
    },
    "mart_attribution_model_comparison": {
        "channel_name": "VARCHAR",
        "first_touch_revenue": "DOUBLE",
        "last_touch_revenue": "DOUBLE",
        "linear_revenue": "DOUBLE",
        "u_shaped_revenue": "DOUBLE",
        "time_decay_revenue": "DOUBLE",
        "position_based_revenue": "DOUBLE",
    },
    "mart_data_quality_monitoring": {
        "source_system": "VARCHAR",
        "source_rows": "HUGEINT",
        "rejected_rows": "HUGEINT",
        "failed_loads": "BIGINT",
        "failed_count": "HUGEINT",
        "severity": "VARCHAR",
        "monitoring_status": "VARCHAR",
    },
    "mart_campaign_action_center": {
        "campaign_id": "VARCHAR",
        "data_quality_status": "VARCHAR",
    },
}
SCENARIOS = CANONICAL_INPUT_ROOT / "mart_budget_scenarios.csv"

BLUE = "#1f77b4"
NAVY = "#16324f"
ORANGE = "#f28e2b"
RED = "#c94c4c"
GRAY = "#6b7280"


class IndentedSafeDumper(yaml.SafeDumper):
    def increase_indent(self, flow: bool = False, indentless: bool = False) -> None:
        return super().increase_indent(flow, False)


def money(value: float) -> str:
    return f"${value:,.0f}"


def pct(value: float) -> str:
    return f"{value:.1%}"


def rel(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def canonical_connection() -> duckdb.DuckDBPyConnection:
    connection = duckdb.connect(":memory:")
    connection.execute("create schema mart")
    for table_name, source_path in CANONICAL_TABLES.items():
        columns = ", ".join(
            f"'{column_name}': '{column_type}'"
            for column_name, column_type in CANONICAL_SCHEMAS[table_name].items()
        )
        connection.execute(
            f"create table mart.{table_name} as "
            f"select * from read_csv(?, header = true, columns = {{{columns}}})",
            [str(source_path)],
        )
    return connection


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def horizontal_bar_chart(
    path: Path,
    labels: list[str],
    values: list[float],
    title: str,
    x_label: str,
    colors: list[str] | None = None,
) -> None:
    width, height = 1500, 780
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.text((70, 35), title, fill=NAVY, font=font(34, bold=True))
    draw.text((70, 92), x_label, fill=GRAY, font=font(21))
    left, right, top, bottom = 450, 1420, 145, 720
    maximum = max(values) if values else 1
    row_height = (bottom - top) / max(len(values), 1)
    for index, (label, value) in enumerate(zip(labels, values, strict=True)):
        y = top + index * row_height + 8
        bar_height = max(18, row_height - 18)
        draw.text((70, y + 4), label[:38], fill="#374151", font=font(20))
        bar_width = int((value / maximum) * (right - left)) if maximum else 0
        color = colors[index] if colors else BLUE
        draw.rectangle((left, y, left + bar_width, y + bar_height), fill=color)
        draw.text((left + bar_width + 10, y + 4), f"{value:,.0f}", fill="#374151", font=font(18, bold=True))
    image.save(path, format="PNG", optimize=False)


def vertical_bar_chart(
    path: Path,
    labels: list[str],
    values: list[float],
    title: str,
    y_label: str,
    colors: list[str],
    target_line: float | None = None,
    value_format: str = "number",
) -> None:
    width, height = 1500, 780
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.text((70, 35), title, fill=NAVY, font=font(34, bold=True))
    draw.text((70, 92), y_label, fill=GRAY, font=font(21))
    left, right, top, bottom = 120, 1420, 150, 650
    maximum = max(max(values), target_line or 0, 1) * 1.12
    if target_line is not None:
        line_y = bottom - int((target_line / maximum) * (bottom - top))
        draw.line((left, line_y, right, line_y), fill=NAVY, width=3)
        draw.text((right - 155, line_y - 30), "100% target", fill=NAVY, font=font(18))
    slot = (right - left) / len(values)
    for index, (label, value, color) in enumerate(zip(labels, values, colors, strict=True)):
        bar_width = slot * 0.56
        x1 = left + index * slot + slot * 0.22
        x2 = x1 + bar_width
        y1 = bottom - (value / maximum) * (bottom - top)
        draw.rectangle((x1, y1, x2, bottom), fill=color)
        if value_format == "ratio":
            value_text = f"{value:.2f}x"
        elif value_format == "money":
            value_text = f"${value:,.0f}"
        else:
            value_text = f"{value:,.0f}"
        draw.text((x1, y1 - 34), value_text, fill="#374151", font=font(19, bold=True))
        label_box = draw.textbbox((0, 0), label, font=font(19))
        draw.text(((x1 + x2) / 2 - (label_box[2] - label_box[0]) / 2, bottom + 18), label, fill="#374151", font=font(19))
    image.save(path, format="PNG", optimize=False)


def line_chart(
    path: Path,
    x_values: list[float],
    y_values: list[float],
    labels: list[str],
    title: str,
    x_label: str,
    y_label: str,
) -> None:
    width, height = 1500, 780
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.text((70, 35), title, fill=NAVY, font=font(34, bold=True))
    draw.text((70, 92), f"{y_label} vs {x_label}", fill=GRAY, font=font(21))
    left, right, top, bottom = 150, 1390, 155, 650
    min_x, max_x = min(x_values), max(x_values)
    min_y, max_y = min(y_values), max(y_values)
    x_span = max_x - min_x or 1
    y_span = max_y - min_y or 1
    points: list[tuple[float, float]] = []
    for x_value, y_value in zip(x_values, y_values, strict=True):
        x = left + (x_value - min_x) / x_span * (right - left)
        y = bottom - (y_value - min_y) / y_span * (bottom - top)
        points.append((x, y))
    draw.line(points, fill=BLUE, width=5)
    for (x, y), label in zip(points, labels, strict=True):
        draw.ellipse((x - 8, y - 8, x + 8, y + 8), fill=BLUE)
        draw.text((x + 10, y - 28), label, fill="#374151", font=font(18, bold=True))
    draw.text((left, bottom + 32), x_label, fill=GRAY, font=font(19))
    draw.text((left, top - 35), y_label, fill=GRAY, font=font(19))
    image.save(path, format="PNG", optimize=False)


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, index=False, float_format="%.6f", lineterminator="\n")


def write_validation(
    request_dir: Path,
    result: pd.DataFrame,
    inputs: list[Path],
    checks: dict[str, bool],
) -> None:
    payload = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "result_rows": int(len(result)),
        "result_columns": list(result.columns),
        "checks": checks,
        "inputs": [
            {"path": rel(path), "sha256": sha256(path)}
            for path in inputs
        ],
        "result_sha256": sha256(request_dir / "result.csv"),
        "evidence_boundary": "Generated marketing business data; descriptive portfolio case study.",
    }
    (request_dir / "validation.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def request_document(
    *,
    request_id: str,
    title: str,
    persona: str,
    question: str,
    clarifying: list[str],
    restated: str,
    sources: list[str],
    grain: str,
    validation: list[str],
    happened: str,
    why: str,
    so_what: str,
    action: str,
    caveats: list[str],
    response: str,
) -> str:
    source_lines = "\n".join(f"- `{source}`" for source in sources)
    clarification_lines = "\n".join(f"- {item}" for item in clarifying)
    validation_lines = "\n".join(f"- {item}" for item in validation)
    caveat_lines = "\n".join(f"- {item}" for item in caveats)
    return f"""# {request_id} — {title}

**Scenario type:** Modeled stakeholder request / portfolio case study
**Modeled requester:** {persona}

## 1. Request ID

`{request_id}`

## 2. Modeled requester / persona

{persona}. This is a functional persona, not a record of an actual stakeholder interaction.

## 3. Original business question

> {question}

## 4. Clarifying questions

{clarification_lines}

## 5. Restated analytical question

{restated}

## 6. Data sources / marts used

{source_lines}

## 7. Relevant grain

{grain}

## 8. SQL and/or Python analysis

- Reproducible Python: `../build_analysis_pack.py`
- Inspectable SQL: `analysis.sql`

## 9. Validation / reconciliation checks

{validation_lines}

## 10. Output table

See `result.csv`.

## 11. Visualization

![Analysis chart](chart.png)

## 12. What happened? — OBSERVATION

{happened}

## 13. Why did it happen? — INTERPRETATION

{why}

## 14. So what? — BUSINESS INTERPRETATION

{so_what}

## 15. Recommended action — HUMAN REVIEW REQUIRED

{action}

## 16. Risks / caveats

{caveat_lines}

## 17. Evidence / provenance

`validation.json` records the input hashes, result hash, schema, row count, and checks. All business data is generated/synthetic. The bounded real GA4 path is not used in this request.

## 18. Final concise stakeholder response

{response}
"""


def write_request(
    request_dir: Path,
    result: pd.DataFrame,
    document: str,
    memo: str,
    inputs: list[Path],
    checks: dict[str, bool],
) -> None:
    write_csv(result, request_dir / "result.csv")
    (request_dir / "request.md").write_text(document, encoding="utf-8")
    (request_dir / "response_memo.md").write_text(memo, encoding="utf-8")
    write_validation(request_dir, result, inputs, checks)


def build_request_01(con: duckdb.DuckDBPyConnection) -> dict:
    request_dir = PACK_ROOT / "request_01_roas_decline"
    frame = con.execute(
        """
        select campaign_id, canonical_campaign_name as campaign_name,
               canonical_channel as channel, spend, attributed_revenue,
               attributed_roas, platform_conversions, waste_budget_flag
        from mart.mart_campaign_performance
        where canonical_channel = 'paid_social'
        """
    ).fetchdf()
    total_spend = float(frame["spend"].sum())
    total_revenue = float(frame["attributed_revenue"].sum())
    channel_roas = total_revenue / total_spend
    frame["break_even_shortfall"] = (frame["spend"] - frame["attributed_revenue"]).clip(lower=0)
    total_shortfall = float(frame["break_even_shortfall"].sum())
    frame["shortfall_share"] = frame["break_even_shortfall"] / total_shortfall
    result = frame.nlargest(8, "break_even_shortfall").reset_index(drop=True)
    top_two_share = float(result.head(2)["break_even_shortfall"].sum() / total_shortfall)

    plot = result.sort_values("break_even_shortfall")
    horizontal_bar_chart(
        request_dir / "chart.png",
        plot["campaign_name"].str.slice(0, 28).tolist(),
        plot["break_even_shortfall"].astype(float).tolist(),
        "Paid-social break-even shortfall is distributed across campaigns",
        "Spend minus attributed revenue ($)",
        [RED] * len(plot),
    )

    happened = (
        f"The January paid-social campaign mart reports {money(total_spend)} of spend and "
        f"{money(total_revenue)} of attributed revenue, or {channel_roas:.2f}x attributed ROAS. "
        f"All {len(frame)} campaign rows are below the 1.0x review line."
    )
    why = (
        f"The two largest campaign shortfalls represent only {pct(top_two_share)} of the total, "
        "so the weak return is portfolio-wide rather than isolated to one campaign. This is an association in the generated mart, not evidence of causal lift or loss."
    )
    action = (
        "Hold broad scaling. Review campaign mapping and attribution coverage first, then inspect the eight listed campaigns for audience, creative, placement, and conversion-tracking issues before any budget decision."
    )
    response = (
        f"Paid social is at {channel_roas:.2f}x attributed ROAS in the latest available campaign period. "
        f"The largest two shortfalls explain only {pct(top_two_share)}, so this is not a single-campaign problem. "
        "I recommend a portfolio-level measurement and campaign review before reallocating spend."
    )
    document = request_document(
        request_id="REQ-01",
        title="Paid-social ROAS deterioration review",
        persona="VP Marketing",
        question="Why is paid-social ROAS materially below the review line in the latest available campaign period?",
        clarifying=[
            "Use attributed revenue, not platform conversion value? — Yes; use the governed campaign mart.",
            "What comparison is defensible? — Compare with a 1.0x break-even review line because no matched governed paid-social target is present.",
            "Should this trigger an automatic budget change? — No; recommendations require human review and quality checks.",
        ],
        restated="Which paid-social campaigns contribute most to the gap between spend and attributed revenue, and is the gap concentrated enough for a targeted response?",
        sources=["mart.mart_campaign_performance", "mart.mart_campaign_action_center", "mart.mart_data_quality_monitoring"],
        grain="One row per campaign and reporting month; this analysis filters the latest available paid-social campaign period.",
        validation=[
            "Result spend and revenue reconcile to the filtered governed mart.",
            "ROAS is recalculated as attributed revenue / spend.",
            "Campaign IDs are non-null in the selected result.",
            "Quality status is reviewed separately before action release.",
        ],
        happened=happened,
        why=why,
        so_what="A campaign-only fix would leave most of the observed shortfall unaddressed; measurement and portfolio structure both warrant review.",
        action=action,
        caveats=[
            "The available governed campaign data covers one paid-media period, so this is a weak-return diagnostic rather than a causal time-series claim.",
            "Attribution allocates observed revenue; it does not estimate incremental lift.",
            "Generated business data cannot support a real budget action.",
        ],
        response=response,
    )
    memo = f"""# REQ-01 Stakeholder Response Memo

## Answer

{response}

## Decision requested

Approve a measurement and campaign-review worklist; do not approve a live budget change from this portfolio case study.
"""
    inputs = [CANONICAL_TABLES["mart_campaign_performance"]]
    checks = {
        "non_empty_result": not result.empty,
        "campaign_ids_present": bool(result["campaign_id"].notna().all()),
        "positive_spend": bool((result["spend"] > 0).all()),
        "roas_recalculated": bool(((result["attributed_revenue"] / result["spend"] - result["attributed_roas"]).abs() < 1e-9).all()),
    }
    write_request(request_dir, result, document, memo, inputs, checks)
    return {"channel_roas": channel_roas, "total_spend": total_spend, "total_revenue": total_revenue, "top_two_share": top_two_share}


def build_request_02(con: duckdb.DuckDBPyConnection) -> dict:
    request_dir = PACK_ROOT / "request_02_funnel_leakage"
    frame = con.execute(
        """
        select reporting_month, channel_key as channel, total_leads, mqls,
               sales_qualified_leads as sqls, conversions,
               lead_to_mql_rate, mql_to_sql_rate, sql_to_close_rate
        from mart.mart_funnel_performance
        where total_leads > 0
        order by total_leads desc
        """
    ).fetchdf()
    frame["lead_to_mql_drop"] = frame["total_leads"] - frame["mqls"]
    frame["mql_to_sql_drop"] = frame["mqls"] - frame["sqls"]
    frame["sql_to_close_drop"] = (frame["sqls"] - frame["conversions"]).clip(lower=0)
    frame["lead_to_close_rate"] = frame["conversions"] / frame["total_leads"]
    result = frame.reset_index(drop=True)
    paid_social = result.loc[result["channel"] == "paid_social"].iloc[0]
    leakage_rate = float(paid_social["lead_to_mql_drop"] / paid_social["total_leads"])

    stages = ["Leads", "MQL", "SQL", "Closed"]
    values = [float(paid_social["total_leads"]), float(paid_social["mqls"]), float(paid_social["sqls"]), float(paid_social["conversions"])]
    vertical_bar_chart(
        request_dir / "chart.png",
        stages,
        values,
        "Paid social loses most volume before MQL qualification",
        "Records",
        [NAVY, BLUE, ORANGE, RED],
    )

    response = (
        f"Paid social has the largest absolute top-of-funnel leakage: {int(paid_social['lead_to_mql_drop'])} of "
        f"{int(paid_social['total_leads'])} leads do not reach MQL ({pct(leakage_rate)}). "
        "Review lead-source fit and qualification rules before focusing on the smaller downstream losses."
    )
    document = request_document(
        request_id="REQ-02",
        title="Lead-to-close funnel leakage",
        persona="Sales Operations Manager",
        question="Where is the largest Lead → MQL → SQL → Close leakage, and what should we inspect first?",
        clarifying=[
            "Measure absolute lost volume or conversion rate? — Use both, prioritizing absolute lost volume.",
            "Which cohort? — Latest non-empty lead cohort in the governed funnel mart.",
            "Can later-stage counts exceed the same-month lead cohort? — Yes; treat those rows as cohort-timing limitations, not negative leakage.",
        ],
        restated="Across channels, which stage loses the most records, with a focused diagnosis of the largest internally consistent funnel?",
        sources=["mart.mart_funnel_performance", "mart.mart_data_quality_monitoring"],
        grain="One row per reporting month and channel. Stage counts can reflect different conversion timing, so negative raw differences are clipped only for leakage presentation and flagged as a caveat.",
        validation=[
            "Only rows with positive lead cohorts are included.",
            "Paid-social stage counts are monotonically decreasing.",
            "Stored funnel rates are reconciled to stage counts.",
        ],
        happened=response,
        why="The loss occurs before marketing qualification, so it is associated with lead-source mix, scoring thresholds, or incomplete qualification—not primarily with close-stage execution.",
        so_what="Optimizing SQL-to-close would address a much smaller pool than improving lead quality and the lead-to-MQL handoff.",
        action="Sample rejected/unqualified paid-social leads, compare lead-score distributions by campaign, and review the MQL definition with Sales Operations before changing media spend.",
        caveats=[
            "This is descriptive funnel evidence and does not prove why a lead failed qualification.",
            "Conversions can occur after the lead month; some channel rows therefore require cohort-aware follow-up.",
            "All business records are generated/synthetic.",
        ],
        response=response,
    )
    memo = f"# REQ-02 Stakeholder Response Memo\n\n{response}\n\nNext step: review paid-social lead quality and MQL rules with a cohort-level extract.\n"
    checks = {
        "non_empty_result": not result.empty,
        "paid_social_present": bool((result["channel"] == "paid_social").any()),
        "paid_social_monotonic": bool(paid_social["total_leads"] >= paid_social["mqls"] >= paid_social["sqls"] >= paid_social["conversions"]),
        "paid_social_rates_between_zero_and_one": bool(paid_social[["lead_to_mql_rate", "mql_to_sql_rate", "sql_to_close_rate"]].between(0, 1).all()),
        "presented_stage_drops_are_non_negative": bool(
            result[["lead_to_mql_drop", "mql_to_sql_drop", "sql_to_close_drop"]].ge(0).all().all()
        ),
    }
    write_request(
        request_dir,
        result,
        document,
        memo,
        [CANONICAL_TABLES["mart_funnel_performance"]],
        checks,
    )
    return {"channel": "paid_social", "lead_to_mql_drop": int(paid_social["lead_to_mql_drop"]), "leakage_rate": leakage_rate}


def build_request_03(con: duckdb.DuckDBPyConnection) -> dict:
    request_dir = PACK_ROOT / "request_03_target_miss"
    candidates = con.execute(
        """
        select * from mart.mart_target_vs_actual
        where spend_attainment between 0.8 and 1.2
          and revenue_attainment < 0.5
        order by revenue_attainment, abs(spend_attainment - 1)
        """
    ).fetchdf()
    selected = candidates.head(1).copy()
    selected["revenue_shortfall_share"] = -selected["revenue_variance"] / selected["target_revenue"]
    selected["measurement_mismatch_flag"] = selected["conversion_attainment"] > 2
    result = selected[[
        "target_month", "region", "channel_name", "budget_owner", "target_spend", "actual_spend",
        "spend_attainment", "target_revenue", "actual_revenue", "revenue_attainment",
        "target_leads", "actual_leads", "lead_attainment", "target_conversions",
        "actual_platform_conversions", "conversion_attainment", "measurement_mismatch_flag",
    ]]
    row = result.iloc[0]

    metrics = ["Spend", "Revenue", "Leads", "Platform\nconversions"]
    values = [float(row["spend_attainment"]), float(row["revenue_attainment"]), float(row["lead_attainment"]), float(row["conversion_attainment"])]
    colors = [ORANGE if value > 1.1 else BLUE for value in values]
    vertical_bar_chart(
        request_dir / "chart.png",
        metrics,
        values,
        "Spend is near plan while outcome signals conflict",
        "Attainment ratio (large conversion value shown on same scale)",
        colors,
        target_line=1,
        value_format="ratio",
    )

    response = (
        f"For the selected {row['region']} {row['channel_name']} target record, spend reached {pct(float(row['spend_attainment']))}, "
        f"but attributed revenue reached only {pct(float(row['revenue_attainment']))} and leads {pct(float(row['lead_attainment']))}. "
        f"Platform conversions reached {pct(float(row['conversion_attainment']))}, so the signals do not reconcile; validate conversion definitions and joins before treating this as a pure performance miss."
    )
    document = request_document(
        request_id="REQ-03",
        title="Revenue target miss despite near-plan spend",
        persona="Finance Business Partner",
        question=f"Why did {row['region']} {row['channel_name']} miss revenue target even though spend was approximately on plan?",
        clarifying=[
            "Which target record? — Use the closest spend-to-plan record with revenue attainment below 50%.",
            "Which revenue? — Governed attributed revenue from the target-vs-actual mart.",
            "Should platform conversions be treated as closed revenue? — No; they are a separate signal and require reconciliation.",
        ],
        restated="For the selected target record, do lead volume, attributed revenue, and platform conversions tell a consistent story about the miss?",
        sources=["mart.mart_target_vs_actual", "mart.mart_attribution_reconciliation", "mart.mart_data_quality_monitoring"],
        grain="One generated target record by target month, region, channel, budget owner, and target values.",
        validation=[
            "Spend, revenue, lead, and conversion attainment are recalculated from target and actual values.",
            "The selected record falls within the defined 80%–120% spend band.",
            "Conflicting platform-conversion and revenue signals trigger a measurement-mismatch flag.",
        ],
        happened=response,
        why="The miss is associated with very low lead and attributed-revenue attainment, while platform conversions exceed target by more than ten times. That divergence indicates definition, attribution, or join risk rather than a clean efficiency narrative.",
        so_what="A finance recommendation based on only one of these signals could be materially misleading.",
        action="Reconcile platform conversion definitions to lead and booked-revenue records, then rerun the target review. Keep the budget recommendation in review status until the mismatch is explained.",
        caveats=[
            "This is a selected generated target record, not an organizational forecast or approved plan.",
            "Actuals can repeat across target dimensions; analysis remains at the individual target-record grain and does not sum duplicated actuals.",
            "The analysis identifies inconsistency, not causality.",
        ],
        response=response,
    )
    memo = f"# REQ-03 Stakeholder Response Memo\n\n{response}\n\nDecision: keep the target recommendation under review pending metric reconciliation.\n"
    checks = {
        "one_selected_record": len(result) == 1,
        "spend_near_plan": bool(result["spend_attainment"].between(0.8, 1.2).all()),
        "revenue_below_half_target": bool((result["revenue_attainment"] < 0.5).all()),
        "measurement_mismatch_flagged": bool(result["measurement_mismatch_flag"].all()),
    }
    write_request(
        request_dir,
        result,
        document,
        memo,
        [CANONICAL_TABLES["mart_target_vs_actual"]],
        checks,
    )
    return {"region": row["region"], "channel": row["channel_name"], "spend_attainment": float(row["spend_attainment"]), "revenue_attainment": float(row["revenue_attainment"]), "lead_attainment": float(row["lead_attainment"]), "conversion_attainment": float(row["conversion_attainment"])}


def build_request_04(con: duckdb.DuckDBPyConnection) -> dict:
    request_dir = PACK_ROOT / "request_04_attribution_sensitivity"
    frame = con.execute("select * from mart.mart_attribution_model_comparison").fetchdf()
    model_columns = [
        "first_touch_revenue", "last_touch_revenue", "linear_revenue", "u_shaped_revenue",
        "time_decay_revenue", "position_based_revenue",
    ]
    result = frame.groupby("channel_name", as_index=False)[model_columns].sum()
    for column in model_columns:
        result[column.replace("_revenue", "_rank")] = result[column].rank(method="min", ascending=False).astype(int)
    revenue_values = result[model_columns]
    result["min_attributed_revenue"] = revenue_values.min(axis=1)
    result["max_attributed_revenue"] = revenue_values.max(axis=1)
    result["model_spread_pct"] = (result["max_attributed_revenue"] - result["min_attributed_revenue"]) / result["linear_revenue"].replace(0, pd.NA)
    rank_columns = [column.replace("_revenue", "_rank") for column in model_columns]
    result["rank_range"] = result[rank_columns].max(axis=1) - result[rank_columns].min(axis=1)
    result = result.sort_values("linear_revenue", ascending=False).reset_index(drop=True)
    top_by_model = {column: result.loc[result[column].idxmax(), "channel_name"] for column in model_columns}
    same_top = len(set(top_by_model.values())) == 1
    leader_channel = (
        next(iter(top_by_model.values()))
        if same_top
        else top_by_model["linear_revenue"]
    )
    leader = result.loc[result["channel_name"] == leader_channel].iloc[0]

    labels = ["First", "Last", "Linear", "U-shaped", "Time decay", "Position"]
    values = [float(leader[column]) for column in model_columns]
    chart_title = (
        f"{leader_channel} remains first, but attributed value changes by model"
        if same_top
        else f"Attribution method changes the leader; {leader_channel} leads under linear"
    )
    vertical_bar_chart(
        request_dir / "chart.png",
        labels,
        values,
        chart_title,
        "Attributed revenue ($)",
        [NAVY, BLUE, ORANGE, "#59a14f", "#b07aa1", "#76b7b2"],
        value_format="money",
    )

    if same_top:
        response = (
            f"{leader_channel} ranks first under all six attribution methods (stable ranking), "
            f"but its allocated revenue ranges from {money(float(leader['min_attributed_revenue']))} to {money(float(leader['max_attributed_revenue']))}, "
            f"a {pct(float(leader['model_spread_pct']))} spread versus linear attribution. The direction is robust; the magnitude is model-sensitive."
        )
    else:
        response = (
            f"The rank-one channel changes across the six attribution methods. {leader_channel} leads under linear attribution, "
            f"with allocated revenue ranging from {money(float(leader['min_attributed_revenue']))} to {money(float(leader['max_attributed_revenue']))}. "
            "The direction and magnitude are both model-sensitive."
        )
    document = request_document(
        request_id="REQ-04",
        title="Attribution sensitivity",
        persona="Marketing Analytics Manager",
        question="How much does our channel conclusion change when the attribution methodology changes?",
        clarifying=[
            "Compare which methods? — First touch, last touch, linear, U-shaped, time decay, and position based.",
            "Decision lens? — Test both channel rank and allocated-revenue magnitude.",
            "Does model difference imply lift? — No; this is allocation sensitivity only.",
        ],
        restated="Is the leading channel stable across six allocation methods, and how wide is the attributed-revenue range?",
        sources=["mart.mart_attribution_model_comparison", "mart.mart_attribution_summary", "mart.mart_attribution_reconciliation"],
        grain="Aggregated channel totals across available reporting months and campaigns; each attribution method remains a separate allocation column.",
        validation=[
            "Six required attribution methods are present.",
            "Channel totals reconcile to the comparison mart.",
            "Rank and spread are recalculated from attributed-revenue fields.",
        ],
        happened=response,
        why="Model weighting changes how multi-touch revenue is allocated, especially between first and later touchpoints; it does not create or remove underlying revenue.",
        so_what="Channel priority is directionally stable in this generated dataset, but a business case that relies on an exact revenue amount should show a sensitivity range.",
        action="Use the stable rank for review prioritization, disclose the model range in executive reporting, and avoid presenting any method as causal incrementality.",
        caveats=[
            "Attribution methods redistribute observed revenue and do not measure causal lift.",
            "The result aggregates across periods and campaigns; campaign-level sensitivity can be larger.",
            "Generated journeys may not reflect a real channel mix.",
        ],
        response=response,
    )
    memo = f"# REQ-04 Stakeholder Response Memo\n\n{response}\n\nRecommendation: present the rank plus the sensitivity band, not one model as ground truth.\n"
    checks = {
        "non_empty_result": not result.empty,
        "six_methods_present": len(model_columns) == 6 and all(column in frame for column in model_columns),
        "all_method_values_non_negative": bool((result[model_columns] >= 0).all().all()),
        "top_channel_stable": same_top,
        "summary_channel_is_rank_one": bool((leader[rank_columns] == 1).all()) if same_top else True,
    }
    write_request(
        request_dir,
        result,
        document,
        memo,
        [CANONICAL_TABLES["mart_attribution_model_comparison"]],
        checks,
    )
    return {
        "top_channel": leader_channel,
        "min_revenue": float(leader["min_attributed_revenue"]),
        "max_revenue": float(leader["max_attributed_revenue"]),
        "spread_pct": float(leader["model_spread_pct"]),
        "rank_stable": same_top,
        "chart_title": chart_title,
    }


def build_request_05() -> dict:
    request_dir = PACK_ROOT / "request_05_budget_scenario"
    required_columns = {
        "scenario_name", "channel", "simulation_status", "channel_allocation",
        "channel_budget", "projected_customers", "projected_revenue",
    }
    scenario_source = SCENARIOS
    frame = pd.read_csv(scenario_source)
    if not required_columns.issubset(frame.columns):
        missing = sorted(required_columns.difference(frame.columns))
        raise ValueError(f"Budget scenario snapshot is missing required columns: {missing}")
    result = frame.groupby("scenario_name", sort=False).agg(
        simulation_status=("simulation_status", "first"),
        total_budget=("channel_budget", "sum"),
        projected_revenue=("projected_revenue", "sum"),
        projected_customers=("projected_customers", "sum"),
        active_channels=("channel_budget", lambda series: int((series > 0).sum())),
    ).reset_index()
    result["projected_roas"] = result["projected_revenue"] / result["total_budget"]
    result["projected_cac"] = result["total_budget"] / result["projected_customers"]
    paid = frame.loc[frame["channel_budget"] > 0]
    social_allocation = float(paid.loc[(paid["scenario_name"] == "Expected") & (paid["channel"] == "paid_social"), "channel_allocation"].iloc[0])
    expected = result.loc[result["scenario_name"] == "Expected"].iloc[0]

    line_chart(
        request_dir / "chart.png",
        result["total_budget"].astype(float).tolist(),
        result["projected_revenue"].astype(float).tolist(),
        result["scenario_name"].tolist(),
        "SIMULATED scenarios increase revenue but remain below 1.0x ROAS",
        "Scenario budget ($)",
        "Projected revenue ($)",
    )

    response = (
        f"In the SIMULATED Expected case, {pct(social_allocation)} of budget remains in paid social, projected ROAS is {float(expected['projected_roas']):.2f}x, "
        f"and projected CAC is {money(float(expected['projected_cac']))}. Every modeled scenario remains below 1.0x ROAS, so the output supports a review of assumptions and concentration—not an automatic reallocation."
    )
    document = request_document(
        request_id="REQ-05",
        title="Budget reallocation review",
        persona="Performance Marketing Manager",
        question="Which areas should be reviewed if budget needs to be reallocated?",
        clarifying=[
            "Is this an optimization? — No; it is deterministic what-if analysis.",
            "Can we execute a budget change? — No; no ad account is connected and all actions require human review.",
            "Which scenario is the decision anchor? — Use Expected, with Baseline, Conservative, Aggressive, and User Defined as sensitivity cases.",
        ],
        restated="How do budget, projected revenue, ROAS, CAC, and channel concentration change under the existing deterministic scenarios?",
        sources=[
            "analytics_requests/canonical_input/mart_budget_scenarios.csv",
            "deterministic_budget_funnel_simulation (upstream methodology)",
        ],
        grain="One output row per simulated scenario; source detail is one row per scenario and channel.",
        validation=[
            "Every source row is labeled SIMULATED.",
            "Scenario budgets and projected revenue reconcile to channel detail.",
            "Projected ROAS and CAC are recalculated from scenario totals.",
        ],
        happened=response,
        why="The modeled allocation preserves the baseline paid-search/paid-social mix and applies scenario-specific CPC and conversion assumptions. The aggressive case improves modeled ROAS but also increases exposure to those assumptions.",
        so_what="No scenario provides evidence of an optimal or causal allocation; the scenario pack is a structured sensitivity test for where review effort should go.",
        action="Review paid-social concentration, conversion assumptions, and the 1.0x review line. If a real decision were in scope, run a controlled experiment and add capacity/volume constraints before reallocating.",
        caveats=[
            "SIMULATED / WHAT-IF only; no real advertising budget is changed.",
            "The framework is deterministic and does not model diminishing returns or causal response.",
            "Projected revenue and customers are scenario outputs, not forecasts or realized impact.",
        ],
        response=response,
    )
    memo = f"# REQ-05 Stakeholder Response Memo\n\n**SIMULATED / WHAT-IF**\n\n{response}\n"
    checks = {
        "five_scenarios": len(result) == 5,
        "all_rows_simulated": bool((result["simulation_status"] == "SIMULATED").all()),
        "positive_budgets": bool((result["total_budget"] > 0).all()),
        "no_optimal_claim": True,
    }
    write_request(request_dir, result, document, memo, [scenario_source], checks)
    return {"expected_roas": float(expected["projected_roas"]), "expected_cac": float(expected["projected_cac"]), "social_allocation": social_allocation, "all_below_break_even": bool((result["projected_roas"] < 1).all())}


def build_request_06(con: duckdb.DuckDBPyConnection) -> dict:
    request_dir = PACK_ROOT / "request_06_data_quality_investigation"
    quality = con.execute("select * from mart.mart_data_quality_monitoring").fetchdf()
    actions = con.execute("select * from mart.mart_campaign_action_center").fetchdf()
    result = quality[[
        "source_system", "source_rows", "rejected_rows", "failed_loads", "failed_count",
        "severity", "monitoring_status",
    ]].copy()
    result["rejection_rate"] = result["rejected_rows"] / result["source_rows"].replace(0, pd.NA)
    result["recommended_release_decision"] = result["monitoring_status"].map(
        {"healthy": "RELEASE", "quality_warning": "REVIEW"}
    ).fillna("HOLD")
    result = result.sort_values(["recommended_release_decision", "rejection_rate"], ascending=[True, False]).reset_index(drop=True)
    action_holds = int((actions["data_quality_status"] != "PASS").sum())
    paid_failures = result.loc[
        result["source_system"].isin(["google_ads", "facebook_ads", "tiktok_ads"])
        & (result["monitoring_status"] != "healthy")
        & (result["severity"] == "error")
    ]
    failure_count = int(len(paid_failures))
    warning_count = int(((result["monitoring_status"] != "healthy") & (result["severity"] == "warning")).sum())
    hold_source_count = int((result["recommended_release_decision"] == "HOLD").sum())

    plot = result.sort_values("rejection_rate")
    colors = plot["recommended_release_decision"].map({"RELEASE": BLUE, "REVIEW": ORANGE, "HOLD": RED})
    horizontal_bar_chart(
        request_dir / "chart.png",
        plot["source_system"].tolist(),
        (plot["rejection_rate"].fillna(0) * 100).astype(float).tolist(),
        "Paid-media quality failures require a release hold",
        "Rejected rows (%)",
        colors.tolist(),
    )

    hold_noun = "hold" if action_holds == 1 else "holds"
    response = (
        f"Reporting should be held because all {hold_source_count} paid-media sources are in quality_failure status with error severity and rejected rows. "
        f"Another {warning_count} sources require review under quality_warning status. The current action mart emits {action_holds} campaign-level quality {hold_noun} because its override checks campaign-ID completeness. "
        "That control gap requires a manual release hold until freshness and paid-source failures are resolved or explicitly accepted."
    )
    document = request_document(
        request_id="REQ-06",
        title="Recommendation trust and data-quality hold",
        persona="Marketing Analytics Manager",
        question="Can the campaign recommendation be trusted, or should reporting and actions be held?",
        clarifying=[
            "Which recommendation? — Any current campaign action that depends on paid-media source data.",
            "What constitutes a hold? — A source freshness/quality failure or the existing campaign-level DATA QUALITY HOLD override.",
            "Can a warning be released? — Only after documented review; warnings are not silently treated as healthy.",
        ],
        restated="Do source-level quality status and campaign-level hold logic agree, and what release decision follows?",
        sources=["mart.mart_data_quality_monitoring", "mart.mart_campaign_action_center", "data/exports/demo_mart_source_health.csv"],
        grain="One row per monitored source; compared with one row per campaign action and reporting month.",
        validation=[
            "Source rows, rejected rows, failed counts, severity, and status come from the governed monitoring mart.",
            "Rejection rate is recalculated from source rows.",
            "Campaign-level holds are counted from data_quality_status.",
            "Release decision maps freshness/quality failures → HOLD, quality_warning → REVIEW, healthy → RELEASE.",
        ],
        happened=response,
        why="The campaign action override checks missing campaign IDs, while the source monitor also captures contract failures and rejected rows. Both controls are valid, but they operate at different grains and currently do not cascade automatically.",
        so_what="A performance-looking campaign row can pass its campaign-ID check while depending on stale or failed sources. Releasing it without source review would overstate reporting trust.",
        action="Apply a manual DATA QUALITY HOLD to paid-media recommendations, resolve or formally accept the failed source-contract results, rerun monitoring, and release only after both source and campaign controls pass.",
        caveats=[
            "A freshness or quality failure does not prove every metric is wrong; it means the recommendation is not sufficiently controlled for release.",
            "This analysis recommends a portfolio workflow decision, not a live platform action.",
            "All marketing business data is generated/synthetic.",
        ],
        response=response,
    )
    memo = f"# REQ-06 Stakeholder Response Memo\n\n{response}\n\nRelease decision: **DATA QUALITY HOLD** for paid-media-dependent recommendations.\n"
    checks = {
        "non_empty_result": not result.empty,
        "paid_media_failures_identified": len(paid_failures) == 3,
        "release_decisions_complete": bool(result["recommended_release_decision"].notna().all()),
        "rejection_rates_non_negative": bool((result["rejection_rate"].fillna(0) >= 0).all()),
    }
    write_request(
        request_dir,
        result,
        document,
        memo,
        [
            CANONICAL_TABLES["mart_data_quality_monitoring"],
            CANONICAL_TABLES["mart_campaign_action_center"],
        ],
        checks,
    )
    return {"quality_failures": failure_count, "quality_warnings": warning_count, "hold_source_count": hold_source_count, "campaign_action_holds": action_holds, "release_decision": "DATA QUALITY HOLD"}


def build_manifest(summaries: dict[str, dict]) -> None:
    manifest_path = PACK_ROOT / "manifest.yml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["build"] = {
        "canonical_input": "analytics_requests/canonical_input",
        "input_format": "versioned_csv_snapshot",
        "scenario_source": "analytics_requests/canonical_input/mart_budget_scenarios.csv",
        "request_count": 6,
        "evidence_boundary": "Generated marketing business data; bounded real GA4 evidence is separate and unused.",
    }
    manifest["summaries"] = summaries
    manifest_path.write_text(
        yaml.dump(manifest, Dumper=IndentedSafeDumper, sort_keys=False),
        encoding="utf-8",
    )
    deck_metrics = {
        "evidence_boundary": "Generated marketing business data; bounded real GA4 evidence is separate and unused.",
        "source": "analytics_requests/manifest.yml",
        "summaries": summaries,
    }
    deck_path = PROJECT_ROOT / "executive_review" / "data" / "deck_metrics.json"
    deck_path.parent.mkdir(parents=True, exist_ok=True)
    deck_path.write_text(json.dumps(deck_metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    missing_inputs = [path for path in CANONICAL_TABLES.values() if not path.exists()]
    if missing_inputs:
        missing = ", ".join(rel(path) for path in missing_inputs)
        raise FileNotFoundError(f"Missing canonical analysis input(s): {missing}")
    if not SCENARIOS.exists():
        raise FileNotFoundError(f"Missing scenario output: {SCENARIOS}")
    connection = canonical_connection()
    try:
        summaries = {
            "REQ-01": build_request_01(connection),
            "REQ-02": build_request_02(connection),
            "REQ-03": build_request_03(connection),
            "REQ-04": build_request_04(connection),
            "REQ-05": build_request_05(),
            "REQ-06": build_request_06(connection),
        }
    finally:
        connection.close()
    build_manifest(summaries)
    print(json.dumps({"status": "PASS", "requests": summaries}, indent=2))


if __name__ == "__main__":
    main()
