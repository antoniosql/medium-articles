-- Central table for reusable quality rules.
-- This is the simplest model that still supports ownership, activation, reuse, and lifecycle.

CREATE TABLE IF NOT EXISTS main.governance.quality_rules (
  rule_name STRING NOT NULL,
  tag STRING NOT NULL,
  action STRING NOT NULL,
  constraint_sql STRING NOT NULL,
  active BOOLEAN NOT NULL,
  severity STRING,
  domain STRING,
  owner STRING,
  description STRING,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)
USING DELTA;
