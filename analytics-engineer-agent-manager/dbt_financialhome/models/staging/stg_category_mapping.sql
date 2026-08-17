select
    trim(cast(raw_category as varchar)) as raw_category,
    trim(cast(canonical_category as varchar)) as canonical_category,
    cast(essential_flag as boolean) as essential_flag,
    trim(cast(category_owner as varchar)) as category_owner
from {{ ref('category_mapping') }}
