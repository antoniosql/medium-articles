# Operating Model

## Ownership

- **Platform team** owns the framework, deployment standards, and observability patterns.
- **Domain team** owns the business meaning of quality rules.
- **Data product owner** approves contract severity for Gold datasets.

## Rule lifecycle

1. Propose a rule
2. Review business intent
3. Define SQL constraint
4. Assign action: warn, drop, or fail
5. Activate the rule in the shared rules table
6. Monitor rule behavior in the event log
7. Adjust severity only with review
