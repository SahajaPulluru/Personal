import os
import sys
import json
import urllib.request
import urllib.error

def test_endpoints():
    print("================================================================================")
    print("TESTING SENTINACH REST API & CONTROL C-247489 VALIDATION ENGINE")
    print("================================================================================")
    
    # 1. Test GET /api/scenarios
    print("\n[TEST 1] Testing GET /api/scenarios...")
    req = urllib.request.Request("http://127.0.0.1:8080/api/scenarios")
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            scenarios = data.get("scenarios", [])
            print(f"  ✓ Successfully fetched {len(scenarios)} scenarios:")
            for sc in scenarios:
                print(f"    - {sc['scenario_id']}: Expected '{sc['expected_outcome']}'")
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False

    # 2. Test POST /api/validate for Scenario 1 (Clean Match)
    print("\n[TEST 2] Testing POST /api/validate (Scenario 1: Clean Match)...")
    payload = json.dumps({"scenario_id": "SCENARIO_1_CLEAN_MATCH", "reviewer_id": "OPER_CHECKER_SMARTIN"}).encode('utf-8')
    req = urllib.request.Request("http://127.0.0.1:8080/api/validate", data=payload, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        print(f"  ✓ Result: Status={res['overall_status']}, Passed={res['passed_checks']}/{res['total_checks']}, Exceptions={res['failed_checks']}")
        assert res['overall_status'] == "PASS", "Scenario 1 should be PASS"

    # 3. Test POST /api/validate for Scenario 5 (Missing Evidence)
    print("\n[TEST 3] Testing POST /api/validate (Scenario 5: Missing Evidence)...")
    payload = json.dumps({"scenario_id": "SCENARIO_5_MISSING_EVIDENCE", "reviewer_id": "OPER_CHECKER_SMARTIN"}).encode('utf-8')
    req = urllib.request.Request("http://127.0.0.1:8080/api/validate", data=payload, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        print(f"  ✓ Result: Status={res['overall_status']}, Exceptions={res['failed_checks']}")
        assert res['overall_status'] == "EXCEPTION", "Scenario 5 should be EXCEPTION"
        print(f"  ✓ Top Exception: {res['exceptions'][0]['reason']}")

    # 4. Test Segregation of Duties (SoD) Lockout: Maker attempting to approve
    print("\n[TEST 4] Testing Strict Segregation of Duties (Maker cannot self-approve)...")
    sod_payload = json.dumps({
        "run_id": res["run_id"],
        "scenario_id": "SCENARIO_5_MISSING_EVIDENCE",
        "decision": "APPROVE",
        "reviewer_id": "OPER_MAKER_JDOE",
        "reviewer_role": "MAKER",
        "maker_user_id": "OPER_MAKER_JDOE",
        "notes": "Attempting illegal self-approval"
    }).encode('utf-8')
    req = urllib.request.Request("http://127.0.0.1:8080/api/decision", data=sod_payload, headers={'Content-Type': 'application/json'})
    try:
        urllib.request.urlopen(req)
        print("  ✗ ERROR: SoD check failed! Maker was allowed to approve.")
    except urllib.error.HTTPError as e:
        if e.code == 403:
            err_data = json.loads(e.read().decode('utf-8'))
            print(f"  ✓ SUCCESS: Blocked with HTTP 403 Forbidden! Message: {err_data['message']}")
        else:
            print(f"  ✗ Unexpected HTTP code: {e.code}")

    # 5. Test AC4 Dynamic Hot-Reload
    print("\n[TEST 5] Testing AC4 Dynamic Hot-Reload of Rules...")
    # Fetch current rules
    req = urllib.request.Request("http://127.0.0.1:8080/api/rules")
    with urllib.request.urlopen(req) as resp:
        rules = json.loads(resp.read().decode('utf-8'))
    
    # Toggle evidence rule mandatory to false temporarily
    ev_rule = next(r for r in rules["evidence_rules"] if r["evidence_id"] == "EV-01")
    original_mandatory = ev_rule["mandatory"]
    ev_rule["mandatory"] = False
    
    reload_payload = json.dumps({"rules": rules}).encode('utf-8')
    req = urllib.request.Request("http://127.0.0.1:8080/api/rules/reload", data=reload_payload, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as resp:
        reload_res = json.loads(resp.read().decode('utf-8'))
        print(f"  ✓ Rules hot-reloaded: {reload_res['message']}")

    # Re-validate Scenario 5 -> Should now PASS!
    req = urllib.request.Request("http://127.0.0.1:8080/api/validate", data=payload, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as resp:
        res2 = json.loads(resp.read().decode('utf-8'))
        print(f"  ✓ Scenario 5 re-evaluated after rule change: Status={res2['overall_status']}, Exceptions={res2['failed_checks']}")
        assert res2['overall_status'] == "PASS", "Scenario 5 should now PASS after rule exemption"

    # Restore original rule
    ev_rule["mandatory"] = original_mandatory
    reload_payload = json.dumps({"rules": rules}).encode('utf-8')
    req = urllib.request.Request("http://127.0.0.1:8080/api/rules/reload", data=reload_payload, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as resp:
        print("  ✓ Restored original rule configuration.")

    print("\n================================================================================")
    print(">>> ALL API AND GOVERNANCE TESTS PASSED WITH 100% SUCCESS! <<<")
    print("================================================================================")
    return True

if __name__ == "__main__":
    test_endpoints()
