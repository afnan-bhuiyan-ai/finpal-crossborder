# Handoff - FinPal CrossBorder

**Status:** Topic C implementation complete; final verification recorded in `evidence/pytest_final.txt`. Complete offline scenario logs and machine-readable results included. Read README first.

**Deadline:** 20 October 2026, 23:59 Beijing / 21:59 Bangladesh. No organizer upload or GitHub publication has been performed.

## What is built

- Python/Streamlit app with chat, engine selector, recipient-value comparison chart, BDT-normalised spending chart, Agent Actions, audit and Confirm/Cancel.
- Six deterministic READ tools; confirmed sandbox FX-alert WRITE; no executable payments, wires, beneficiary/credential changes, account closure or unrestricted export.
- Three months of synthetic BDT/USD transactions; six MOCK pairs with 30-day histories; five fictional providers; hidden margin, high card fee, structuring/rapid/large transfer patterns and a quarantined injection.
- Original Topic A loop/provider/policy/audit architecture adapted, including Gemini native raw-message replay and latest-alias fallback chain.
- Deterministic fact reports prevent the model from substituting financial figures. Tuition highlights existing USD coverage and BDT shortfall.
- Security/technical docs, sources/licences notice, timed presentation outline, submission checklist, test results, eight scenarios plus compliance supplement.

## Continue on another machine/account

1. Extract the ZIP and open its `finpal-crossborder` folder.
2. Install Python 3.12 if needed; create `.venv`, install `requirements-lock.txt`, run Streamlit using README commands. Offline requires no key or network after installation.
3. Run `python -m pytest -q` and `python run_scenarios.py --engine offline` in that environment. All app tests isolate local state.
4. Optionally copy `.env.example` to `.env`, use a non-billed Google AI Studio project, set the key and `GEMINI_FREE_TIER_CONFIRMED=1`, restart and choose Gemini. Live Gemini has **not** been tested here. Preserve actual provider/fallback labels in evidence.
5. Run `python list_models.py` if aliases are unavailable; choose currently supported free-tier aliases in `GEMINI_MODELS`. Do not copy a dated model name from old tutorials. Default chain stays `gemini-flash-lite-latest,gemini-flash-latest`.
6. Add participant/team details in the organizer's submission, establish rights/licensing for the supplied Topic A source, publish your repository and paste its actual URL. Assemble a deck from the 9:30 outline; record a brief demo if time permits. Submit before the deadline.

## State and reset

The ZIP includes one synthetic confirmed-alert evidence state at `evidence/sandbox_offline.json`; the interactive app starts with no `logs/` folder. Interactive writes create `logs/sandbox_state.json`; remove that file to reset alerts. Do not remove data fixtures. `data/generate_data.py` recreates them, retaining the fixed as-of date 2026-10-20. Scenario runs use separate state and overwrite only their own chosen evidence outputs.

No secrets, `.env`, virtual environment or real account data are packaged. This computer lacked a standalone system Python; validation used the Python bundled with Codex and an isolated virtual environment. On another machine, use a normal free Python installation or the app's bundled runtime.

## Honest boundaries

No real transfer, university integration, credit reporting, KYC, sanctions screening or live alert monitoring. Offline intent routing is limited English keyword matching. Pattern masking is incomplete; local audit/state files are editable, shared and unencrypted. The app has no production authentication or concurrent-user protection. The free-tier attestation cannot independently verify billing. Full known-risk list is in the security assessment.

The requested code, tests, evidence, documents, handoff, outline and ZIP are delivered. A presentation deck, optional video, live Gemini run, repository URL and actual competition submission remain participant actions. No unfinished implementation work is hidden behind those actions.
