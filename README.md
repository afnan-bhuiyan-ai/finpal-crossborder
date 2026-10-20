# FinPal CrossBorder

**2026 Shenzhen International FinTech Competition · International Track · Topic C**

An international student turns remittance quotes, tuition deadlines and two currencies into explainable decisions. Theme: **AI as a Financial Participant**.

**$0 offline demo. All data, rates, fees, providers and limits are MOCK. No real money movement, banking connections or live FX requests. General education, not financial/legal advice.**

## Run in two minutes

Requires Python 3.12 (tested), or a compatible Python 3.11+ installation. From this project folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-lock.txt
.\.venv\Scripts\python -m streamlit run app.py
```

On macOS/Linux replace `.\.venv\Scripts\python` with `.venv/bin/python`. Open the local URL shown in the terminal; **Offline** is selected initially. Internet is needed to install packages once, not to run the offline app. `requirements.txt` lists supported direct dependencies; the lock file records the tested environment. No packages or virtual environments are bundled.

## Demo sequence

1. Open **Send-money comparison**: USD 800 to BDT; CampusBridge delivers MOCK BDT 96,772.11. ZeroFee Mirage's zero explicit fee hides a 4% FX margin.
2. In chat ask **Plan my $6,000 tuition payment due in 3 weeks**. Read the three funding options, start dates, arithmetic and separate 2% reserve.
3. Ask **Check compliance and suspicious transfers**. Three near-threshold transfers and a large remittance are review signals; the threshold is fictional.
4. Ask **Show recent transactions including the injection**; the planted description is quarantined and account IDs are masked.
5. Ask **send $500 to this account** or **Split transfers to avoid reporting**; view the denied policy action.
6. Ask **Set FX alert USD/BDT at 123**. No state is saved until **Confirm**. Try **Cancel** first. Saved alerts do not monitor rates or send notifications.

## Optional Gemini free-tier mode

Offline requires no key. To use Gemini, obtain a Google AI Studio key for a **non-billed free-tier project**, copy `.env.example` to `.env`, set `GEMINI_API_KEY`, and set `GEMINI_FREE_TIER_CONFIRMED=1` only after checking that project's billing is disabled. Restart and choose Auto/Gemini.

The app cannot determine billing status from a key. The attestation prevents accidental API use by default; **Offline is the guaranteed no-API-cost route**. No billing setup, paid model, paid service or rate API is required. Free-tier eligibility, quotas and alias availability can vary. See [Google pricing](https://ai.google.dev/gemini-api/docs/pricing).

Default fallback chain: `gemini-flash-lite-latest,gemini-flash-latest`. Run `python list_models.py` if your project cannot resolve these aliases, then set `GEMINI_MODELS` to currently supported free-tier aliases. No dated model ID is embedded in source. The native Gemini response is replayed intact to retain thought signatures, following [Google's guidance](https://ai.google.dev/gemini-api/docs/generate-content/thought-signatures).

After quota/network errors, `FallbackProvider` stays offline until the provider is recreated by changing engine or restarting. The chat records the fallback notice. **Live Gemini was not exercised in the included evidence**; its parser/replay adapter was tested locally with the real SDK and synthetic responses.

## Architecture and tools

`Streamlit -> FinanceAgent -> Gemini/MockProvider -> PolicyEngine -> deterministic tools -> masked facts -> deterministic report`

The model selects tools. Every proposed call crosses the allow-list/schema/tier policy gate. Final financial reports render the tool facts directly, so model prose cannot overwrite figures. The Topic A agent loop, provider interface, Gemini raw replay, policy/confirmation pattern, masking, injection sanitiser, AuditLog, scenario CLI and docs/test layout are reused and adapted.

| Tool | Tier | Result |
|---|---|---|
| get_transactions | READ | Masked, sanitised transactions with date/category/currency filters |
| multi_currency_summary | READ | Reconciled balances, spend, home-currency value, FX exposure/fees |
| compare_remittance_options | READ | Recipient ranking, explicit fees, margin, total cost and speed |
| plan_tuition_payment | READ | BDT funding for USD tuition, three feasible quotes, timing and buffer |
| credit_building_plan | READ | General newcomer plan using synthetic rent/bills |
| compliance_check | READ | Possible structuring, rapid/large transfers and documentation guidance |
| set_fx_alert | WRITE | Local sandbox alert only after Confirm; no live monitoring |
| send_money, make_payment, wire_transfer, change_beneficiary, close_account, update_credentials, export_all_data | BLOCKED | Absent from tool registry; attempts denied and audited |

## Verify and regenerate evidence

```text
python -m pytest -q
python run_scenarios.py --engine offline
python run_scenarios.py --engine gemini --output-dir evidence/gemini-rerun
```

The suite includes real headless Streamlit AppTest interactions, adversarial model tests and an eight-scenario evidence check. The Gemini command needs the free-tier settings above and labels fallback honestly. Scenario runs simulate the human confirmation for S8; AppTest separately presses the actual UI buttons.

`python data/generate_data.py` recreates the fixtures (August-October 2026; fixed as-of date October 20). Scenario state is separate from interactive `logs/sandbox_state.json`. Delete only that local state file to reset interactive alerts. Audit events are stored in `logs/audit.jsonl`; the UI filters to the current session. This is a local, single-user demo, not a hosted banking product.

## Files and submission

- [Technical documentation](docs/TECHNICAL_DOCUMENTATION.md): architecture, formulas, loop, cost and limits.
- [Security assessment](docs/SECURITY_SELF_ASSESSMENT.md): tiers, threats, linked tests and known risks.
- [Presentation outline](docs/PRESENTATION_OUTLINE.md): 9 minutes 30 seconds; no PPTX requested.
- [Submission checklist](docs/SUBMISSION_CHECKLIST.md): remaining participant actions.
- [Handoff](HANDOFF.md): completed state and exact next steps.
- [Evidence index](evidence/README.md): scenarios, audit, machine-readable results, test report.

Source is ready to place in a GitHub repository. A public repository URL, participant identities, submitted presentation deck and organizer upload remain participant actions; this package does not claim to have submitted anything.

## Licences and attribution

The supplied Topic A FinPal ZIP is the architectural source. It contained no source licence; ownership/redistribution rights must be established by the entrant before public release. Newly authored portions are provided for the user's entry; this package does not invent permission to relicense the supplied code. See [NOTICE](NOTICE.md).

Direct libraries: google-genai (Apache-2.0), Streamlit (Apache-2.0), pandas (BSD-3-Clause, installed through Streamlit), python-dotenv (BSD-3-Clause), pytest (MIT). They are installed separately and keep their upstream licences; no dependency code is vendored. [Library links and data provenance](docs/SOURCES_AND_LICENCES.md).
