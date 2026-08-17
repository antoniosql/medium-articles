select
    transaction_id,
    transaction_date,
    raw_category,
    spend_eur
from {{ ref('int_transactions_enriched') }}
where transaction_type = 'expense'
  and canonical_category is null
