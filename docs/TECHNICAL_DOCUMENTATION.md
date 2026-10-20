# Technical documentation - FinPal CrossBorder

## Purpose and scoring

Topic C: help a synthetic BDT/USD student compare remittances, fund tuition, understand multi-currency exposure and build financial habits. Task completion (40%) is demonstrated by six read tools and one confirmed write. Security/compliance (30%) is visible in policy traces, refusals and masked audit events. Innovation/interaction (30%) combines recipient-value comparisons, tuition timing, deterministic fact rendering, offline continuity and inspectable decisions.

## Architecture

```text
 Chat / comparison form / currency dashboard
                    |
                    v
               FinanceAgent <---- Confirm / Cancel (trusted UI event)
                    |
       +------------+-------------+
       |                          |
 GeminiProvider                MockProvider
 native raw replay            intent router
 latest alias chain               ^
       +----- FallbackProvider ----+
                    |
           proposed tool call
                    v
      PolicyEngine (allow-list, schema, tiers, call limit)
        | denied       | READ          | WRITE
        v              v               v
      refusal    deterministic tools  pending validated arguments
                       |               | Confirm only
                       v               v
                synthetic CSV/JSON   local sandbox state
                       |
                 mask + sanitise
                       |
       model continuation + deterministic final fact renderer
                       |
                      UI

      Every message, policy decision, confirmation and result status -> AuditLog
```

Dashboard READ calls also pass the agent policy gate. They use fixed tool names and validated form values, bypassing the LLM only to save quota. Charts are generated from tool figures. Spending columns retain original units; the comparison chart uses recipient currency and the spending chart converts both series to BDT before comparison.

## Data model

`data/generate_data.py` deterministically creates a synthetic student profile, transactions spanning three calendar months, six directional FX pairs with 30 history points each, and five fictional providers. Every data asset declares MOCK. Positive transactions are inflows; negative transactions are outflows. Opening balances are explicit and nonzero. FX fees have their own rows and are a subset of spending; they are not subtracted twice. Each monthly USD 400 card purchase has a separate USD 28 fee (7%).

Rates are snapshot conversion factors, not live or historical transaction execution rates. The USD/BDT history rises from 119 to 122; BDT/USD is reciprocal. Other demo pairs are flat. Provider fixed fees/limits are explicitly expressed in sender currency for this simplified model. That assumption explains why the tuition ranking can differ from a USD 800 remittance ranking.

## Core algorithms

For sender budget A, fixed fee F, percentage fee p, FX margin m and mid-rate R:

```text
fee = round_half_up(F + A*p/100, 2)
effective_rate = R*(1 - m/100)
recipient = round_half_up((A-fee)*effective_rate, 2)
total_cost_sender = A - recipient/R
total_cost_percent = 100*(A-recipient/R)/A
```

Providers outside their sender limits or with fees consuming the budget are excluded. Sort descending by recipient amount, then ascending by delivery hours. All quotes include fee, margin, effective rate, total cost, speed, MOCK disclosure and arithmetic. Cost percentage is relative to sender budget; rounded displays can differ by a cent from a manually rounded intermediate calculation.

For USD tuition target T funded from BDT, invert the receive equation:

```text
BDT_budget = ceil_to_cent((T/effective_rate + F)/(1-p/100))
```

The implementation verifies the recipient after rounding the fee and increments by sender cents if needed. It filters provider limits and feasibility. Latest start = due date minus ceil(speed_hours/24) minus two calendar days for reconciliation. The cheapest three feasible options show sender cost and a separate 2% planning reserve. Existing USD funds are checked first: when they cover tuition, the plan suggests comparing the university's accepted USD funding channel, which avoids FX conversion but has unknown payment fees and timing. BDT availability and any additional funding required for the cheapest conversion are disclosed. No affordability or delivery guarantee is made. The reserve is not a quote or guarantee. Past mock trends are described, never used as a forecast; holidays, cutoff times and real university policies are outside the model. Rate lock availability is only a question to ask a provider. Legitimate tuition instalments are distinguished from prohibited reporting evasion.

Balances = opening balance + signed transaction totals, by currency. Spending excludes outgoing transfers and includes tuition and card fees. Home value = USD balance * MOCK USD/BDT + BDT balance. FX exposure = USD home value / combined home value. No investment return or historical-cost claim is made.

Compliance is a transparent heuristic: at least three USD transfers at 90%-100% of a fictional review threshold within seven days; at least three transfers in two days; and transfers/remittances of at least MOCK USD 5,000. These are review signals, not accusations or statements of law. The simplified rules do not resolve actual beneficial ownership or screen sanctions. Credit education uses the three-month average rent and bills; it promises no eligibility or credit score.

## Agent and provider lifecycle

1. Bound user input to 2,000 characters; strip control characters and mask identifiers before history/audit.
2. A new question clears a pending action. Explicit evasion and direct money movement requests receive policy refusals before any model call.
3. Provider proposes calls. Validate names, required/extra args, types, finite numbers and tool-specific bounds. At most six calls can be permitted per turn and five provider steps can run.
4. READ runs immediately. WRITE validates its values and stores a copied pending action without writing state. No `confirmed` argument exists in tool schemas.
5. Tool results are masked, description injection is quarantined, and results return as untrusted data for continuation. Gemini native messages are retained unchanged for thought-signature replay.
6. Final financial reports use deterministic tool facts; no numeric LLM explanation overrides them. No-tool numeric replies are replaced by a request to use tools.
7. Confirm rechecks policy and persists one sandbox alert by temporary-file replacement. Cancel writes nothing. A consumed confirmation cannot replay. No additional LLM call occurs.

`FallbackProvider` sticks to offline after an LLMUnavailable error and exposes a persistent notice, avoiding a half-turn silently switching back to Gemini. A new provider instance retries Gemini. API calls use a 15-second HTTP timeout and 2,048 output-token cap; quota errors have one brief retry per alias. Timeout/retry duration can still exceed one timeout over the fallback chain.

## Cost and deployment

Offline runtime uses no API and no external rates. Initial dependency downloads require internet. Gemini is opt-in: key plus non-billed-project attestation. The app cannot independently inspect billing, so a billed key is outside the supported $0 configuration. Current free-tier quotas/eligibility must be checked with Google; no paid fallback exists.

Run locally with `python -m streamlit run app.py`; bind defaults to 127.0.0.1 and usage telemetry is disabled in the supplied Streamlit configuration. Hosting publicly is outside scope because authentication, durable storage, transport security and multi-user isolation are absent.

## Validation and limitations

See [test report](../evidence/pytest_final.txt), [scenario log](../evidence/scenario_log_offline.md) and [security assessment](SECURITY_SELF_ASSESSMENT.md). Headless AppTest exercises chats, denied actions, comparison form changes, Confirm/Cancel and the no-key Gemini selector. Native Gemini raw-message replay uses real SDK objects in a no-network unit test. Live Gemini, alias access and model-selected arguments have not been tested against a real key.

Offline English keyword routing is intentionally limited; ambiguous amounts/dates or unsupported language can be misrouted. The as-of date is fixed for reproducible judging. Financial arithmetic uses Python floats with Decimal half-up cent presentation; this is a sandbox, not a financial ledger. No real rates, transfer execution, credit bureau reporting, alerts monitoring, university verification or regulated compliance service is implemented.
