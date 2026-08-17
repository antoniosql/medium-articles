# Security policy

This repository contains synthetic data only and must not be configured with production credentials.

## Do not

- commit API keys, database passwords, or cloud credentials;
- point the example profile at a production database;
- grant the optional LLM planner write access outside an isolated development branch;
- treat this reference implementation as a substitute for a security review.

For a production implementation, use isolated execution, least-privilege identities, short-lived credentials, network controls, branch protection, signed artifacts, immutable audit logs, and explicit approval for deployment.
