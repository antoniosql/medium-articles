-- Optional local SQL example for teams that prefer inline expectation logic.
-- Use this style when the rules are simple and intentionally local.

CREATE OR REFRESH STREAMING TABLE customers_silver_sql
(
  CONSTRAINT customer_id_present EXPECT (customer_id IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT valid_email_shape EXPECT (email RLIKE '^[^@]+@[^@]+\\.[^@]+$') ON VIOLATION DROP ROW,
  CONSTRAINT country_present EXPECT (country IS NOT NULL)
)
AS
SELECT customer_id, email, country, updated_at
FROM STREAM(main.bronze.customers_raw);
