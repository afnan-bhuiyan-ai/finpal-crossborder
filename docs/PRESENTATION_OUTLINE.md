# FinPal CrossBorder - 9 minute 30 second presentation outline

International Track · Topic C · AI as a Financial Participant

Use this as an eight-slide deck script. All on-screen quotes and examples must retain a visible MOCK label. Budget includes live interaction; stop at 9:30, leaving 30 seconds under the ten-minute maximum. No PPTX or demo video is included because the requested deliverable is an outline.

| Slide | Time | Visual and key message |
|---|---|---|
| 1. One student, two currencies | 0:00-0:45 | Synthetic student: family support and part-time wages; USD tuition, BDT home wallet. Turn confusing costs into a checkable plan. |
| 2. The cost you cannot see in a headline fee | 0:45-2:00 | Open comparison chart, USD 800 to BDT. CampusBridge: MOCK BDT 96,772.11. ZeroFee Mirage: MOCK BDT 93,696 despite no explicit fee. Show fee + effective rate arithmetic. |
| 3. Tuition needs a funding plan and a deadline | 2:00-3:15 | Ask S3. Existing MOCK USD 22,602 covers USD 6,000 before other obligations. A verified USD channel avoids conversion; bank/payment fees are unknown. Show three BDT alternatives, the shortfall and separate reserve. |
| 4. Balances, fees and newcomer habits | 3:15-4:15 | Currency dashboard converts the spending chart to one BDT axis. Point to USD 84 in three months of card FX fees. Ask for credit plan: rent USD 700/month, bills USD 90; low utilisation and timely payment, with no score promise. |
| 5. Safe participation is visible | 4:15-6:15 | Show transaction injection quarantine; send-money denial; reporting-evasion refusal. Ask compliance check: three near-threshold transfers and rapid activity are review signals, not proof. Threshold is fictional, never a legal rule. |
| 6. An agent that asks before changing state | 6:15-7:15 | Request FX alert USD/BDT at 123. Open Agent Actions. Cancel once, request again, Confirm. Explain sandbox save, no live monitoring. View audit decision and confirmation. |
| 7. How the agent earns trust | 7:15-8:30 | Architecture: provider -> policy -> deterministic tools -> fact report. Explain alias fallback and native thought-signature replay. Report actual pytest/AppTest and eight-scenario evidence; distinguish adapter tests from live Gemini execution. |
| 8. Results, boundaries and next steps | 8:30-9:30 | Map 40/30/30 criteria to completed tasks, permission tiers, transparent interaction. Offline costs no API calls. Future work: verified providers, authenticated isolation and reviewed legal/compliance processes before any real-data pilot. |

## Presenter notes

- Opening: "A student should know what arrives, what tuition requires, and what the assistant is permitted to change."
- Slide 2 arithmetic: fee = 2 + 800 * 0.25% = USD 4; effective rate = 122 * (1 - 0.35%) = 121.573 BDT/USD; recipient = (800 - 4) * 121.573 = BDT 96,772.11 after cent rounding.
- Slide 3: StudentWire's hypothetical BDT conversion quote is BDT 733,478.94, or BDT 748,148.52 including the separate 2% reserve. Current BDT 174,000 leaves a BDT 559,478.94 funding shortfall before that reserve. Never imply the app sends funds or guarantees the university accepts a method.
- Slide 5: decline evasion without teaching workarounds. Explain legitimate source-of-funds documents. No KYC or sanctions screening is performed.
- Slide 7: use the count in `evidence/pytest_final.txt`. Included evidence is offline; Gemini adapter coverage is a local SDK test. Do not describe it as a live Gemini demonstration.
- Closing: "FinPal completes the decision workflow, makes its arithmetic visible, and leaves every state change under the student's control."

## Rehearsal checklist

Start Offline, close unrelated browser windows, enlarge the app to a readable size, keep the MOCK banner visible, and pre-open the comparison panel. Use the same fixed data as the evidence. If a chat is misrouted, use the exact sidebar prompt. Keep `evidence/scenario_log_offline.md` ready as the reproducible fallback. Check that no API key, local personal file or participant's private account appears on screen.
