-- Quarantine pattern example.
-- The idea is to preserve bad records for analysis without polluting trusted outputs.

CREATE OR REPLACE TEMP VIEW orders_with_quarantine AS
SELECT
  *,
  CASE
    WHEN order_id IS NULL THEN true
    WHEN amount < 0 THEN true
    ELSE false
  END AS is_quarantined
FROM main.bronze.orders_raw;

CREATE OR REPLACE TABLE main.silver.orders_valid AS
SELECT * FROM orders_with_quarantine WHERE is_quarantined = false;

CREATE OR REPLACE TABLE main.observability.orders_quarantine AS
SELECT * FROM orders_with_quarantine WHERE is_quarantined = true;
