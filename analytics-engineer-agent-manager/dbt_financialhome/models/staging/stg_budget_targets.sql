select
    cast(month_start as date) as month_start,
    trim(cast(canonical_category as varchar)) as canonical_category,
    cast(budget_eur as double) as budget_eur
from {{ ref('budget_targets') }}
