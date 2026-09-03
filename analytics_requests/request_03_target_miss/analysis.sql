-- REQ-03: closest-to-plan spend record with a material revenue miss.
select *
from mart.mart_target_vs_actual
where spend_attainment between 0.8 and 1.2
  and revenue_attainment < 0.5
order by revenue_attainment, abs(spend_attainment - 1)
limit 1;
