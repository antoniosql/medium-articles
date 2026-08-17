-- Publish the pipeline event log to a managed location, then create a stable view over it.
-- This is the recommended foundation for dashboards and alerts.

CREATE OR REPLACE VIEW main.observability.vw_customers_pipeline_event_log AS
SELECT *
FROM main.observability.customers_event_log;
