select
    cast(account_id as varchar) as account_id,
    cast(account_name as varchar) as account_name,
    cast(account_type as varchar) as account_type,
    cast(active_flag as boolean) as active_flag
from {{ ref('raw_accounts') }}
