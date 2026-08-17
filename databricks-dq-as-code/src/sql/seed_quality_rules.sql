-- Seed data for the example pipelines.
-- In a real project, manage this through CI/CD or migration scripts.

INSERT INTO main.governance.quality_rules
(rule_name, tag, action, constraint_sql, active, severity, domain, owner, description, created_at, updated_at)
VALUES
('customer_id_present_warn', 'customers_silver_warn', 'warn', 'customer_id IS NOT NULL', true, 'medium', 'customers', 'data-platform', 'Warn when customer_id is null', current_timestamp(), current_timestamp()),
('country_present_warn', 'customers_silver_warn', 'warn', 'country IS NOT NULL', true, 'low', 'customers', 'data-platform', 'Warn when country is null', current_timestamp(), current_timestamp()),
('valid_email_shape_drop', 'customers_silver_drop', 'drop', "email RLIKE '^[^@]+@[^@]+\\.[^@]+$'", true, 'medium', 'customers', 'data-platform', 'Drop records with invalid email format', current_timestamp(), current_timestamp()),
('customer_id_present_fail', 'customers_gold_fail', 'fail', 'customer_id IS NOT NULL', true, 'high', 'customers', 'data-product-owner', 'Gold table contract requires customer_id', current_timestamp(), current_timestamp()),
('amount_non_negative_fail', 'orders_silver_drop', 'drop', 'amount >= 0', true, 'high', 'orders', 'finance-domain', 'Drop rows with negative amounts', current_timestamp(), current_timestamp());
