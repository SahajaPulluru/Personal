# SentinACH: Control C-247489 Operations Reviewer Cockpit
## COO Technology | Global Hackathon Winning Solution

**SentinACH** is a configuration-driven, deterministic validation engine and operations reviewer cockpit designed for **Control C-247489: ACH DB Next Day Validation (Maker-Checker Review)**.

---

## Key Features & Compliance Alignment

1. **Deterministic Comparison Engine (Zero Hallucination)**:
   - Evaluates requested customer maintenance changes (ServiceNow & DMS) against implemented database audit records (TNAL & GPS).
   - Enforces 100% precision on all 5 seeded scenarios.

2. **Strict Segregation of Duties (SoD)**:
   - Built around the inviolable banking regulation: **Automate comparison, preserve human approval**.
   - Enforces role-based lockouts—ACH Processors (Makers) are strictly prohibited from approving their own implementations.

3. **Live Policy Studio (Acceptance Criteria AC4)**:
   - Configuration-driven rule schema in `config/rules.json`.
   - In-app Live Policy Studio supports instant hot-reloading of rules without restarting the server or touching application code.

4. **Cryptographic Audit Trail (CheckMate Integration)**:
   - Emits tamper-evident audit packets with SHA-256 digests, timestamps, Run IDs, and human reviewer decisions (`Approve` vs. `Investigate`).

---

## Project Structure

```
TCOO_Hackathon/
├── config/
│   └── rules.json              # External validation policy schema (AC4)
├── data/
│   ├── scenarios.json          # 5 Seeded reference scenarios (AC6)
│   └── audit_records.json      # Persistent maker-checker audit log
├── engine/
│   └── validator.py            # Pure deterministic validation core
├── web/
│   ├── index.html              # Modern, responsive Reviewer Cockpit UI
│   └── server.py               # Lightweight REST API & static server
├── tests/
│   └── test_harness.py         # End-to-end API, SoD, and AC4 test suite
└── README.md                   # Complete documentation
```

---

## Quickstart & Live Demo Instructions

### 1. Start the Reviewer Cockpit Server
```bash
python3 web/server.py 8080
```
Open **`http://localhost:8080`** in your browser.

### 2. Run the 5 Seeded Scenarios
Click through the scenario buttons in the top ribbon:
- **Scenario 1**: Clean Match $\rightarrow$ Returns `PASS` (14/14 checks pass). Reviewer can click `[Approve & Complete Task]`.
- **Scenario 2**: Field Mismatch $\rightarrow$ Returns `EXCEPTION` (Company Entry Description mismatch).
- **Scenario 3**: Missing Field $\rightarrow$ Returns `EXCEPTION` (Effective Entry Date omitted).
- **Scenario 4**: Unauthorized Change $\rightarrow$ Returns `EXCEPTION` (Unapproved 10x limit increase flagged).
- **Scenario 5**: Missing Evidence $\rightarrow$ Returns `EXCEPTION` (Missing signed customer authorization form in DMS).

### 3. Demonstrate AC4 Live Rule Hot-Reloading
1. While on **Scenario 5**, open the **Live Policy Studio (AC4)** modal.
2. Click the shortcut button: **`[Toggle Rule EV-01 (Mandatory -> Optional)]`**.
3. Click **`[Save & Hot-Reload Policy]`**.
4. Observe **Scenario 5 recalculate live on screen from `EXCEPTION` to `PASS`** without restarting the application!

### 4. Demonstrate Segregation of Duties (SoD)
1. In the header, change the Active Persona to **`John Doe (ACH Operations Processor / Maker)`**.
2. Notice the badge changes to **`SoD Lockout Active`**.
3. Attempt to click **`[Approve & Complete Task]`** $\rightarrow$ The system displays an immediate security lockout blocking self-approval.

---

## Running Automated Tests

```bash
python3 tests/test_harness.py
```
Validates all REST endpoints, the 5 seeded scenarios, SoD enforcement, and AC4 hot-reloading.
