-- Example inline SQL expectations for the orders domain.

CREATE OR REFRESH STREAMING TABLE orders_silver_sql
(
  CONSTRAINT order_id_present EXPECT (order_id IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT customer_id_present EXPECT (customer_id IS NOT NULL),
  CONSTRAINT amount_non_negative EXPECT (amount >= 0) ON VIOLATION FAIL UPDATE
)
AS
SELECT order_id, customer_id, amount, currency, order_ts
FROM STREAM(main.bronze.orders_raw);
