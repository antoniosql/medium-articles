# Methodology

## Core operating model

The calculator treats an AI agent as an operating workflow, not merely as a sequence of model calls.

### Successful outcomes

```text
Successful outcomes
=
Monthly tasks × end-to-end success rate
```

A successful outcome must represent a correctly completed business task. Returning an answer, producing a tool call, or ending a run without an exception is not sufficient.

### Human effort

The model includes four human-effort categories:

1. assistance for successful tasks that are not autonomous;
2. quality sampling of autonomous outcomes;
3. rework after the initial result;
4. manual fallback for failed tasks.

```text
Human labor cost
=
Total human hours × loaded hourly cost
```

### Technology cost

```text
Variable technology cost
=
Inference cost
+ Tool and API cost
+ Telemetry and evaluation cost
```

```text
Fixed technology cost
=
Platform cost
+ Operations and maintenance
+ Amortized development and change cost
```

### Failure impact

```text
Failure impact
=
Failed tasks × business impact per failed task
```

This input represents the operational consequence beyond fallback labor.

### Total monthly cost

```text
Total monthly cost
=
Human labor cost
+ Variable technology cost
+ Fixed technology cost
+ Failure impact
```

### Cost per successful outcome

```text
Cost per successful outcome
=
Total monthly cost ÷ successful outcomes
```

This is the primary unit-economics measure.

### Value and ROI

```text
Value created
=
Successful outcomes × business value per successful outcome
```

```text
Net monthly value
=
Value created − total monthly cost
```

```text
ROI
=
Net monthly value ÷ total monthly cost
```

## Default decision thresholds

- `SCALE`: ROI is at least 50%.
- `OPTIMIZE`: ROI is non-negative but below 50%.
- `RETIRE`: ROI is negative.

These are discussion thresholds, not universal investment rules. Adjust the interpretation for risk, strategic value, adoption stage, and capital constraints.

## Scenario logic

### Token Saver

Uses inexpensive inference but has lower completion, more rework, and more manual fallback.

### High Accuracy, Heavy Review

Achieves better completion but requires extensive review and expert involvement.

### Outcome Optimized

Balances model cost, task success, autonomy, targeted QA, and controlled failure exposure.

## Measurement recommendations

- Use representative production tasks.
- Fix the success definition before comparing versions.
- Capture retries and tool calls from traces.
- Measure review and fallback time from work logs or observation.
- Segment high-risk tasks rather than relying only on averages.
- Treat reported time savings as value only when the organization can realize them.

## Sources

- Microsoft: Introducing ROI for agents in Foundry  
  https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/introducing-roi-for-agents-in-foundry/4531970
- Microsoft Learn: Observability in Generative AI  
  https://learn.microsoft.com/en-us/azure/foundry/concepts/observability
- Microsoft Learn: Agent Monitoring Dashboard  
  https://learn.microsoft.com/en-us/azure/foundry/observability/how-to/how-to-monitor-agents-dashboard
- Databricks: Use agents on Databricks  
  https://docs.databricks.com/aws/en/agents/custom-agents/build-agents
- Databricks: MLflow 3 for GenAI  
  https://docs.databricks.com/aws/en/mlflow3/genai/
- Research paper: The Real Barrier to LLM Agent Usability is Agentic ROI  
  https://arxiv.org/abs/2505.17767
