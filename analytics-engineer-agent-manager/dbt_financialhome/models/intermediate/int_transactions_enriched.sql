with transactions as (
    select * from {{ ref('stg_transactions') }}
),

category_mapping as (
    select * from {{ ref('stg_category_mapping') }}
),

accounts as (
    select * from {{ ref('stg_accounts') }}
)

select
    t.transaction_id,
    t.transaction_date,
    date_trunc('month', t.transaction_date)::date as month_start,
    t.account_id,
    a.account_name,
    a.account_type,
    t.merchant,
    t.raw_category,
    m.canonical_category,
    m.essential_flag,
    m.category_owner,
    t.amount_eur,
    t.transaction_type,
    t.spend_eur
from transactions as t
left join category_mapping as m
    on lower(t.raw_category) = lower(m.raw_category)
left join accounts as a
    on t.account_id = a.account_id
