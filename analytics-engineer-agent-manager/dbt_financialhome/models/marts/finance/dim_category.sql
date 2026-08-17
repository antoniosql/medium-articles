select distinct
    canonical_category,
    essential_flag,
    category_owner
from {{ ref('stg_category_mapping') }}
where canonical_category not in ('Income', 'Transfer')
