-- Example lineage queries to support impact analysis.
-- Adjust filters to your catalog, schema, and data product names.

SELECT *
FROM system.access.table_lineage
WHERE target_table_full_name = 'main.gold.customers_gold';

SELECT *
FROM system.access.column_lineage
WHERE target_table_full_name = 'main.gold.customers_gold';
