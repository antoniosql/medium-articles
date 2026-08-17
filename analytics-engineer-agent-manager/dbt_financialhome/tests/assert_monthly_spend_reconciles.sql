with source_total as (
    select round(sum(spend_eur), 2) as spend_eur
    from {{ ref('stg_transactions') }}
    where transaction_type = 'expense'
),

mart_total as (
    select round(sum(actual_spend_eur), 2) as spend_eur
    from {{ ref('fct_monthly_spend') }}
)

select
    source_total.spend_eur as source_spend_eur,
    mart_total.spend_eur as mart_spend_eur,
    abs(source_total.spend_eur - mart_total.spend_eur) as difference_eur
from source_total
cross join mart_total
where abs(source_total.spend_eur - mart_total.spend_eur) > 0.01
