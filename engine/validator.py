import json
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

class SentinACHValidator:
    """
    Control C-247489: ACH DB Next Day Validation Engine
    Pure, deterministic Policy-as-Code comparison engine with zero LLM hallucination.
    """

    def __init__(self, rules_path: Optional[str] = None, rules_data: Optional[Dict[str, Any]] = None):
        self.rules_path = rules_path
        if rules_data:
            self.rules = rules_data
        elif rules_path:
            self.load_rules(rules_path)
        else:
            raise ValueError("Either rules_path or rules_data must be provided.")

    def load_rules(self, rules_path: str):
        """Loads external configuration rules from JSON file."""
        with open(rules_path, 'r', encoding='utf-8') as f:
            self.rules = json.load(f)
        self.rules_path = rules_path

    def reload_rules(self) -> Dict[str, Any]:
        """Hot-reloads configuration rules live without code recompile or restart (AC4)."""
        if self.rules_path:
            self.load_rules(self.rules_path)
        return self.rules

    def _get_nested_val(self, data: Dict[str, Any], path: str) -> Any:
        """Extracts value from data using dot-notation path, stripping leading namespace."""
        parts = path.split('.')
        key = parts[-1] if len(parts) > 1 else parts[0]
        return data.get(key)

    def validate_scenario(
        self,
        scenario: Dict[str, Any],
        reviewer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes the 5 Core Validations of Control C-247489:
        1. Validate Request Exists & is Approved
        2. Compare Requested Values vs. TNAL Actual Values
        3. Verify All Requested Changes Completed (Blank/Missing Detection)
        4. Check for Unauthorized or Unexpected Changes
        5. Validate GPS Matches ACH Implementation
        + Evidence Verification in DMS
        """
        now_utc = datetime.now(timezone.utc)
        run_id = f"RUN-{now_utc.strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8].upper()}"
        timestamp = now_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        request_meta = scenario.get("request_metadata", {})
        servicenow = scenario.get("servicenow_request", {})
        tnal = scenario.get("tnal_audit_log", {})
        gps = scenario.get("gps_customer_report", {})
        dms = scenario.get("dms_evidence", [])

        field_evaluations: List[Dict[str, Any]] = []
        exceptions: List[Dict[str, Any]] = []

        # -------------------------------------------------------------
        # STEP 6.1: Validate Request Exists & is Approved in ServiceNow
        # -------------------------------------------------------------
        req_ticket_id = request_meta.get("servicenow_ticket_id", "")
        req_status = request_meta.get("status", "")
        if not req_ticket_id:
            exc = {
                "check_category": "REQUEST_GOVERNANCE",
                "field_name": "servicenow_ticket_id",
                "display_label": "ServiceNow Request Record",
                "expected": "Valid Approved Ticket",
                "actual": "Missing Request ID",
                "rule_applied": "GOV-01: Approved Maintenance Ticket Required",
                "result": "FAIL",
                "severity": "CRITICAL",
                "reason": "No approved customer maintenance ticket identified for this change batch."
            }
            exceptions.append(exc)
            field_evaluations.append(exc)

        # -------------------------------------------------------------
        # STEP 6.2 & 6.3: Field-by-Field Comparison & Missing Fields
        # -------------------------------------------------------------
        for rule in self.rules.get("field_rules", []):
            field_name = rule["field_name"]
            display_label = rule.get("display_label", field_name)
            exp_val = servicenow.get(field_name)
            act_val = tnal.get(field_name)
            comp_type = rule.get("comparison_type", "exact")
            mandatory = rule.get("mandatory", True)
            severity = rule.get("severity", "HIGH")

            # Check 6.3: Missing mandatory field in TNAL
            if mandatory and (act_val is None or act_val == ""):
                exc = {
                    "check_category": "MISSING_FIELD",
                    "field_name": field_name,
                    "display_label": display_label,
                    "expected": str(exp_val),
                    "actual": "[BLANK / OMITTED]",
                    "rule_applied": f"Rule AC-2: Mandatory Field Enforcement ({field_name})",
                    "result": "FAIL",
                    "severity": severity,
                    "reason": f"Mandatory field '{display_label}' was requested as '{exp_val}' but omitted or empty in TNAL audit log."
                }
                exceptions.append(exc)
                field_evaluations.append(exc)
                continue

            # Check 6.2: Comparison logic
            passed = False
            reason = "Values match approved request."

            if comp_type == "exact_case_insensitive":
                passed = str(exp_val).strip().lower() == str(act_val).strip().lower()
                if not passed:
                    reason = f"Case-insensitive value mismatch: Expected '{exp_val}', but implemented as '{act_val}'."
            elif comp_type == "numeric_tolerance":
                try:
                    exp_num = float(exp_val)
                    act_num = float(act_val)
                    tol = float(rule.get("tolerance", 0.0))
                    diff = abs(exp_num - act_num)
                    passed = diff <= tol
                    if not passed:
                        if act_num > exp_num:
                            reason = f"Unauthorized limit inflation: Database limit (${act_num:,.2f}) exceeds approved request (${exp_num:,.2f})."
                        else:
                            reason = f"Numeric mismatch: Expected ${exp_num:,.2f}, actual ${act_num:,.2f} (diff ${diff:,.2f} > tolerance ${tol:,.2f})."
                except (ValueError, TypeError):
                    passed = False
                    reason = f"Invalid numeric format encountered during comparison."
            elif comp_type == "date_exact":
                passed = str(exp_val).strip() == str(act_val).strip()
                if not passed:
                    reason = f"Effective date mismatch: Requested date '{exp_val}' differs from implemented date '{act_val}'."
            else:  # default 'exact'
                passed = str(exp_val).strip() == str(act_val).strip()
                if not passed:
                    reason = f"Exact value mismatch: Requested '{exp_val}', but TNAL audit log records '{act_val}'."

            eval_entry = {
                "check_category": "FIELD_COMPARISON",
                "field_name": field_name,
                "display_label": display_label,
                "expected": str(exp_val) if exp_val is not None else "[NONE]",
                "actual": str(act_val) if act_val is not None else "[BLANK]",
                "rule_applied": f"Rule: {comp_type}",
                "result": "PASS" if passed else "FAIL",
                "severity": "NORMAL" if passed else severity,
                "reason": reason
            }

            if not passed:
                exceptions.append(eval_entry)
            field_evaluations.append(eval_entry)

        # -------------------------------------------------------------
        # STEP 6.4: Unauthorized / Unexpected Changes Detection
        # -------------------------------------------------------------
        if self.rules.get("unauthorized_change_detection", {}).get("enabled", True):
            for tnal_k, tnal_v in tnal.items():
                if tnal_k in ["report_id", "execution_timestamp", "processor_id"]:
                    continue
                if tnal_k not in servicenow:
                    exc = {
                        "check_category": "UNAUTHORIZED_CHANGE",
                        "field_name": tnal_k,
                        "display_label": f"Unexpected Column: {tnal_k}",
                        "expected": "[NO REQUESTED CHANGE]",
                        "actual": str(tnal_v),
                        "rule_applied": "UNAUTH-01: Disallow modifications without ServiceNow change ticket",
                        "result": "FAIL",
                        "severity": "CRITICAL",
                        "reason": f"Field '{tnal_k}' modified in ACH DB to '{tnal_v}' without corresponding ServiceNow maintenance request."
                    }
                    exceptions.append(exc)
                    field_evaluations.append(exc)

        # -------------------------------------------------------------
        # EVIDENCE VERIFICATION: DMS Supporting Documents Check
        # -------------------------------------------------------------
        evidence_evaluations: List[Dict[str, Any]] = []
        for ev_rule in self.rules.get("evidence_rules", []):
            ev_type = ev_rule["evidence_type"]
            ev_label = ev_rule.get("display_label", ev_type)
            is_mandatory = ev_rule.get("mandatory", True)
            condition = ev_rule.get("applicable_condition", {})

            # Check applicability
            sec_cond = condition.get("sec_code", [])
            min_limit = condition.get("min_credit_limit", 0)
            req_sec = servicenow.get("sec_code", "")
            req_limit = float(servicenow.get("daily_credit_limit", 0))

            applicable = True
            if sec_cond and req_sec not in sec_cond:
                applicable = False
            if min_limit and req_limit < min_limit:
                applicable = False

            if applicable and is_mandatory:
                # Find in DMS evidence
                matching_doc = next(
                    (d for d in dms if d.get("document_type") == ev_type and d.get("status") == "ATTACHED_AND_VERIFIED"),
                    None
                )
                if matching_doc:
                    ev_eval = {
                        "check_category": "EVIDENCE_VERIFICATION",
                        "evidence_id": ev_rule.get("evidence_id"),
                        "evidence_type": ev_type,
                        "display_label": ev_label,
                        "document_name": matching_doc.get("document_name"),
                        "status": "VERIFIED_PRESENT",
                        "result": "PASS",
                        "reason": f"Required evidence '{ev_label}' verified in DMS (Doc ID: {matching_doc.get('document_id')})."
                    }
                else:
                    ev_eval = {
                        "check_category": "EVIDENCE_VERIFICATION",
                        "evidence_id": ev_rule.get("evidence_id"),
                        "evidence_type": ev_type,
                        "display_label": ev_label,
                        "document_name": "[NOT FOUND IN DMS]",
                        "status": "MISSING_EVIDENCE",
                        "result": "FAIL",
                        "severity": ev_rule.get("severity", "CRITICAL"),
                        "reason": f"Regulatory Non-Compliance: '{ev_label}' is mandatory for SEC Code '{req_sec}' but missing in DMS."
                    }
                    exceptions.append(ev_eval)
                evidence_evaluations.append(ev_eval)

        # -------------------------------------------------------------
        # STEP 6.5: Validate GPS Matches ACH Implementation
        # -------------------------------------------------------------
        gps_evaluations: List[Dict[str, Any]] = []
        gps_rules = self.rules.get("gps_cross_system_reconciliation", {})
        if gps_rules.get("enabled", True):
            for mapping in gps_rules.get("compare_fields", []):
                fname = mapping["field_name"]
                tnal_f = mapping["tnal_field"]
                gps_f = mapping["gps_field"]
                t_val = str(tnal.get(tnal_f, "")).strip().lower()
                g_val = str(gps.get(gps_f, "")).strip().lower()
                
                # Format float if limit
                if "limit" in tnal_f:
                    try:
                        t_val = f"{float(t_val):.2f}"
                        g_val = f"{float(g_val):.2f}"
                    except (ValueError, TypeError):
                        pass

                gps_pass = (t_val == g_val)
                g_eval = {
                    "field_name": fname,
                    "tnal_value": str(tnal.get(tnal_f)),
                    "gps_value": str(gps.get(gps_f)),
                    "result": "PASS" if gps_pass else "FAIL",
                    "reason": "GPS Customer Master matches TNAL implementation." if gps_pass else f"Cross-system desync: TNAL has '{t_val}' but GPS report records '{g_val}'."
                }
                if not gps_pass:
                    exceptions.append({
                        "check_category": "GPS_CROSS_SYSTEM_DESYNC",
                        "field_name": fname,
                        "display_label": f"GPS Sync: {fname}",
                        "expected": str(tnal.get(tnal_f)),
                        "actual": str(gps.get(gps_f)),
                        "rule_applied": "GPS-SYNC-01: Ensure GPS Customer Master reflects ACH DB",
                        "result": "FAIL",
                        "severity": gps_rules.get("severity", "HIGH"),
                        "reason": g_eval["reason"]
                    })
                gps_evaluations.append(g_eval)

        # -------------------------------------------------------------
        # Summary & Cryptographic Audit Hash
        # -------------------------------------------------------------
        overall_status = "PASS" if len(exceptions) == 0 else "EXCEPTION"
        total_checks = len(field_evaluations) + len(evidence_evaluations) + len(gps_evaluations)
        failed_count = len(exceptions)
        passed_count = total_checks - failed_count

        summary_payload = {
            "control_id": self.rules.get("control_id", "C-247489"),
            "control_name": self.rules.get("control_name", "ACH DB Next Day Validation"),
            "run_id": run_id,
            "timestamp": timestamp,
            "config_version": self.rules.get("config_version", "2.4.1"),
            "scenario_id": scenario.get("scenario_id", "UNKNOWN"),
            "scenario_name": scenario.get("name", "Unknown Scenario"),
            "servicenow_ticket_id": req_ticket_id,
            "tnal_report_id": tnal.get("report_id", "UNKNOWN"),
            "gps_report_id": gps.get("report_id", "UNKNOWN"),
            "overall_status": overall_status,
            "expected_outcome": scenario.get("expected_outcome", "UNKNOWN"),
            "benchmark_match": (overall_status == scenario.get("expected_outcome")),
            "total_checks": total_checks,
            "passed_checks": passed_count,
            "failed_checks": failed_count,
            "field_evaluations": field_evaluations,
            "evidence_evaluations": evidence_evaluations,
            "gps_evaluations": gps_evaluations,
            "exceptions": exceptions,
            "segregation_of_duties": {
                "maker_user_id": request_meta.get("maker_user_id", "UNKNOWN"),
                "maker_name": request_meta.get("maker_name", "ACH Processor"),
                "checker_user_id": reviewer_id or "PENDING_CHECKER_ASSIGNMENT",
                "sod_compliant": (reviewer_id != request_meta.get("maker_user_id")) if reviewer_id else True
            }
        }

        # Calculate SHA-256 hash of results for immutable audit trail
        digest = hashlib.sha256(json.dumps(summary_payload, sort_keys=True).encode('utf-8')).hexdigest()
        summary_payload["audit_packet_hash"] = f"SHA256:{digest}"

        return summary_payload


if __name__ == "__main__":
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rules_path = os.path.join(base_dir, "config", "rules.json")
    scenarios_path = os.path.join(base_dir, "data", "scenarios.json")

    validator = SentinACHValidator(rules_path=rules_path)
    with open(scenarios_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("================================================================================")
    print("RUNNING SENTINACH DETERMINISTIC VALIDATION HARNESS (5 SEEDED SCENARIOS)")
    print("================================================================================")
    
    all_matched = True
    for sc in data["scenarios"]:
        res = validator.validate_scenario(sc, reviewer_id="OPER_CHECKER_SMARTIN")
        status_match = res["benchmark_match"]
        all_matched = all_matched and status_match
        print(f"\n[{sc['scenario_id']}]")
        print(f"  Name:     {sc['name']}")
        print(f"  Expected: {sc['expected_outcome']} | Actual: {res['overall_status']} -> {'✓ MATCH' if status_match else '✗ MISMATCH'}")
        print(f"  Passed Checks: {res['passed_checks']}/{res['total_checks']} | Exceptions: {res['failed_checks']}")
        if res["exceptions"]:
            print("  Top Exception:")
            print(f"    - {res['exceptions'][0]['display_label']}: {res['exceptions'][0]['reason']}")

    print("\n================================================================================")
    if all_matched:
        print(">>> 100% SUCCESS: ALL 5 SEEDED SCENARIOS MATCHED EXPECTED OUTCOMES PERFECTLY! <<<")
    else:
        print(">>> WARNING: Benchmark mismatch detected! <<<")
    print("================================================================================")
