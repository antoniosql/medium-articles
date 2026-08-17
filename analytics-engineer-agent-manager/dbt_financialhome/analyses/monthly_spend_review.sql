select
    month_start,
    canonical_category,
    actual_spend_eur,
    budget_eur,
    variance_eur,
    variance_pct,
    budget_status
from {{ ref('fct_monthly_spend') }}
where actual_spend_eur > 0
order by month_start, variance_eur desc
