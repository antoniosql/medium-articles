# Microsoft-Decision-1 in Microsoft Foundry

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Microsoft Foundry](https://img.shields.io/badge/Microsoft-Foundry-0078D4.svg)](https://ai.azure.com/catalog/models/Microsoft-Decision-1)
[![Bicep](https://img.shields.io/badge/IaC-Bicep-orange.svg)](https://learn.microsoft.com/azure/azure-resource-manager/bicep/)

Companion code for the Medium article **Your agents don't need to think so much: Microsoft-Decision-1 in Foundry**.
<!-- TODO: add the Medium link once published -->

> Most of what an agent does is not writing, it is deciding: which queue, how urgent, is this safe to send. Microsoft-Decision-1 answers those questions with typed probabilities instead of prose. This repository deploys it in Foundry and runs the article's two patterns on FraSoHome, a fictional furniture retailer.

## What this repository demonstrates

Two patterns from the Jev / System One ecosystem, ported to Foundry. Both follow one rule: **the model answers bounded questions, code owns the workflow, and the LLM is only called for the step that has to write.**

```text
Pattern 1 · ticket triage
  Customer ticket ──→ Decision-1 (choice + score + noul, one call) ──→ Routing policy (code)
                                                                        ├─→ Team queue (1 of 7)
                                                                        ├─→ Priority queue (blocked and frustrated)
                                                                        └─→ Human review (top probability < 0.6)

Pattern 2 · brand gate
  LLM drafts email ──→ Decision-1 (one noul per brand rule, one call) ──→ Send / Review / Block (code)
```

| Pattern | Ported from | FraSoHome version |
| --- | --- | --- |
| Ticket triage | TypeSafe's Jev quickstart: `department` (choice), `frustration` (score), `is_urgent` (noul) in one request | 560 support tickets routed to 7 queues; accuracy measured against the human `tipo_caso` label |
| Brand gate | pi-warden: noul checks before a coding agent runs a risky command | 11 brand rules checked on a GenAI email before it is sent; rules generated from a CSV |

## Quick start

### 1. Create a virtual environment and install

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### 2. Run everything that needs no Azure

```bash
python -m pytest -q                      # 34 tests against a local fake of the API
decision-demo audit-labels               # the label-consistency numbers quoted in the article
decision-demo triage --dry-run           # the exact triage request, without sending it
decision-demo guardrails --dry-run       # the exact guardrail request, without sending it
```

`audit-labels` reproduces the article's argument for a decision model:

```text
Tickets                   : 560
Messages repeated verbatim: 43 (152 tickets)
  conflicting tipo_caso           : 0 of 43
  conflicting prioridad           : 27 of 43
  conflicting sentimiento_inicial : 30 of 43

Worst case (16 copies): Mi nivel de fidelización no coincide con el gasto acumulado que tengo en la cuenta.
  prioridad labels: {'Alta': 3, 'Baja': 7, 'Media': 6}
```

### 3. Deploy Microsoft-Decision-1

You need an Azure subscription, the [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli) and rights to create resources and role assignments. Sign in first with `az login`.

**Option A: new resource group, Foundry resource, project and deployment (Bicep)**

```bash
# macOS / Linux
bash infra/scripts/deploy.sh
LOCATION=eastus2 DEPLOYMENT_SKU=DataZoneStandard bash infra/scripts/deploy.sh   # overrides
```

```powershell
# Windows PowerShell
./infra/scripts/deploy.ps1
./infra/scripts/deploy.ps1 -Location eastus2 -DeploymentSku DataZoneStandard
```

The script deploys [`infra/main.bicep`](infra/main.bicep), grants your user the **Cognitive Services User** role on the resource, and writes `.env` with the endpoint and deployment name. API keys are disabled; calls use Microsoft Entra ID. Role assignments can take a few minutes to propagate.

**Option B: add the deployment to an existing Foundry resource (Azure CLI, as in the article)**

```bash
ACCOUNT_NAME=my-foundry RESOURCE_GROUP=my-rg bash infra/scripts/add-deployment.sh
```

```powershell
./infra/scripts/add-deployment.ps1 -AccountName my-foundry -ResourceGroup my-rg
```

**Option C: Foundry portal.** Model catalog → Microsoft-Decision-1 → Deploy. Then copy `.env.example` to `.env` and paste the endpoint and deployment name from the deployment page.

> Pick a region where the model is offered. `GlobalStandard` is available broadly; `DataZoneStandard` keeps inference inside the data zone and is offered in selected regions. If the deployment fails on region, change `LOCATION` / `-Location`.

### 4. Smoke test: send one example and look at the raw response

```bash
decision-demo send examples/02-choice.json
```

Or without Python:

```bash
bash examples/send.sh examples/02-choice.json
```

```powershell
./examples/send.ps1 examples/02-choice.json
```

Check the response shape before you tune thresholds. The client reads `answers.<name>.choice`, `probabilities`, `score` and `noul`, and falls back to `confidence` / `probability`. If a field is named differently, it fails with a clear error instead of guessing. Add `--save` to keep the response in `outputs/`.

### 5. Pattern 1: triage FraSoHome tickets

```bash
decision-demo triage --limit 100          # 0 = all 560 tickets
```

It sends one request per ticket (8 in parallel), applies the routing policy, and prints:

- accuracy against the human `tipo_caso` label, plus a confusion table per queue;
- client-side latency p50 / p95 (includes network);
- input tokens and their cost at $0.042 per million (output tokens are free);
- how many tickets went to human review and to the priority queue.

Per-ticket decisions go to `outputs/triage_decisions.csv`, next to the human priority label, so you can see where the model and the humans disagree. The summary goes to `outputs/triage_report.json`. Tune the policy with `--min-confidence` or in [`policy.py`](src/frasohome_decision/policy.py).

### 6. Pattern 2: brand gate for a GenAI email

```bash
decision-demo guardrails
decision-demo guardrails --fail-on-block   # exit code 2 unless the verdict is SEND (CI-friendly)
```

The [sample draft](data/sample_draft.json) claims stock, says "the cheapest on the market", pushes "last chance" urgency after a return, offers 20% off without conditions, and ends with two calls to action. High-severity rules block at p ≥ 0.5; medium ones go to review at p ≥ 0.7. Edit [`brand_guardrails.csv`](data/brand_guardrails.csv) to change the rules without touching code.

### 7. Clean up

```bash
bash infra/scripts/teardown.sh            # PURGE=1 also purges the soft-deleted resource
```

```powershell
./infra/scripts/teardown.ps1              # -Purge also purges the soft-deleted resource
```

## The examples from the article

Every request in the article is a file in [`examples/`](examples/). Send any of them with `decision-demo send <file>`, `examples/send.sh` or `examples/send.ps1`. The `"<deployment-name>"` placeholder is replaced with your deployment name.

| File | Question types | What it shows |
| --- | --- | --- |
| `01-noul.json` | noul | Does a support reply promise a refund? A gate. |
| `02-choice.json` | choice | Which team handles "The API returns 500"? Routing. |
| `03-score.json` | score | How severe is "Checkout is down for all EU customers"? Ranking. |
| `04-combined.json` | choice + score + noul | Three decisions on one JSON state, one request |
| `05-frasohome-triage.json` | choice + score + noul | Pattern 1 on a FraSoHome WhatsApp ticket |
| `06-frasohome-guardrails.json` | 11 × noul | Pattern 2 on the sample email draft |

Files 01–04 come from the Microsoft Learn quickstart. Files 05–06 are generated from the code; a test fails if they drift.

## From Jev to Foundry

Microsoft-Decision-1 uses the same System One request contract as TypeSafe's Jev, so Jev patterns port with small changes:

| | Jev (TypeSafe) | Microsoft-Decision-1 (Foundry) |
| --- | --- | --- |
| Endpoint | `https://api.typesafe.ai/v1/systemone` | `<foundry-endpoint>/providers/microsoft/v1/systemone` |
| `model` field | `jev-latest` | your **deployment name** (`frasohome-decision`) |
| Auth | TypeSafe API key | Microsoft Entra ID token (recommended) or `api-key` header |
| Request body | `state`, `questions`, `type`, `instructions`, `criteria` | same |
| Question types | `choice`, `score`, `noul` | same |
| Price | $0.042 / 1M input tokens, output free | same |

## Repository map

```text
.
├── infra/
│   ├── main.bicep                 # Foundry resource + project + Decision-1 deployment + role
│   ├── main.bicepparam            # default parameters
│   └── scripts/
│       ├── deploy.sh / .ps1       # new environment, writes .env
│       ├── add-deployment.sh/.ps1 # existing Foundry resource (Azure CLI path from the article)
│       └── teardown.sh / .ps1     # delete (and optionally purge)
├── examples/                      # every request in the article + raw-HTTP senders
├── data/                          # FraSoHome synthetic tickets, brand rules, sample draft
├── src/frasohome_decision/
│   ├── client.py                  # stdlib HTTP client, Entra ID or key, retries on 429/5xx
│   ├── questions.py               # triage and guardrail questions
│   ├── policy.py                  # routing and gate policies: thresholds live here
│   ├── triage.py                  # Pattern 1 evaluation: accuracy, latency, cost
│   ├── audit.py                   # offline label-consistency audit
│   └── cli.py                     # decision-demo command
├── tests/                         # offline tests against a local fake of the API
└── outputs/                       # generated reports (git-ignored)
```

## Configuration

| Variable | Required | Meaning |
| --- | --- | --- |
| `AZURE_ENDPOINT` | yes | Foundry resource endpoint, e.g. `https://<name>.services.ai.azure.com` |
| `DEPLOYMENT_NAME` | yes | The deployment name sent in the `model` field |
| `AZURE_API_KEY` | no | Use an API key instead of Entra ID (only if the resource allows keys) |

Values come from the environment or from `.env` (`--env-file` to choose another file). Without `AZURE_API_KEY`, the client uses `DefaultAzureCredential`, so `az login`, a managed identity or environment credentials all work.

## Limits worth stating

- **It chooses well inside your options, not outside them.** A schema-valid answer can still be the wrong queue. Add an abstention option when a forced choice would be worse than none.
- **Wording moves the scores.** Keep `criteria` text under version control and test with shuffled option order.
- **No explanation comes back.** Log the state, the questions and the probabilities; that triple is your audit trail.
- **Not for decisions about people on its own.** Credit, employment, housing or health decisions need meaningful human review.
- **The fake API in `tests/` checks plumbing, not quality.** Accuracy numbers only mean something from a run against a real deployment.

## References

- [Introducing Microsoft-Decision-1, our model for fast decision-making](https://commandline.microsoft.com/microsoft-decision-1-model-foundry/) — Microsoft Command Line
- [Deploy and use Microsoft-Decision-1 in Microsoft Foundry](https://learn.microsoft.com/en-us/azure/foundry/foundry-models/how-to/use-foundry-models-microsoft-decision) — Microsoft Learn
- [Microsoft-Decision-1 in the Foundry model catalog](https://ai.azure.com/catalog/models/Microsoft-Decision-1)
- [What Is Jev? Inside TypeSafe's Decision-Only AI Model](https://www.firecrawl.dev/blog/what-is-jev) — TypeSafe quickstart and pi-warden guardrail
- [Building a harness with Jev](https://www.langchain.com/blog/building-a-harness-with-jev) — LangChain

## License

[MIT](LICENSE)
