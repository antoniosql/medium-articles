select
    month_start,
    canonical_category,
    actual_spend_eur
from {{ ref('fct_monthly_spend') }}
where actual_spend_eur < 0
