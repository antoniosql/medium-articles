{% set failure_scenario = var('failure_scenario', 'none') %}

with source as (
    {% if failure_scenario == 'unmapped_category' %}
        select * from {{ ref('raw_transactions_unmapped') }}
    {% else %}
        select * from {{ ref('raw_transactions') }}
    {% endif %}
)

select
    cast(transaction_id as varchar) as transaction_id,
    cast(transaction_date as date) as transaction_date,
    cast(account_id as varchar) as account_id,
    trim(cast(merchant as varchar)) as merchant,
    trim(cast(raw_category as varchar)) as raw_category,
    cast(amount_eur as double) as amount_eur,
    lower(trim(cast(transaction_type as varchar))) as transaction_type,
    case
        when lower(trim(cast(transaction_type as varchar))) = 'expense'
            then abs(cast(amount_eur as double))
        else 0.0
    end as spend_eur
from source
