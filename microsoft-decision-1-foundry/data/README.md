# Data

Synthetic data from **FraSoHome**, a fictional omnichannel home-furniture and decor retailer used across my demos. No real customers. Text fields are in Spanish, as they would be in production; the questions sent to the model are in English.

| File | Rows | Used by |
| --- | --- | --- |
| `support_tickets.csv` | 560 | Pattern 1 (triage) and `audit-labels` |
| `brand_guardrails.csv` | 12 | Pattern 2 (brand gate) |
| `sample_draft.json` | 1 | Pattern 2: a GenAI email draft that breaks several rules on purpose |

## support_tickets.csv

| Column | Meaning |
| --- | --- |
| `service_ticket_id` | Ticket id (`SRV-000266`) |
| `canal_soporte` | Channel: Chat, WhatsApp, Email, Teléfono, Tienda |
| `tipo_caso` | Human-assigned queue. **Ground truth** for accuracy: `devolucion`, `info_producto`, `entrega`, `defecto`, `stock_tienda`, `cupon`, `fidelizacion` |
| `prioridad` | Human-assigned priority (Alta / Media / Baja). Inconsistent on purpose, see `decision-demo audit-labels` |
| `sentimiento_inicial` | Human-assigned sentiment. Also inconsistent |
| `texto_cliente` | The customer's message: the `state` sent to the model |
| other columns | Dates, order, store, agent, SLA, CSAT, compensation, resolution text. Not used by the demo |

## brand_guardrails.csv

| Column | Meaning |
| --- | --- |
| `regla_id` | Rule id, used as the question name (`GR-002`) |
| `categoria_regla` | Category: tone, promise, price, privacy, urgency… |
| `descripcion_regla` | The rule text, inserted into the question's instructions |
| `aplica_a_canal` | `all` or a comma-separated list of channels |
| `severidad` | `alta` blocks at p ≥ 0.5, `media` goes to review at p ≥ 0.7 |
