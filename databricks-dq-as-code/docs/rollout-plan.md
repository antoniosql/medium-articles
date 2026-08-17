# Rollout Plan

## Phase 1 - Foundation
- Create catalog structure
- Create the quality rules table
- Seed a small reusable rule set

## Phase 2 - First pipeline
- Implement one Bronze-to-Silver pipeline
- Apply reusable `warn` and `drop` rules
- Publish the event log

## Phase 3 - Trusted outputs
- Implement one Silver-to-Gold pipeline
- Apply reusable `fail` rules
- Connect metrics to monitoring

## Phase 4 - Scale
- Add more domains
- Add quarantine patterns
- Add lineage-based impact triage
