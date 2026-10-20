# Security self-assessment - FinPal CrossBorder

Scope: a local single-user synthetic demonstration. This is a self-assessment, not certification, a penetration-test report or a legal opinion.

## Permission tiers and trust boundaries

| Tier | Tools | Enforcement |
|---|---|---|
| READ | get_transactions, multi_currency_summary, compare_remittance_options, plan_tuition_payment, credit_building_plan, compliance_check | Allow-list + schema + finite-number/type checks + tool bounds; no state writes |
| WRITE | set_fx_alert | Validated pending arguments, visible Confirm/Cancel, policy recheck at execution; no model-accessible confirmation parameter |
| BLOCKED | send_money, make_payment, wire_transfer, change_beneficiary, close_account, update_credentials, export_all_data and legacy movement/credential actions | Not registered or advertised to Gemini; any attempted call denied and logged |

Unknown tools, missing required arguments, extra properties (including `confirmed`), wrong types, NaN/infinity and excess call budgets are rejected. Business bounds and supported-pair checks run before an FX alert becomes pending. The model cannot press UI buttons. Only trusted application code calls `confirm_pending(True)`; the scenario runner explicitly simulates that human event and AppTest exercises actual buttons.

## Threats, controls and evidence

| Threat | Control | Evidence |
|---|---|---|
| Hidden transaction instructions | Entire suspicious description quarantined, not partly redacted; tool data marked untrusted | [test_full_injection_quarantine](../tests/test_security.py), [transaction test](../tests/test_tools.py), [S5](../evidence/scenario_log_offline.md#s5---pass) |
| Model requests money movement | Absent executable tool; PolicyEngine denies; direct command refused before model call | [test_blocked_tools_absent_and_denied](../tests/test_security.py), [adversarial model](../tests/test_agent.py), [S6](../evidence/scenario_log_offline.md#s6---pass) |
| Reporting/KYC/sanctions evasion | Intent guard refuses common evasion requests before calling model; no payment capabilities | [test_evasion_refused_before_model](../tests/test_agent.py), [S7](../evidence/scenario_log_offline.md#s7---pass) |
| Unauthorised sandbox write | Explicit Confirm, no pre-confirm write, Cancel, single-use pending action | [test_confirm_cancel_replay](../tests/test_agent.py), [UI buttons](../tests/test_app.py), [S8](../evidence/scenario_log_offline.md#s8---pass) |
| Stale or changed approval | New question/engine change invalidates pending action; returned pending copy cannot mutate server arguments | [test_new_question_invalidates_stale_write](../tests/test_agent.py), [test_reply_cannot_mutate_pending](../tests/test_agent.py) |
| Identifier/secret leakage | Account fields last-four only; long/separated digit strings, email local part and common secret formats masked; sensitive dict keys redacted | [test_masking_before_provider_and_audit](../tests/test_security.py), [provider spy](../tests/test_agent.py) |
| Hallucinated financial figures | Tools compute; deterministic final report replaces provider prose for financial results | [test_hallucinated_figures_replaced_by_tool_facts](../tests/test_agent.py), [math tests](../tests/test_tools.py) |
| Malformed inputs/resource use | Schema/type/length limits, tool bounds, max six permitted calls/five model steps, output cap and API timeout | [test_schema_and_call_budget](../tests/test_security.py), [invalid inputs](../tests/test_tools.py), [bounded model](../tests/test_agent.py) |
| Misleading free-tier operation | No-key offline default, explicit non-billed-project attestation, no paid provider, disclosed sticky fallback | [test_billing_opt_in_required](../tests/test_agent.py), [test_fallback_sticky_and_disclosed](../tests/test_agent.py) |
| Missing auditability | Masked UTC JSONL events for messages, calls, policy decisions, confirmations and result status; current session UI filter | [audit test](../tests/test_security.py), [offline audit](../evidence/audit_offline.jsonl) |
| Hidden FX charges / false compliance conclusion | Fee/margin/effective-rate arithmetic and MOCK labels; review signals, no legal threshold claims | [ranking/compliance tests](../tests/test_tools.py), [S2/S3 and supplement](../evidence/scenario_log_offline.md) |
| Lost Gemini thought signatures | Retain and replay original model Content object and function response ordering | [test_gemini_raw_signature_replay_without_network](../tests/test_agent.py) |

## Compliance posture

The assistant refuses assistance to evade reporting, KYC, sanctions or transfer limits. It asks for legitimate source-of-funds evidence such as family support letters, payroll records and tuition invoices. It does not submit reports, verify identities, perform screening, define actual regulatory thresholds or accuse users of wrongdoing. All detected patterns are synthetic and explainable.

Every financial reply and the interface disclose MOCK data and the educational scope. General credit guidance is not tailored to a country's laws or underwriting rules. No investment, tax, legal or regulated payment service is offered. No raw bank data or keys are included in this package. Only synthetic prompts should be sent to Gemini; the provider's current data-use terms still apply.

## Known risks and residual limitations

1. Regex injection/intent/masking filters are incomplete. Obfuscation, other languages and unusual identifier formats can evade them. Safety ultimately depends on the absent dangerous tools and human write gate; this is not an exhaustive prompt-injection defence.
2. LLM planning can select wrong tools/arguments. Deterministic facts remain correct for the chosen inputs, which may not match the user's intent. Non-numeric free-form no-tool text is not fact-verified.
3. Local Python functions and files are trusted. A local user can bypass the app, call a write function, alter fixtures/state/audit, or replace code. No protection against a hostile local operator is claimed.
4. No login, encryption at rest, multi-user state isolation or production access controls. Audit UI is session-filtered, but its local file and sandbox state are shared by the process. Concurrent state writes can race despite atomic replacement. Do not expose publicly.
5. JSONL is append-by-application, not tamper-evident, signed, remote or an immutable record. Result statuses and truncated messages are audited; full numeric scenario results are separately stored in evidence. No non-repudiation claim is made.
6. Pending actions have no wall-clock expiry, but new questions, engine changes and session restarts invalidate them. Confirmation binds the currently displayed session action; this is not a banking-grade transaction authorization protocol.
7. Compliance rules can produce false positives and false negatives. Transfers are not grouped by real verified beneficiary identity; no sanctions lists, legal thresholds or jurisdiction-specific obligations are modeled.
8. Snapshot rates, currency-dependent fictional fixed fees, cent rounding, calendar-day speeds and a 2% reserve simplify reality. Neither timing nor delivery/affordability is guaranteed; tuition instalment/lock availability is not verified.
9. Free-tier status cannot be inferred from an API key. Operator attestation is necessary; choose Offline for guaranteed no API charges. The SDK adapter is tested without a network, but actual Gemini aliases, quota and responses remain unverified.
10. The offline engine is an English keyword router, not general language understanding. Fixtures and as-of dates are fixed. Audit/history grow during long sessions; no cross-session request rate limiter or log rotation is implemented.
11. The dependency lock captures a tested environment, not a vulnerability audit. Confirm licences of the supplied Topic A source before a public release. The package contains no credentials or original uploaded attachments.

## Next hardening steps

Before any real-data pilot: jurisdiction-specific review, authenticated per-user storage, transaction-bound expiring approvals, secret management, durable tamper-evident audit, concurrency control, data minimisation, dependency scanning, structured model-output controls and adversarial multilingual evaluation. These are future requirements, not completed features.
