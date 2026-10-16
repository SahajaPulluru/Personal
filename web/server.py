import os
import sys
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timezone

# Add parent directory to path to import engine
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)

from engine.validator import SentinACHValidator

rules_file = os.path.join(base_dir, "config", "rules.json")
scenarios_file = os.path.join(base_dir, "data", "scenarios.json")
audit_store_file = os.path.join(base_dir, "data", "audit_records.json")

# Initialize validator
validator = SentinACHValidator(rules_path=rules_file)

# Ensure audit store exists
if not os.path.exists(audit_store_file):
    with open(audit_store_file, 'w', encoding='utf-8') as f:
        json.dump([], f)

class SentinACHHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.join(base_dir, "web"), **kwargs)

    def _send_json(self, data, status=200):
        body = json.dumps(data, indent=2).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/scenarios":
            with open(scenarios_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._send_json(data)
            return

        if path == "/api/rules":
            with open(rules_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._send_json(data)
            return

        if path == "/api/audit-records":
            with open(audit_store_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._send_json(data)
            return

        # Serve static web files
        if path == "/" or path == "":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        payload = json.loads(post_data.decode('utf-8')) if post_data else {}

        if path == "/api/validate":
            scenario_id = payload.get("scenario_id")
            reviewer_id = payload.get("reviewer_id", "OPER_CHECKER_SMARTIN")
            
            with open(scenarios_file, 'r', encoding='utf-8') as f:
                scenarios_data = json.load(f)
            
            target_scenario = next((s for s in scenarios_data["scenarios"] if s["scenario_id"] == scenario_id), None)
            if not target_scenario:
                self._send_json({"error": f"Scenario '{scenario_id}' not found."}, status=404)
                return

            result = validator.validate_scenario(target_scenario, reviewer_id=reviewer_id)
            self._send_json(result)
            return

        if path == "/api/rules/reload":
            """AC4 Core Requirement: Dynamic hot-reloading of configuration rules."""
            updated_rules = payload.get("rules")
            if updated_rules:
                # Update config version and timestamp
                updated_rules["last_updated"] = datetime.now(timezone.utc).isoformat() + "Z"
                # Persist to disk
                with open(rules_file, 'w', encoding='utf-8') as f:
                    json.dump(updated_rules, f, indent=2)
                # Reload validator in-memory
                validator.load_rules(rules_file)
            else:
                validator.reload_rules()

            self._send_json({
                "status": "SUCCESS",
                "message": "Validation rules hot-reloaded successfully without server restart.",
                "config_version": validator.rules.get("config_version"),
                "last_updated": validator.rules.get("last_updated")
            })
            return

        if path == "/api/decision":
            """AC5 & SoD: Captures human checker decision (Approve vs. Investigate)."""
            run_id = payload.get("run_id")
            scenario_id = payload.get("scenario_id")
            decision = payload.get("decision")  # "APPROVE" or "INVESTIGATE"
            reviewer_id = payload.get("reviewer_id")
            reviewer_role = payload.get("reviewer_role")
            notes = payload.get("notes", "")
            maker_id = payload.get("maker_user_id")

            # Strict Segregation of Duties Check
            if reviewer_role == "MAKER" or (maker_id and reviewer_id == maker_id):
                self._send_json({
                    "status": "ERROR",
                    "error_code": "SOD_VIOLATION",
                    "message": "Segregation of Duties Breach: Maker cannot approve their own change implementation!"
                }, status=403)
                return

            audit_entry = {
                "audit_id": f"AUDIT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                "run_id": run_id,
                "scenario_id": scenario_id,
                "control_id": "C-247489",
                "decision": decision,
                "reviewer_id": reviewer_id,
                "reviewer_role": reviewer_role,
                "decision_timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                "notes": notes,
                "config_version": validator.rules.get("config_version"),
                "audit_packet_hash": payload.get("audit_packet_hash"),
                "status": "COMPLETED" if decision == "APPROVE" else "EXCEPTION_ROUTED_TO_PROCESSOR"
            }

            # Append to persistent audit records
            with open(audit_store_file, 'r', encoding='utf-8') as f:
                records = json.load(f)
            records.append(audit_entry)
            with open(audit_store_file, 'w', encoding='utf-8') as f:
                json.dump(records, f, indent=2)

            self._send_json({
                "status": "SUCCESS",
                "message": f"Reviewer decision '{decision}' recorded successfully.",
                "audit_entry": audit_entry
            })
            return

        self._send_json({"error": "Endpoint not found"}, status=404)

def run_server(port=8080):
    server_address = ('127.0.0.1', port)
    httpd = HTTPServer(server_address, SentinACHHandler)
    print(f"================================================================================")
    print(f"SentinACH Reviewer Cockpit Server listening at http://localhost:{port}")
    print(f"Control C-247489 Next Day Validation Engine Active (Config: {validator.rules.get('config_version')})")
    print(f"================================================================================")
    httpd.serve_forever()

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port)
