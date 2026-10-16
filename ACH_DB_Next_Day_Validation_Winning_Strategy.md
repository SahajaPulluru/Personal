# ACH DB Next Day Validation (C-247489): Winning Strategy

> **Caveat**: The document has no judging rubric, so scoring weights below are inferred from the acceptance criteria (AC1-AC6), the “What a Strong Solution Looks Like” FAQ, and the 5-minute demo guideline. Treat the numbers as informed estimates, not facts.

---

## 1. Hackathon Deconstruction

### Core requirements (explicit)

| # | Requirement | Source |
|---|---|---|
| 1 | Compare request (expected) vs. TNAL/GPS record (actual), output a single PASS / EXCEPTION | AC1 |
| 2 | All 5 seeded scenarios hit their predefined outcomes | AC2 |
| 3 | Per-exception output: field, expected, actual, rule, reason | AC3, FAQ 6 |
| 4 | External config (JSON/YAML/table); change a rule, rerun, behavior changes with no code change | AC4, FAQ 4 |
| 5 | Human decision: Approve or Investigate; system never auto-approves | AC5 |
| 6 | Guardrails: synthetic data, SoD, “SIMULATED” labels | AC6 |
| 7 | Run metadata: Run ID, request ID, report IDs, config version, timestamp, decision, notes | FAQ 7 |
| 8 | Clean separation: engine / config / UI | FAQ 8 |
| 9 | Deliverables: prototype + source, config file, test suite, 5-min deck, demo script, architecture doc | 4.3 |

### Hidden / implicit requirements
- **Live rule change without restart** (FAQ 4 and 10 say “live during presentation,” “without restarting”). Your engine must re-read config per run, or have hot reload.
- **SoD must be demonstrable**, not just a field in a database. The judges want to see it block someone.
- **The process flow lists 5 Core Validations** (request exists and is approved; requested vs. TNAL; all changes completed; no unauthorized changes; GPS matches ACH). The seeded scenarios cover only some of these. Mapping your engine explicitly to all 5 shows you understood the real control, not just the toy test.
- **“Stare-and-compare fatigue” is the emotional core.** The UI must make mismatches obvious in under 3 seconds.
- **Audit-readiness (“audit-ready summary”)**: this is a control, so evidence retention matters. The real flow says “Control Pass, Evidence Retained.”
- **Exceptions need a path forward** (Steps 9-11: contact maker, correct, revalidate), even though routing is out of scope. A minimal “investigate → revalidate” re-run hook makes the story complete without building ticketing.
- **Determinism.** “100% precision on seeded scenarios” means no flaky logic and no probabilistic components in the decision path.

### Judging criteria (inferred, ranked)
1. Correctness on the 5 scenarios (100% expected)
2. Explainability of exceptions
3. Live config change works
4. SoD / human-in-the-loop integrity
5. Traceability and audit summary
6. Architecture cleanliness
7. Demo clarity within 5 minutes
8. Business-value articulation

### Frequently misunderstood requirements

| Misunderstanding | Reality |
|---|---|
| “Config-driven” means a settings file with a few flags | Judges want to see a validation rule (required field, match type, tolerance, evidence requirement) change outcomes. |
| Build AI to validate | The spec wants deterministic, explainable results. AI in the decision path is a liability. |
| Auto-approve passes to save time | Explicitly prohibited. Even PASS requires a human click. |
| SoD means “log in as checker” | The check must compare the checker’s identity against the maker recorded on the change record, per transaction. |
| Integrations are impressive | Out of scope. Fake integrations must be labeled simulated. |
| Mismatch = string inequality | Real data needs normalization (case, whitespace, date formats) as a configurable rule, or you get false exceptions on the clean-match scenario. |

### What judges explicitly vs. implicitly want
- **Explicitly**: everything in the table above.
- **Implicitly**: confidence that this could become a real control tool, and a team that understands maker-checker and audit. They’re also looking for a zero-failure demo. Judges in control and ops environments are risk-averse, so a crash is fatal and polish is rewarded.

### What separates winners from average
Average teams build a diff viewer with a hardcoded rule list and a “config” file that is only partially wired up. Winners prove each acceptance criterion on screen, in order, with visible evidence.

---

## 2. Scoring Optimization Analysis

### Estimated weight distribution

| Category | Est. weight |
|---|---|
| Functional correctness (AC1, AC2) | 25% |
| Explainability (AC3) | 15% |
| Config-driven proof (AC4) | 15% |
| Human approval and SoD (AC5, AC6) | 15% |
| Traceability / audit | 8% |
| Architecture and code quality | 7% |
| Presentation and demo | 10% |
| Innovation / extras | 5% |

### Requirement scoring

| Requirement | Importance | Effort | Judge Impact | Verdict |
|---|---|---|---|---|
| Rule engine with 5 scenarios passing | 10 | 5 | 10 | Must |
| Explainable exception table (6 FAQ-6 fields) | 10 | 3 | 10 | Must |
| External YAML config, re-read per run | 10 | 3 | 10 | Must |
| Live rule edit in demo | 10 | 3 | 10 | Must |
| Approve / Investigate with notes | 9 | 2 | 8 | Must |
| SoD enforcement with visible block | 9 | 2 | 9 | Must |
| Run metadata header | 8 | 1 | 7 | Must |
| “SIMULATED” labeling | 7 | 1 | 6 | Must |
| Automated test suite (5 scenarios) | 8 | 2 | 7 | Must |
| Architecture doc (1 page) | 6 | 2 | 5 | Must |
| 5-min deck + demo script | 9 | 3 | 9 | Must |
| Map to the 5 Core Validations | 7 | 2 | 8 | Must (cheap differentiator) |
| Config schema validation and safe-reload | 6 | 2 | 8 | Nice (protects demo) |
| Config diff display + hash as version | 6 | 2 | 8 | Nice (high wow) |
| Tamper-evident audit log (hash chain) | 5 | 2 | 7 | Nice |
| Exportable audit pack (JSON/PDF) | 5 | 2 | 6 | Nice |
| Normalization rules (case/whitespace) | 6 | 2 | 6 | Nice |
| Severity levels (blocking/warning) | 5 | 2 | 6 | Nice |
| Revalidation after “Investigate” | 5 | 2 | 6 | Nice |
| LLM-generated explanations | 3 | 4 | 4 (can hurt) | Ignore in decision path |
| Real DB / auth / cloud deploy | 2 | 6 | 2 | Ignore |
| Integrations with ServiceNow/GPS etc. | 1 | 9 | 1 | Ignore (out of scope) |
| Other payment rails | 1 | 8 | 1 | Ignore (out of scope) |

### Common reasons teams lose points
- The config change requires a restart, or only changes a threshold unrelated to a scenario.
- Missing-field vs. mismatch vs. unauthorized change are lumped under one generic “difference” label.
- No visible SoD check.
- PASS auto-completes (violates the no-automated-approval rule).
- Reasons are developer-speak (“diff != null”) instead of plain language.
- No run metadata, or metadata not stored with the decision.
- Demo overruns 5 minutes or breaks live.
- Real-looking account numbers or names in the sample data (guardrail violation).

### High-ROI vs. low-ROI
- **High ROI**: live config flip, SoD block moment, exception cards with expected/actual side by side, config hash/version display, test suite running green on screen.
- **Low ROI**: authentication systems, databases, cloud hosting, AI chat, multi-rail generalization, fancy animations.

### Expected winner profile
A small, disciplined team showing a boringly reliable prototype that proves all six ACs in order, with a polished reviewer screen and one or two memorable touches.

---

## 3. Winning Idea Generation

### Option A: Safest High-Scoring (“The Checklist Crusher”)
- **Stack**: Python engine + YAML + simple UI that implements the ACs literally.
- **Problem solved**: the seeded scenarios and the spec as written.
- **Users**: checkers primarily.
- **Advantage**: zero risk, complete AC coverage.
- **Metrics**: Feasibility: 10/10 | Novelty: 3 | Judge appeal: 7 | Win probability: ~20%.
- **Weakness**: indistinguishable from half the field.

### Option B: Most Innovative (“AI Co-Checker”)
- **Concept**: LLM reads the request text and the TNAL log, infers rules, and writes narratives.
- **Advantage**: buzzword appeal.
- **Metrics**: Feasibility: 5/10 | Novelty: 8 | Judge appeal: 5 (violates determinism and explainability; control owners distrust it) | Win probability: ~8%.

### Option C: Best Balance (“Control-in-a-Box”)
- **Concept**: Option A’s reliability plus a rule-governed validation workbench: config hot-reload with schema validation, visible config diff and hash, rules mapped to the 5 Core Validations, SoD enforcement with persona switching, and a tamper-evident audit pack.
- **Problem solved**: the spec, plus “how would this become a reusable control pattern?”
- **Users**: checkers, control owners, and the tech teams who’d reuse it.
- **Advantage**: proves the “reusable validation pattern” claim in section 1.3.
- **Metrics**: Feasibility: 9/10 | Novelty: 6 | Judge appeal: 9 | Win probability: ~38%.

### Option D: Dark Horse (“Rule Impact Simulator”)
- **Concept**: Option C plus a what-if panel: before saving a rule edit, the UI re-runs all 5 scenarios against the draft config and shows a before/after outcome matrix (“this change flips Scenario 5 from EXCEPTION to PASS”). A control owner immediately sees the risk of loosening a rule. Optional stretch: natural-language rule drafting that produces a YAML diff a human must confirm, never an auto-apply.
- **Advantage**: addresses the real-world fear with config-driven controls: “who stops someone from weakening the control by accident?”
- **Metrics**: Feasibility: 8/10 (the what-if is just running the engine N times) | Novelty: 8 | Judge appeal: 9 | Win probability: ~42% (the NL drafting adds risk, so keep it optional).

### Selection: Option C + the what-if matrix from D
**Reasoning**: the what-if matrix costs about 2 hours (it reuses the engine), it makes the AC4 demo far more compelling than “edit file, rerun,” and it raises a governance question that bank judges care about. Skip NL rule drafting unless everything else is locked.

---

## 4. Build Strategy

### Phase 1: Critical MVP (Hours 0-8)

| Feature | Why | Complexity | Judge impact | Time |
|---|---|---|---|---|
| Synthetic data (5 requests, 5 TNAL/GPS records, expected outcomes, evidence flag) | Everything depends on it | Low | High | 1h |
| YAML rule config + loader | AC4 foundation | Low | High | 1h |
| Pure-Python comparison engine returning structured findings | AC1-3 | Medium | Critical | 3h |
| Pytest suite: 5 scenarios vs. expected | AC2 proof | Low | High | 1h |
| Minimal UI: pick scenario → result + exception table | AC1, AC3 | Medium | Critical | 2h |

### Phase 2: Core Features (Hours 8-14)

| Feature | Why | Complexity | Impact | Time |
|---|---|---|---|---|
| Approve/Investigate + notes, stored with run | AC5 | Low | High | 1h |
| SoD: persona switcher, block when checker == maker | AC6 | Low | High | 1h |
| Run metadata header | FAQ 7 | Low | Med | 0.5h |
| Live config editor in-app + re-read per run | AC4 live | Medium | Critical | 2h |
| SIMULATED banners/labels on all “integrations” | AC6 | Low | Med | 0.5h |
| Plain-language reason templates | AC3 | Low | High | 1h |

### Phase 3: Judge-Wow (Hours 14-19)

| Feature | Why | Complexity | Impact | Time |
|---|---|---|---|---|
| What-if matrix (draft config × 5 scenarios) | Governance wow | Medium | Very high | 2h |
| Config diff + content hash as “config version” | Traceability | Low | High | 1h |
| Schema validation, bad config rejected with clear message | Demo safety | Low | High | 1h |
| Five Core Validations checklist panel | Shows control understanding | Low | High | 1h |

### Phase 4: Stretch (Hours 19-22, only if green)
- Hash-chained JSONL audit log + “verify integrity” button (1.5h)
- Export audit pack as JSON/PDF (1h)
- Investigate → “Revalidate” re-run (1h)
- Severity levels: blocking vs. warning (1h)

*Hours 22-24 are for the deck, rehearsal, and submission. Never spend them on features.*

---

## 5. Technology Strategy

**Optimization target**: no setup friction, no network dependency, fully local demo.

| Layer | Recommendation | Why |
|---|---|---|
| Engine | Pure Python module (no framework imports) | Satisfies “clean separation,” trivially testable |
| Config | YAML (rules.yaml) validated with Pydantic | Human-readable live edits, schema safety |
| Backend | FastAPI with `/validate`, `/config`, `/whatif`, `/decision` | Fast, typed, easy to demo |
| Frontend | React + Vite + Tailwind if someone is fluent; otherwise a single-page HTML+Alpine/HTMX UI. Streamlit is the fastest fallback, but it makes the SoD persona and live edit feel less app-like | Pick the stack your team is fastest in |
| Database | SQLite (or just JSONL files) for runs/decisions | Zero setup; a real DB is not a differentiator |
| AI | None in the decision path. Optionally an LLM on a separate “Summarize for ticket” button, labeled advisory | Preserves determinism and explainability |
| APIs | Internal only; mock “ServiceNow/DMS/TNAL/GPS” as loader modules marked SIMULATED | Shows the seam where real integrations plug in |
| Cloud | Run locally. Have a recorded backup video. Bank judges’ networks are unpredictable | Demo reliability |
| Auth | Simulated personas (Maker: proc_jlee, Checker A: rev_mkhan, etc.), no real auth | SoD logic matters, not login |
| Analytics | Run history table + counts of PASS/EXCEPTION by rule | Cheap, supports the business story |

### Config schema sketch
```yaml
version_label: "demo-v1"        # displayed; hash is auto-computed
rules:
  - field: sec_code
    check: exact_match
    on_fail: EXCEPTION
    message: "SEC Code must match the approved request."
  - field: company_entry_description
    check: exact_match
    normalize: [trim, casefold]
  - field: daily_limit
    check: numeric_tolerance
    tolerance: 0
  - field: ach_origination_limit
    check: no_unrequested_change       # unauthorized change detection
  - evidence: customer_authorization_form
    check: required_present
unrequested_changes: EXCEPTION
mandatory_fields: [sec_code, company_entry_description, daily_limit]
```

### Engine design
`engine.run(request, tnal, gps, evidence, config) → Result with overall, findings[], and core_validations[1..5]`. Each finding carries: field, expected, actual, rule_id, rule_text, result, reason, category (`MISMATCH` | `MISSING` | `UNAUTHORIZED` | `EVIDENCE`). It has no I/O and no UI knowledge.

---

## 6. Differentiation Strategy

| Tier | What they build |
|---|---|
| **90% of competitors** | Side-by-side diff, hardcoded rules (or a config that only holds a threshold), generic “mismatch” labels, approve button, slides with ServiceNow logos |
| **Top 10%** | Working YAML rules, categorized findings, SoD check, metadata header, passing tests |
| **Winner** | All of the top-10% items plus the what-if impact matrix, config hash and diff in the audit trail, explicit mapping to the 5 Core Validations, SoD blocking with a logged violation attempt, tamper-evident run log, and a rehearsed 5-minute demo with zero dead air |

### Blue-ocean angle
“Config-driven controls are only safe if changing a rule is itself controlled.” Everyone will prove the rule can change. You prove it can change safely: validated, diffed, impact-previewed, hashed, and recorded in every run. That reframes the entire solution from “a diff tool” to a reusable, governable control pattern, which is exactly the phrase in the spec’s Technology-team beneficiary line.

---

## 7. Demo Day Strategy

### Exact “impress the judges” moments
- **Hook**: a split screen of a spreadsheet-style manual compare vs. the exception card. “Which would you trust at 4:45 p.m. on a Friday?”
- **Scenario 4 (unauthorized change)**: the card highlights a field nobody asked to change. This is the control’s real value.
- **The SoD block**: switch to the maker’s persona, click Approve, red banner: “Blocked: maker cannot approve own change.” Also logged.
- **What-if matrix** before saving a rule edit, showing which scenarios flip.
- **Live flip**: Scenario 5 goes `EXCEPTION → PASS` by changing one line, config hash changes, then flip it back. Both runs appear in history with different config versions.
- **Audit pack**: one click, one screen with run ID, config version hash, decision, notes.

### 3-minute pitch

| Time | Beat |
|---|---|
| 0:00-0:20 | Hook + problem: “Checkers stare at two reports and hunt for a mismatch. Fatigue is the risk.” |
| 0:20-1:20 | Demo: Scenario 1 PASS (checker still must approve), then Scenario 4 exception card with expected/actual/rule/reason |
| 1:20-2:15 | Live config change with what-if preview; the outcome flips; the hash changes |
| 2:15-2:40 | SoD block as the maker |
| 2:40-3:00 | Close: “A first-pass that never approves, never hides its reasoning, and whose rules can’t change silently.” |

### 5-minute pitch (aligned to FAQ 9)

| Min | Content |
|---|---|
| 1 | Hook, problem, stakes: control C-247489, maker-checker, stare-and-compare fatigue. One architecture slide showing the engine / config / UI split and the SIMULATED sources |
| 2-3 | Run all 5 scenarios fast via the scenario list showing expected-vs-actual outcome. Linger on #2 and #4. Show the 5 Core Validations panel lighting up |
| 4 | AC4: edit rule in the live editor → what-if matrix → save → rerun → flip → hash change → revert |
| 5 | Checker records a decision with notes; SoD block; open audit pack; business value (“production savings to be quantified once volume and handling-time baselines are supplied; here’s the measurement hook”) |

### 10-minute pitch (if allowed)
Add: 1 minute on test suite and CI-style green run, 1 minute on the architecture and how a second control (another field set) is added via config only, 1.5 minutes on the roadmap (real TNAL/GPS ingestion, severity levels, revalidation, metrics), 1 minute on the governance story (config change approval workflow). Do not pad with more scenarios.

### Metrics to cite (honest ones)
- 5/5 seeded scenarios match expected outcomes
- Rule change to behavior change: under 10 seconds, zero code changes, zero restarts
- Every finding carries 6 explainability fields
- 100% of runs carry the 5 traceability fields
- *Do not invent production savings. The spec says baselines are pending. Saying “we’ve built the instrumentation to compute it” earns more trust.*

### Closing statement
> *“We didn’t automate the decision, we automated the staring. The checker decides, the rules are visible, and nothing changes silently.”*

---

## 8. Judge Psychology Analysis

- **What judges emotionally look for**: reassurance. They’re control and operations people, so the dominant fear is “will this weaken a control?” They want to feel the checker is more powerful, not replaced.
- **What makes a submission memorable**: a single strong narrative sentence plus one visceral moment. The SoD block and the config flip are the two.

### Features likely to trigger high scores:
- Side-by-side Expected | Actual with the differing characters highlighted
- Color-coded categories (Mismatch / Missing / Unauthorized / Evidence) so scenario types are distinguishable at a glance
- The config version hash printed in the run header
- Automated tests visibly passing

### Looks impressive but is unnecessary:
- Chatbot / “AI assistant” panel
- Real cloud deployment, Kubernetes, a login system
- Dashboards with many charts (one small run-history table is enough)
- Support for additional payment rails (explicitly out of scope)
- Animated transitions and 3D anything

**Subtle trap**: a flashy AI feature in the decision path invites the question “can it be wrong?”, and the spec’s emphasis on explainability turns that into a point loss.

---

## 9. Risk Analysis

### Technical

| Risk | Prob. | Impact | Mitigation |
|---|---|---|---|
| Normalization causes false exceptions on clean match | Med | High | Test Scenario 1 first; make normalization a per-field config option |
| Live-reload race or stale cached config | Med | Critical | Load config on every /validate; no module-level cache; test in pytest |
| Invalid YAML typed live crashes the app | High | Critical | Pydantic validation; reject and keep last-good config; show the error inline |
| Date/number format edge cases | Low | Med | Keep synthetic data in one canonical format; add one normalizer test |

### Time

| Risk | Prob. | Impact | Mitigation |
|---|---|---|---|
| UI polish eats engine time | High | High | Engine + tests locked by hour 8 before any UI styling |
| Deck made last-minute | High | High | Draft deck skeleton at hour 12; final screenshots at hour 20 |
| Stretch goals sneak in | Med | Med | Hard feature freeze at hour 19 |

### Scope

| Risk | Prob. | Impact | Mitigation |
|---|---|---|---|
| Building mock integrations | Med | Med | Static JSON loaders labeled SIMULATED, nothing more |
| Auto-approve creeps in via a “ready” state | Low | Critical | Result states never include “Approved”; only human decision can; add a test asserting this |
| Gold-plating the rule language | Med | Med | Support ~6 check types only: exact, numeric tolerance, allowed values, required, no-unrequested-change, evidence-required |

### Demo

| Risk | Prob. | Impact | Mitigation |
|---|---|---|---|
| Live edit fails on stage | Med | Critical | Pre-written “demo edits” as one-click presets plus manual typing as backup; recorded backup video |
| Network or laptop issue | Med | High | Fully local; second laptop with the same build; no external calls |
| Overrun past 5 min | High | High | Timed rehearsals (minimum 5); scripted click path; cut Scenario 3 narration if needed |
| Real-looking data flagged | Low | High | Obviously fake IDs (ACH-REQ-0001, ACME TEST CO), no account numbers at all |

---

## 10. Winning Execution Plan

*Assumptions: 3 people (Engine/Tests, UI, Pitch/Docs/QA), ~24 hours with sleep, laptops only. If you have fewer hours, compress Phases 3-4 first, never Phase 1-2.*

### Hour-by-hour

| Hours | Engine/Backend | UI | Pitch/Docs |
|---|---|---|---|
| 0-1 | Repo, schema, data model | Wireframe reviewer screen | Reread spec; assign AC owners |
| 1-3 | Synthetic data (5+5), expected outcomes, YAML v1 | Static mock of exception card | Draft architecture one-pager |
| 3-6 | Engine + 6 check types + findings | Scenario selector + result view wired to API | Skeleton deck (6 slides) |
| 6-8 | Pytest 5/5 green, reason templates | Expected/Actual table | Demo script v1 |
| 8-10 | Decision API, run storage, metadata | Approve/Investigate form + header | - |
| 10-12 | SoD logic + violation log | Persona switcher + block banner | Architecture doc finalized |
| 12-14 | `/config` GET/PUT, validation, re-read per run | Config editor panel | First timed rehearsal |
| 14-16 | `/whatif` endpoint | What-if matrix UI | - |
| 16-18 | Config hash, diff, run history | Diff view + Core Validations panel | Screenshots for deck |
| 18-19 | **FEATURE FREEZE** | Polish only | Deck v2 |
| 19-21 | Stretch: audit hash chain / export if all green | Stretch UI | Rehearsals #2-3 |
| 21-22 | Full regression, bug bash | Bug bash | Record backup video |
| 22-23 | Clean repo, README | Final visual polish | Rehearsals #4-5 |
| 23-24 | Package and submit | - | Submission checklist |

### Priority matrix

| | Low effort | High effort |
|---|---|---|
| **High impact** | Explainable table, live config, SoD block, metadata header, tests | What-if matrix, audit chain |
| **Low impact** | SIMULATED labels, severity | Auth, DB, cloud, integrations |

### Feature ranking (build order)
1. Engine + 5 scenarios + tests
2. Explainable exception card
3. External YAML re-read per run
4. Approve/Investigate + metadata
5. SoD block
6. Live config editor + validation
7. What-if matrix
8. Config hash and diff
9. Core Validations panel
10. Audit chain / export / revalidate

### Demo preparation plan
- Preload all 5 scenarios and 2-3 one-click “demo edits”
- Rehearse the exact click path 5+ times with a timer
- Rehearse a failure recovery (what you say if the edit errors)
- Record a backup video at hour 21
- Reset-to-baseline button so repeated demos start clean

### Submission checklist
- [x] Source code and README with a 3-command run
- [x] rules.yaml / rules.json (external, committed)
- [x] Synthetic data files (labeled synthetic)
- [x] Pytest / Test suite: 5 seeded scenarios + live-reload test + no-auto-approve test + SoD test
- [x] Demo walkthrough doc and live-demo script
- [x] 5-minute deck
- [x] 1-page architecture summary (engine / config / UI, SIMULATED sources)
- [x] AC1-AC6 traceability table (each AC → where it’s proven)
- [x] 12-item build checklist (FAQ 11) ticked, with evidence
- [x] Backup demo video

---

## 11. Final Recommendation

### 1. The exact solution to build
“Control-in-a-Box”: a rule-governed ACH Next Day Validation workbench. A pure-Python comparison engine driven by a validated YAML/JSON config, exposed through FastAPI/server, with a reviewer UI showing a categorized exception card, SoD-enforced Approve/Investigate decisions, run metadata, and a live config editor with a what-if impact matrix and config hash/diff.

### 2. Build first
Engine → 5 scenarios + pytest → exception card → YAML/JSON re-read per run → decision + metadata → SoD → live editor.

### 3. Skip
Real auth, databases beyond SQLite/JSONL, cloud, integrations, other rails, AI in the decision path, ticket routing, dashboards.

### 4. Features that maximize score
Findings with all six FAQ-6 fields, a visible AC1-AC6 traceability slide, the live flip, the SoD block, config hash in every run header, green tests on screen.

### 5. Stretch goals worth pursuing
Hash-chained audit log with a verify button, exportable audit pack, investigate → revalidate loop (mirrors Steps 9-11), severity levels. Optional only if everything is locked: natural-language rule drafting that produces a YAML diff requiring human confirmation.

### 6. Architecture diagram
```
┌───────────────────────────────────────────────────────────┐
│  UI (Reviewer Workbench)                                  │
│  Scenario picker │ Exception cards │ Decision + SoD block │
│  Config editor + What-if matrix │ Run history │ Audit pack│
└───────────────▲───────────────────────────────────────────┘
                │ REST (JSON)
┌───────────────┴───────────────────────────────────────────┐
│  API (FastAPI / Server)                                   │
│  /validate  /config  /whatif  /decision  /runs  /export   │
└──────┬──────────────┬──────────────────────┬──────────────┘
       │              │                      │
┌──────▼──────┐ ┌─────▼────────────┐  ┌──────▼───────────┐
│ ENGINE      │ │ CONFIG LOADER    │  │ RUN STORE        │
│ (pure py)   │◄┤ rules.yaml/json  │  │ SQLite / JSONL   │
│ no I/O      │ │ schema-validated │  │ hash-chained     │
│ → findings  │ │ hash = version   │  │ run+decision log │
└──────▲──────┘ └──────────────────┘  └──────────────────┘
       │
┌──────┴─────────────────────────────────────────────────────┐
│ SIMULATED SOURCES (clearly labeled)                         │
│ ServiceNow/DMS request JSON │ TNAL + GPS report JSON │ evid.│
└─────────────────────────────────────────────────────────────┘
SoD: decision API compares checker_id vs. maker_id on the TNAL record
```

### 7. Demo strategy
Scripted click path, one-click demo edits, reset button, backup video, five timed rehearsals. Order: PASS → Unauthorized change → SoD block → what-if → live flip → audit pack.

### 8. Pitch strategy
One narrative: “We automated the staring, not the decision.” Sell trust, not technology. Name the control (C-247489), use the sponsor’s vocabulary (maker-checker, TNAL, SoD, evidence retained), and be candid that savings need baselines.

### 9. What makes this Top 1%
- Every AC visibly proven, in order, with on-screen evidence
- Config change is governed (validated, impact-previewed, hashed, logged), which most teams won’t think of
- The SoD block and logged violation attempt
- Explicit mapping to the real 5 Core Validations, including “GPS matches ACH” and “request exists and is approved,” which most teams ignore
- Zero demo failures and timing to the second
- Test suite includes “system never approves” and “stale config is never used” as named tests

### 10. Estimated probability of winning (if executed well)
Roughly 35-45% to win outright and 75-85% to place in the top three, assuming a field of around 10-20 teams and a rubric close to what’s inferred. The biggest swing factors are demo reliability (±15 points) and whether other teams stumble on the live config requirement.
