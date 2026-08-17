select
    month_start,
    canonical_category,
    count(*) as row_count
from {{ ref('fct_monthly_spend') }}
group by 1, 2
having count(*) > 1
