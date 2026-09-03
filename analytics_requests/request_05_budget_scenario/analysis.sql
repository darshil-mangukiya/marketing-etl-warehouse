-- REQ-05: deterministic SIMULATED scenario totals from the governed export.
select
    scenario_name,
    max(simulation_status) as simulation_status,
    sum(channel_budget) as total_budget,
    sum(projected_revenue) as projected_revenue,
    sum(projected_customers) as projected_customers,
    sum(projected_revenue) / nullif(sum(channel_budget), 0) as projected_roas,
    sum(channel_budget) / nullif(sum(projected_customers), 0) as projected_cac
from read_csv_auto('analytics_requests/canonical_input/mart_budget_scenarios.csv')
group by scenario_name;
