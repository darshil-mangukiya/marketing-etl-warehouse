# Power BI Usability and Accessibility Review

Review basis: the seven-page PBIX screenshot evidence plus source-controlled specifications for the GA4 Funnel, Variance Drivers, Campaign Action Center, and Scenario Planning pages.

| Area | Finding | Phase 2 treatment | Runtime status |
|---|---|---|---|
| Navigation | Seven original pages are evidenced; newer analytical pages require Desktop assembly. | Page names follow decision sequence: overview, performance, drivers, funnel, attribution, targets, actions, scenarios, governance. | PBIX original pages verified; additions Power BI-ready |
| Titles | Business questions are present in page specifications. | Keep question-led titles and show reporting period in subtitles. | Specification validated |
| Filters | Date/channel/region terms were not uniform across every source. | Each page now declares a compact filter contract; unsupported dimensions are not implied. | Specification validated |
| Visual clutter | Detailed evidence can overwhelm executive pages. | Keep KPI cards and exception summaries on overview; route record-level evidence to drill-through/detail pages. | Build guidance |
| Tooltips | KPI interpretation needs definitions and quality context. | Use governed definition, formula, grain, source, and quality status from the KPI catalog. | Data assets implemented |
| Contrast | Screenshot evidence is visually legible, but automated WCAG measurement is unavailable for PBIX. | Use non-color status labels/icons, high-contrast foreground/background pairs, and avoid red/green-only meaning. | Manual Desktop check required |
| Tab order | Not inspectable from source-controlled screenshots/TMDL. | Verify left-to-right KPI, slicer, chart, detail, navigation order in Desktop. | Not executed |
| Keyboard/navigation | Button focus and alternative text require Desktop authoring. | Add meaningful alt text and consistent Back/Home buttons. | Not executed |
| Drill-through | Campaign evidence is modeled, but newer pages are not in PBIX. | Campaign ID is the drill-through key; retain visible reset/back controls. | Specification validated |
| RLS clarity | Service enforcement is not present. | Role definitions and an explicit View-as test protocol are documented. | Static tests only |

The modeled UAT package contains the remaining Desktop accessibility checks; formal certification requires the applicable organizational process.
