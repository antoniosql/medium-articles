with actuals as (
    select
        month_start,
        canonical_category,
        round(sum(spend_eur), 2) as actual_spend_eur,
        count(*) as expense_transaction_count
    from {{ ref('int_transactions_enriched') }}
    where transaction_type = 'expense'
    group by 1, 2
),

budgets as (
    select
        month_start,
        canonical_category,
        budget_eur
    from {{ ref('stg_budget_targets') }}
),

combined as (
    select
        coalesce(a.month_start, b.month_start) as month_start,
        coalesce(a.canonical_category, b.canonical_category) as canonical_category,
        coalesce(a.actual_spend_eur, 0.0) as actual_spend_eur,
        coalesce(b.budget_eur, 0.0) as budget_eur,
        coalesce(a.expense_transaction_count, 0) as expense_transaction_count
    from actuals as a
    full outer join budgets as b
        on a.month_start = b.month_start
       and a.canonical_category = b.canonical_category
)

select
    month_start,
    canonical_category,
    actual_spend_eur,
    budget_eur,
    round(actual_spend_eur - budget_eur, 2) as variance_eur,
    case
        when budget_eur = 0 then null
        else round(((actual_spend_eur - budget_eur) / budget_eur) * 100, 2)
    end as variance_pct,
    expense_transaction_count,
    case
        when budget_eur = 0 and actual_spend_eur > 0 then 'no_budget'
        when actual_spend_eur > budget_eur then 'over_budget'
        else 'within_budget'
    end as budget_status
from combined
