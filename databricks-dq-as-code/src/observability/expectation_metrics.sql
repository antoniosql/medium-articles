-- Query expectation metrics from the event log.
-- The objective is to expose passed, failed, and dropped counts in a simple view.

WITH latest_update AS (
  SELECT origin.update_id AS update_id
  FROM main.observability.vw_customers_pipeline_event_log
  WHERE event_type = 'create_update'
  ORDER BY timestamp DESC
  LIMIT 1
),
expanded AS (
  SELECT
    explode(
      from_json(
        details:flow_progress:data_quality:expectations,
        'array<struct<name:string,dataset:string,passed_records:bigint,failed_records:bigint>>'
      )
    ) AS exp,
    CAST(details:flow_progress:data_quality:dropped_records AS BIGINT) AS dropped_records
  FROM main.observability.vw_customers_pipeline_event_log
  WHERE event_type = 'flow_progress'
    AND origin.update_id = (SELECT update_id FROM latest_update)
)
SELECT
  exp.dataset,
  exp.name AS expectation_name,
  SUM(exp.passed_records) AS passed_records,
  SUM(exp.failed_records) AS failed_records,
  SUM(COALESCE(dropped_records, 0)) AS dropped_records
FROM expanded
GROUP BY exp.dataset, exp.name
ORDER BY exp.dataset, exp.name;
