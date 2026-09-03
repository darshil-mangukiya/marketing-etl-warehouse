import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "..");
const FINAL_PPTX = path.join(HERE, "Marketing_Monthly_Business_Review.pptx");
const RENDER_DIR = path.join(process.env.TMPDIR || "/tmp", "p2_marketing_mbr_rendered");

const COLORS = {
  ink: "#172B4D",
  muted: "#5E6C84",
  panel: "#F1F3F5",
  rule: "#D7DCE2",
  blue: "#2F80ED",
  cyan: "#6DCBF4",
  orange: "#F2994A",
  red: "#C94C4C",
  green: "#3D8F62",
  white: "#FFFFFF",
};

function parseCsv(text) {
  const rows = text.trim().split(/\r?\n/).map((line) => {
    const values = [];
    let current = "";
    let quoted = false;
    for (let index = 0; index < line.length; index += 1) {
      const character = line[index];
      if (character === '"') {
        if (quoted && line[index + 1] === '"') {
          current += '"';
          index += 1;
        } else {
          quoted = !quoted;
        }
      } else if (character === "," && !quoted) {
        values.push(current);
        current = "";
      } else {
        current += character;
      }
    }
    values.push(current);
    return values;
  });
  const headers = rows[0];
  return rows.slice(1).map((row) => Object.fromEntries(headers.map((header, index) => [header, row[index]])));
}

async function readCsv(relativePath) {
  return parseCsv(await fs.readFile(path.join(ROOT, relativePath), "utf8"));
}

function addBox(slide, name, left, top, width, height, fill = COLORS.panel, lineFill = COLORS.rule) {
  return slide.shapes.add({
    geometry: "rect",
    name,
    position: { left, top, width, height },
    fill,
    line: { style: "solid", fill: lineFill, width: 1 },
  });
}

function addText(slide, name, text, left, top, width, height, options = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    name,
    position: { left, top, width, height },
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = String(text);
  shape.text.style = {
    fontSize: options.fontSize ?? 22,
    typeface: "Arial",
    bold: options.bold ?? false,
    color: options.color ?? COLORS.ink,
    alignment: options.alignment ?? "left",
    verticalAlignment: options.verticalAlignment ?? "top",
  };
  return shape;
}

function addTitle(slide, title, slideNumber) {
  addText(slide, `slide-${slideNumber}-title`, title, 58, 36, 1120, 66, { fontSize: 48, bold: true });
  addText(slide, `slide-${slideNumber}-footer`, `MODELED PORTFOLIO CASE STUDY   ${slideNumber}`, 58, 675, 1164, 20, {
    fontSize: 14,
    color: COLORS.muted,
    alignment: "right",
  });
}

function addKpi(slide, name, value, label, left, top, width, accent = COLORS.blue) {
  addBox(slide, `${name}-panel`, left, top, width, 196, COLORS.panel, COLORS.panel);
  addBox(slide, `${name}-accent`, left, top, 9, 196, accent, accent);
  addText(slide, `${name}-value`, value, left + 28, top + 34, width - 46, 76, { fontSize: 52, bold: true });
  addText(slide, `${name}-label`, label, left + 28, top + 122, width - 46, 48, { fontSize: 22, color: COLORS.muted });
}

function addCallout(slide, name, heading, body, left, top, width, height, accent = COLORS.blue) {
  addBox(slide, `${name}-box`, left, top, width, height, COLORS.panel, COLORS.panel);
  addBox(slide, `${name}-rule`, left, top, 8, height, accent, accent);
  addText(slide, `${name}-heading`, heading, left + 24, top + 18, width - 42, 34, { fontSize: 24, bold: true, color: accent });
  addText(slide, `${name}-body`, body, left + 24, top + 62, width - 42, height - 78, { fontSize: 20, color: COLORS.ink });
}

function addNotes(slide, sources, note = "") {
  const lines = ["[Sources]", ...sources.map((source) => `- ${source}`)];
  if (note) lines.push("", note);
  slide.speakerNotes.textFrame.setText(lines.join("\n"));
  slide.speakerNotes.setVisible(true);
}

function usdMillions(value) {
  return `$${(value / 1_000_000).toFixed(2)}M`;
}

function percent(value, digits = 0) {
  return `${(value * 100).toFixed(digits)}%`;
}

async function main() {
  const metrics = JSON.parse(await fs.readFile(path.join(HERE, "data", "deck_metrics.json"), "utf8"));
  const summaries = metrics.summaries;
  const roasRows = await readCsv("analytics_requests/request_01_roas_decline/result.csv");
  const funnelRows = await readCsv("analytics_requests/request_02_funnel_leakage/result.csv");
  const attributionRows = await readCsv("analytics_requests/request_04_attribution_sensitivity/result.csv");
  const scenarioRows = await readCsv("analytics_requests/request_05_budget_scenario/result.csv");
  const qualityRows = await readCsv("analytics_requests/request_06_data_quality_investigation/result.csv");

  const presentation = Presentation.create({ slideSize: { width: 1280, height: 720 } });
  presentation.theme.name = "Portfolio Editorial";
  presentation.theme.colorScheme = {
    name: "Portfolio Editorial",
    themeColors: {
      accent1: COLORS.blue,
      accent2: COLORS.orange,
      accent3: COLORS.green,
      accent4: COLORS.cyan,
      accent5: COLORS.red,
      accent6: COLORS.muted,
      bg1: COLORS.white,
      bg2: COLORS.panel,
      tx1: COLORS.ink,
      tx2: COLORS.muted,
      dk1: "#000000",
      dk2: COLORS.ink,
      lt1: COLORS.white,
      lt2: COLORS.panel,
      hlink: COLORS.blue,
      folHlink: "#6B4EA0",
    },
  };

  // 1 — Cover
  {
    const slide = presentation.slides.add();
    slide.background.fill = COLORS.white;
    addText(slide, "cover-eyebrow", "MONTHLY MARKETING BUSINESS REVIEW", 58, 58, 560, 34, { fontSize: 22, bold: true, color: COLORS.blue });
    addText(slide, "cover-title", "Review first.\nHold on failure.", 58, 148, 580, 176, { fontSize: 72, bold: true });
    addText(slide, "cover-subtitle", "A modeled executive review of campaign return, funnel leakage, attribution sensitivity, target variance, budget scenarios, and reporting trust.", 58, 370, 548, 130, { fontSize: 25, color: COLORS.muted });
    addBox(slide, "cover-hero", 675, 60, 547, 560, COLORS.panel, COLORS.panel);
    addText(slide, "cover-hero-value", `${summaries["REQ-01"].channel_roas.toFixed(2)}x`, 722, 148, 450, 125, { fontSize: 96, bold: true, color: COLORS.red, alignment: "center" });
    addText(slide, "cover-hero-label", "Paid-social attributed ROAS", 722, 286, 450, 46, { fontSize: 28, bold: true, alignment: "center" });
    addText(slide, "cover-hero-question", "The signal is weak—but three paid-media sources also fail quality checks. The management question is whether to optimize or pause for validation.", 738, 378, 418, 145, { fontSize: 23, color: COLORS.muted, alignment: "center" });
    addText(slide, "cover-footer", "GENERATED / SYNTHETIC MARKETING DATA · MODELED PORTFOLIO CASE STUDY", 58, 675, 1164, 20, { fontSize: 14, color: COLORS.muted, alignment: "right" });
    addNotes(slide, ["analytics_requests/manifest.yml", "executive_review/data/deck_metrics.json"]);
  }

  // 2 — Executive summary
  {
    const slide = presentation.slides.add();
    slide.background.fill = COLORS.white;
    addTitle(slide, "Validate the signal before changing budget", 2);
    addCallout(slide, "summary-what", "WHAT HAPPENED", `Paid social shows ${summaries["REQ-01"].channel_roas.toFixed(2)}x attributed ROAS. ${percent(summaries["REQ-02"].leakage_rate)} of its lead cohort does not reach MQL.`, 58, 148, 548, 188, COLORS.red);
    addCallout(slide, "summary-why", "WHY", `Weak return is distributed across campaigns, while the selected target record contains conflicting lead, revenue, and platform-conversion signals.`, 632, 148, 590, 188, COLORS.orange);
    addCallout(slide, "summary-so", "SO WHAT", `${summaries["REQ-06"].hold_source_count} paid-media sources require a release hold; ${summaries["REQ-06"].quality_warnings} other sources require review. Campaign logic emits ${summaries["REQ-06"].campaign_action_holds} automatic hold.`, 58, 370, 548, 210, COLORS.orange);
    addCallout(slide, "summary-action", "ACTION", "Apply a manual DATA QUALITY HOLD, reconcile measurement definitions, then review campaign and funnel actions. Do not execute a live budget change from this case study.", 632, 370, 590, 210, COLORS.blue);
    addNotes(slide, ["analytics_requests/request_01_roas_decline/request.md", "analytics_requests/request_02_funnel_leakage/request.md", "analytics_requests/request_06_data_quality_investigation/request.md"]);
  }

  // 3 — KPI scorecard
  {
    const slide = presentation.slides.add();
    slide.background.fill = COLORS.white;
    addTitle(slide, "The scorecard says review, not scale", 3);
    addText(slide, "scorecard-context", "Latest available governed paid-social campaign period", 58, 112, 760, 34, { fontSize: 23, color: COLORS.muted });
    addKpi(slide, "spend", usdMillions(summaries["REQ-01"].total_spend), "Paid-social spend", 58, 184, 270, COLORS.blue);
    addKpi(slide, "revenue", `$${Math.round(summaries["REQ-01"].total_revenue / 1000)}K`, "Attributed revenue", 354, 184, 270, COLORS.cyan);
    addKpi(slide, "roas", `${summaries["REQ-01"].channel_roas.toFixed(2)}x`, "Attributed ROAS", 650, 184, 270, COLORS.red);
    addKpi(slide, "leakage", percent(summaries["REQ-02"].leakage_rate), "Lead → MQL leakage", 946, 184, 276, COLORS.orange);
    addCallout(slide, "scorecard-meaning", "MANAGEMENT READING", "Performance evidence warrants investigation; it does not support a causal claim or an automatic budget cut. Quality status and attribution boundaries remain part of the decision.", 58, 430, 1164, 156, COLORS.blue);
    addNotes(slide, ["analytics_requests/request_01_roas_decline/result.csv", "analytics_requests/request_02_funnel_leakage/result.csv"]);
  }

  // 4 — Campaign variance drivers
  {
    const slide = presentation.slides.add();
    slide.background.fill = COLORS.white;
    addTitle(slide, "Weak return is not isolated to one campaign", 4);
    const top = roasRows.slice(0, 5).reverse();
    slide.charts.add("bar", {
      position: { left: 58, top: 138, width: 720, height: 470 },
      categories: top.map((row) => `CMP-${row.campaign_id.slice(-3)}\n${row.campaign_name.replace(/ 20\d\d$/, "")}`),
      series: [{
        name: "Break-even shortfall",
        values: top.map((row) => Number(row.break_even_shortfall) / 1000),
        fill: COLORS.red,
        dataLabelOverrides: top.map((row, idx) => ({ idx, text: `$${Math.round(Number(row.break_even_shortfall) / 1000)}K`, position: "outEnd", showValue: false, textStyle: { fontSize: 15, fill: COLORS.ink, bold: true } })),
      }],
      hasLegend: false,
      barOptions: { direction: "column", grouping: "clustered", gapWidth: 48 },
      xAxis: { textStyle: { fontSize: 13, fill: COLORS.ink }, line: { style: "solid", fill: COLORS.rule, width: 1 } },
      yAxis: { min: 0, max: 150, numberFormatCode: "$0\"K\"", majorGridlines: { style: "solid", fill: COLORS.rule, width: 1 }, textStyle: { fontSize: 14, fill: COLORS.muted } },
      dataLabels: { showValue: true, position: "outEnd", textStyle: { fontSize: 15, fill: COLORS.ink, bold: true } },
      chartFill: COLORS.white,
      chartLine: { style: "solid", fill: COLORS.white, width: 0 },
      plotAreaFill: { type: "none" },
    });
    addCallout(slide, "campaign-so", "SO WHAT", `The largest two shortfalls explain only ${percent(summaries["REQ-01"].top_two_share)} of the total. A one-campaign fix would leave most of the observed gap unresolved.`, 820, 168, 402, 176, COLORS.orange);
    addCallout(slide, "campaign-action", "ACTION", "Review campaign mapping, attribution coverage, and conversion tracking across the portfolio before changing spend. Prioritize the listed campaigns for diagnostic sampling.", 820, 376, 402, 204, COLORS.blue);
    addNotes(slide, ["analytics_requests/request_01_roas_decline/result.csv", "analytics_requests/request_01_roas_decline/validation.json"], "Break-even shortfall = max(spend − attributed revenue, 0). It is a review line, not a profit or incrementality estimate.");
  }

  // 5 — Funnel health
  {
    const slide = presentation.slides.add();
    slide.background.fill = COLORS.white;
    addTitle(slide, "Paid social loses most volume before MQL", 5);
    const paidSocial = funnelRows.find((row) => row.channel === "paid_social");
    slide.charts.add("bar", {
      position: { left: 58, top: 150, width: 760, height: 430 },
      categories: ["Leads", "MQL", "SQL", "Closed"],
      series: [{ name: "Records", values: [Number(paidSocial.total_leads), Number(paidSocial.mqls), Number(paidSocial.sqls), Number(paidSocial.conversions)], fill: COLORS.blue, points: [{ idx: 0, fill: COLORS.ink }, { idx: 2, fill: COLORS.orange }, { idx: 3, fill: COLORS.red }] }],
      hasLegend: false,
      barOptions: { direction: "column", grouping: "clustered", gapWidth: 65, varyColors: true },
      xAxis: { textStyle: { fontSize: 17, fill: COLORS.ink }, line: { style: "solid", fill: COLORS.rule, width: 1 } },
      yAxis: { visible: false, majorGridlines: null },
      dataLabels: { showValue: true, position: "outEnd", textStyle: { fontSize: 18, fill: COLORS.ink, bold: true } },
      chartFill: COLORS.white,
      chartLine: { style: "solid", fill: COLORS.white, width: 0 },
      plotAreaFill: { type: "none" },
    });
    addCallout(slide, "funnel-why", "WHY", `${summaries["REQ-02"].lead_to_mql_drop} of ${paidSocial.total_leads} paid-social leads do not reach MQL. The largest loss precedes Sales qualification.`, 850, 170, 372, 176, COLORS.orange);
    addCallout(slide, "funnel-action", "ACTION", "Sample unqualified leads by campaign and lead score; review source fit and the MQL definition before optimizing the smaller downstream stages.", 850, 382, 372, 198, COLORS.blue);
    addNotes(slide, ["analytics_requests/request_02_funnel_leakage/result.csv", "analytics_requests/request_02_funnel_leakage/validation.json"], "Some other channel rows contain cross-period cohort timing effects; the paid-social row is internally monotonic and is the focus here.");
  }

  // 6 — Attribution sensitivity
  {
    const slide = presentation.slides.add();
    slide.background.fill = COLORS.white;
    addTitle(slide, "Attribution changes magnitude—not the leader", 6);
    const leaderName = summaries["REQ-04"].top_channel;
    const leader = attributionRows.find((row) => row.channel_name === leaderName);
    const methods = ["First", "Last", "Linear", "U-shaped", "Time decay", "Position"];
    const values = ["first_touch_revenue", "last_touch_revenue", "linear_revenue", "u_shaped_revenue", "time_decay_revenue", "position_based_revenue"].map((key) => Number(leader[key]) / 1000);
    slide.charts.add("bar", {
      position: { left: 58, top: 146, width: 780, height: 430 },
      categories: methods,
      series: [{
        name: `${leaderName} attributed revenue`,
        values,
        fill: COLORS.blue,
        dataLabelOverrides: values.map((value, idx) => ({
          idx,
          text: `$${Math.round(value)}K`,
          position: "outEnd",
          showValue: false,
          textStyle: { fontSize: 15, fill: COLORS.ink, bold: true },
        })),
      }],
      hasLegend: false,
      barOptions: { direction: "column", grouping: "clustered", gapWidth: 48 },
      xAxis: { textStyle: { fontSize: 14, fill: COLORS.ink }, line: { style: "solid", fill: COLORS.rule, width: 1 } },
      yAxis: { min: 0, max: 150, numberFormatCode: "$0\"K\"", majorGridlines: { style: "solid", fill: COLORS.rule, width: 1 }, textStyle: { fontSize: 14, fill: COLORS.muted } },
      dataLabels: { showValue: true, position: "outEnd", textStyle: { fontSize: 14, fill: COLORS.ink, bold: true } },
      chartFill: COLORS.white,
      chartLine: { style: "solid", fill: COLORS.white, width: 0 },
      plotAreaFill: { type: "none" },
    });
    addCallout(slide, "attribution-reading", "READING", `${leaderName} ranks first under all six methods. Allocated revenue ranges from $${Math.round(summaries["REQ-04"].min_revenue / 1000)}K to $${Math.round(summaries["REQ-04"].max_revenue / 1000)}K—a ${percent(summaries["REQ-04"].spread_pct, 1)} spread versus linear.`, 870, 170, 352, 204, COLORS.green);
    addCallout(slide, "attribution-action", "ACTION", "Use the stable rank, but disclose the sensitivity band. Attribution reallocates observed revenue; it does not prove causal lift.", 870, 408, 352, 172, COLORS.blue);
    addNotes(slide, ["analytics_requests/request_04_attribution_sensitivity/result.csv", "analytics_requests/request_04_attribution_sensitivity/validation.json"]);
  }

  // 7 — Target vs actual
  {
    const slide = presentation.slides.add();
    slide.background.fill = COLORS.white;
    addTitle(slide, "Near-plan spend masks conflicting signals", 7);
    const r3 = summaries["REQ-03"];
    addText(slide, "target-context", `${r3.region} · ${r3.channel} · selected target record`, 58, 112, 700, 34, { fontSize: 23, color: COLORS.muted });
    const table = slide.tables.add({
      rows: 5,
      columns: 3,
      left: 58,
      top: 176,
      width: 710,
      height: 354,
      values: [
        ["Metric", "Attainment", "Management reading"],
        ["Spend", percent(r3.spend_attainment, 1), "Near plan / modestly over"],
        ["Attributed revenue", percent(r3.revenue_attainment, 1), "Material miss"],
        ["Leads", percent(r3.lead_attainment, 1), "Material miss"],
        ["Platform conversions", percent(r3.conversion_attainment, 1), "Definition / join conflict"],
      ],
    });
    table.styleOptions = { headerRow: true, bandedRows: true };
    table.borders.assign({ style: "solid", fill: COLORS.rule, width: 1 });
    for (let column = 0; column < 3; column += 1) table.getCell(0, column).fill = COLORS.ink;
    table.cells.block({ row: 0, column: 0, rowCount: 1, columnCount: 3 }).textStyle.color = COLORS.white;
    table.cells.block({ row: 0, column: 0, rowCount: 5, columnCount: 3 }).textStyle.fontSize = 18;
    table.cells.block({ row: 1, column: 1, rowCount: 4, columnCount: 1 }).textStyle.bold = true;
    table.getCell(2, 1).fill = "#FCE8E8";
    table.getCell(3, 1).fill = "#FCE8E8";
    table.getCell(4, 1).fill = "#FFF0DF";
    addCallout(slide, "target-so", "SO WHAT", "Revenue and lead attainment are extremely low, while platform conversions exceed target by more than ten times. The signals do not support one clean performance story.", 816, 176, 406, 190, COLORS.orange);
    addCallout(slide, "target-action", "ACTION", "Keep the recommendation on hold. Reconcile conversion definitions, joins, and target grain; then rerun the review.", 816, 400, 406, 160, COLORS.blue);
    addNotes(slide, ["analytics_requests/request_03_target_miss/result.csv", "analytics_requests/request_03_target_miss/validation.json"], "The analysis preserves one target-record grain and does not sum duplicated actuals across target dimensions.");
  }

  // 8 — Budget scenarios
  {
    const slide = presentation.slides.add();
    slide.background.fill = COLORS.white;
    addTitle(slide, "All simulated cases stay below 1.0x ROAS", 8);
    slide.charts.add("bar", {
      position: { left: 58, top: 150, width: 760, height: 430 },
      categories: scenarioRows.map((row) => row.scenario_name),
      series: [{
        name: "Projected ROAS",
        values: scenarioRows.map((row) => Number(row.projected_roas)),
        fill: COLORS.blue,
        dataLabelOverrides: scenarioRows.map((row, idx) => ({ idx, text: `${Number(row.projected_roas).toFixed(2)}x`, position: "outEnd", showValue: false, textStyle: { fontSize: 14, fill: COLORS.ink, bold: true } })),
      }],
      hasLegend: false,
      barOptions: { direction: "column", grouping: "clustered", gapWidth: 55 },
      xAxis: { textStyle: { fontSize: 15, fill: COLORS.ink }, line: { style: "solid", fill: COLORS.rule, width: 1 } },
      yAxis: { min: 0, max: 1, majorUnit: 0.2, numberFormatCode: "0.0x", majorGridlines: { style: "solid", fill: COLORS.rule, width: 1 }, textStyle: { fontSize: 14, fill: COLORS.muted } },
      dataLabels: { showValue: true, position: "outEnd", textStyle: { fontSize: 14, fill: COLORS.ink, bold: true } },
      chartFill: COLORS.white,
      chartLine: { style: "solid", fill: COLORS.white, width: 0 },
      plotAreaFill: { type: "none" },
    });
    addCallout(slide, "scenario-what", "EXPECTED CASE", `${percent(summaries["REQ-05"].social_allocation, 1)} of budget remains in paid social; projected ROAS is ${summaries["REQ-05"].expected_roas.toFixed(2)}x and projected CAC is $${Math.round(summaries["REQ-05"].expected_cac).toLocaleString("en-US")}.`, 850, 170, 372, 190, COLORS.orange);
    addCallout(slide, "scenario-action", "ACTION", "Review concentration and funnel assumptions. This WHAT-IF is not an optimizer, forecast, causal estimate, or live-budget instruction.", 850, 394, 372, 186, COLORS.blue);
    addNotes(slide, ["analytics_requests/request_05_budget_scenario/result.csv", "analytics_requests/request_05_budget_scenario/validation.json"], "SIMULATED / WHAT-IF. No real ad account or budget is connected.");
  }

  // 9 — Data quality and reporting trust
  {
    const slide = presentation.slides.add();
    slide.background.fill = COLORS.white;
    addTitle(slide, "Source failures require a manual release hold", 9);
    const paid = qualityRows.filter((row) => ["google_ads", "facebook_ads", "tiktok_ads"].includes(row.source_system));
    slide.charts.add("bar", {
      position: { left: 58, top: 158, width: 700, height: 400 },
      categories: paid.map((row) => row.source_system.replace("_", " ")),
      series: [{
        name: "Rejected rows (%)",
        values: paid.map((row) => Number(row.rejection_rate) * 10_000),
        fill: COLORS.red,
        dataLabelOverrides: paid.map((row, idx) => ({ idx, text: `${(Number(row.rejection_rate) * 100).toFixed(1)}%`, position: "outEnd", showValue: false, textStyle: { fontSize: 15, fill: COLORS.ink, bold: true } })),
      }],
      hasLegend: false,
      barOptions: { direction: "bar", grouping: "clustered", gapWidth: 55 },
      xAxis: { min: 0, max: 100, majorUnit: 25, title: "Rejected rows (basis points)", numberFormatCode: "0", majorGridlines: { style: "solid", fill: COLORS.rule, width: 1 }, textStyle: { fontSize: 14, fill: COLORS.muted } },
      yAxis: { textStyle: { fontSize: 17, fill: COLORS.ink }, line: { style: "solid", fill: COLORS.rule, width: 1 } },
      dataLabels: { showValue: true, position: "outEnd", textStyle: { fontSize: 15, fill: COLORS.ink, bold: true } },
      chartFill: COLORS.white,
      chartLine: { style: "solid", fill: COLORS.white, width: 0 },
      plotAreaFill: { type: "none" },
    });
    addKpi(slide, "failures", String(summaries["REQ-06"].quality_failures), "paid-source error states", 804, 158, 194, COLORS.red);
    addKpi(slide, "auto-holds", String(summaries["REQ-06"].campaign_action_holds), "automatic campaign holds", 1028, 158, 194, COLORS.orange);
    addCallout(slide, "quality-action", "RELEASE DECISION", "Hold paid-media recommendations until failed source checks are resolved or accepted and monitoring is rerun.", 804, 398, 418, 160, COLORS.red);
    addNotes(slide, ["analytics_requests/request_06_data_quality_investigation/result.csv", "analytics_requests/request_06_data_quality_investigation/validation.json"], "The current action override checks campaign-ID completeness; source-level quality failures operate at a different grain and do not currently cascade automatically.");
  }

  // 10 — Actions and evidence boundaries
  {
    const slide = presentation.slides.add();
    slide.background.fill = COLORS.white;
    addTitle(slide, "Resolve trust first, then review performance", 10);
    addText(slide, "actions-sequence", "1", 70, 164, 60, 60, { fontSize: 44, bold: true, color: COLORS.red, alignment: "center" });
    addText(slide, "actions-one", "Hold paid-media actions", 150, 166, 440, 42, { fontSize: 28, bold: true });
    addText(slide, "actions-one-body", "Resolve or formally accept source-contract failures and rerun monitoring.", 150, 220, 440, 62, { fontSize: 21, color: COLORS.muted });
    addText(slide, "actions-sequence-2", "2", 70, 308, 60, 60, { fontSize: 44, bold: true, color: COLORS.orange, alignment: "center" });
    addText(slide, "actions-two", "Reconcile definitions", 150, 310, 440, 42, { fontSize: 28, bold: true });
    addText(slide, "actions-two-body", "Trace platform conversions to leads, attributed revenue, target grain, and campaign mapping.", 150, 364, 440, 72, { fontSize: 21, color: COLORS.muted });
    addText(slide, "actions-sequence-3", "3", 70, 466, 60, 60, { fontSize: 44, bold: true, color: COLORS.blue, alignment: "center" });
    addText(slide, "actions-three", "Review campaigns and funnel", 150, 468, 440, 42, { fontSize: 28, bold: true });
    addText(slide, "actions-three-body", "Prioritize portfolio-wide campaign diagnostics and paid-social lead qualification.", 150, 522, 440, 72, { fontSize: 21, color: COLORS.muted });
    addBox(slide, "boundary-panel", 656, 146, 566, 444, COLORS.panel, COLORS.panel);
    addText(slide, "boundary-title", "Evidence boundaries", 692, 178, 480, 42, { fontSize: 30, bold: true });
    addText(slide, "boundary-body", "• Generated/synthetic marketing business data\n\n• Bounded real portfolio-site GA4 remains separate and unused here\n\n• Attribution is allocation—not causal lift\n\n• Budget outputs are SIMULATED / WHAT-IF\n\n• No real approval, ad execution, realized impact, Power BI Service deployment, or production SLA", 692, 248, 470, 306, { fontSize: 20, color: COLORS.ink });
    addNotes(slide, ["analytics_requests/README.md", "business_analysis/stakeholder_requests/decision_log.csv", "docs/project_scope_boundaries.md"]);
  }

  await fs.mkdir(RENDER_DIR, { recursive: true });
  for (const [index, slide] of presentation.slides.items.entries()) {
    const preview = await presentation.export({ slide, format: "png", scale: 1 });
    await fs.writeFile(path.join(RENDER_DIR, `slide-${String(index + 1).padStart(2, "0")}.png`), new Uint8Array(await preview.arrayBuffer()));
    const layout = await slide.export({ format: "layout" });
    await fs.writeFile(path.join(RENDER_DIR, `slide-${String(index + 1).padStart(2, "0")}.layout.json`), await layout.text());
  }
  const montage = await presentation.export({ format: "webp", montage: true, scale: 1 });
  await fs.writeFile(path.join(RENDER_DIR, "deck-montage.webp"), new Uint8Array(await montage.arrayBuffer()));
  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(FINAL_PPTX);
  await fs.rm(`${FINAL_PPTX}.inspect.ndjson`, { force: true });
  const inspect = await presentation.inspect({ kind: "slide,textbox,shape,chart,table,notes", maxChars: 24000 });
  await fs.writeFile(path.join(RENDER_DIR, "deck-inspect.ndjson"), inspect.ndjson);
  console.log(JSON.stringify({ output: FINAL_PPTX, slides: presentation.slides.items.length, renders: RENDER_DIR }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
