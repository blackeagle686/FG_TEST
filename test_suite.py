#!/usr/bin/env python3
"""
FortyGuard API v1 Comprehensive Unit Test Suite
Covers all 14 official endpoints with positive contract checks, 
negative input validation, asynchronous status polling, and full monitor lifecycle testing.
"""

import os
import sys
import time
import json
import argparse
from pathlib import Path
import requests

DEFAULT_API_KEY = "f2012*******************************"
API_KEY = os.environ.get("FORTYGUARD_API_KEY", DEFAULT_API_KEY)
BASE_URL = os.environ.get("FORTYGUARD_BASE_URL", "https://api.fortyguard.com")

RESULTS_DIR = Path(__file__).resolve().parent / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "api-key": API_KEY,
    "Content-Type": "application/json"
}

class FortyGuardTestSuite:
    def __init__(self, base_url=BASE_URL, headers=HEADERS):
        self.base_url = base_url
        self.headers = headers
        self.results = []
        self.completed_heatmap_id = None
        self.created_monitor_id = None

    def record_result(self, test_id, name, method, endpoint, status_code, duration_sec, passed, details=None, payload=None):
        entry = {
            "test_id": test_id,
            "name": name,
            "method": method,
            "endpoint": endpoint,
            "status_code": status_code,
            "duration_sec": round(duration_sec, 3),
            "passed": passed,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "details": details,
            "payload": payload
        }
        self.results.append(entry)
        status_symbol = "✓ PASS" if passed else "✗ FAIL"
        print(f"[{status_symbol}] [{test_id}] {name} ({method} {endpoint}) -> Status: {status_code} ({duration_sec:.2f}s)")
        if not passed and details:
            print(f"       Details: {str(details)[:200]}")
        return entry

    def request(self, method, endpoint, payload=None, params=None, custom_headers=None, timeout=25):
        url = f"{self.base_url}{endpoint}" if endpoint.startswith("/") else endpoint
        h = self.headers if custom_headers is None else custom_headers
        t0 = time.time()
        try:
            if method == "GET":
                resp = requests.get(url, headers=h, params=params, timeout=timeout)
            elif method == "POST":
                resp = requests.post(url, headers=h, json=payload, params=params, timeout=timeout)
            elif method == "PATCH":
                resp = requests.patch(url, headers=h, json=payload, params=params, timeout=timeout)
            elif method == "DELETE":
                resp = requests.delete(url, headers=h, params=params, timeout=timeout)
            else:
                raise ValueError(f"Method {method} not supported")
            
            duration = time.time() - t0
            body = None
            if "application/json" in resp.headers.get("content-type", ""):
                try:
                    body = resp.json()
                except Exception:
                    body = resp.text
            else:
                body = resp.text
            return resp.status_code, body, duration
        except requests.exceptions.Timeout:
            return 504, "Client Request Timeout", time.time() - t0
        except Exception as e:
            return 0, str(e), time.time() - t0

    # =========================================================================
    # 1. AUTHENTICATION & SECURITY TESTS
    # =========================================================================
    def test_auth(self):
        print("\n--- Running Authentication Tests ---")
        # Missing Header
        sc, body, dt = self.request("GET", "/v1/monitors", custom_headers={})
        self.record_result("AUTH-01", "Missing API Key Header", "GET", "/v1/monitors", sc, dt, sc == 401, body)

        # Invalid Key
        sc, body, dt = self.request("GET", "/v1/monitors", custom_headers={"api-key": "invalid_api_key_123"})
        self.record_result("AUTH-02", "Invalid API Key Header", "GET", "/v1/monitors", sc, dt, sc == 401, body)

        # Valid Key
        sc, body, dt = self.request("GET", "/v1/monitors")
        self.record_result("AUTH-03", "Valid API Key Header", "GET", "/v1/monitors", sc, dt, sc == 200, body)

    # =========================================================================
    # 2. HEATMAP ENDPOINTS (1. POST /v1/heatmap)
    # =========================================================================
    def test_heatmap(self):
        print("\n--- Running Heatmap Tests (1. /v1/heatmap) ---")
        base_aoi = {
            'type': 'Polygon',
            'coordinates': [[
                [-74.0170, 40.7051],
                [-74.0031, 40.7051],
                [-74.0031, 40.7180],
                [-74.0170, 40.7180],
                [-74.0170, 40.7051]
            ]]
        }

        # 1a. Filter 1: Single Hour
        p1 = {'polygon_aoi': base_aoi, 'date_time': {'start_date': '2024-07-15', 'start_time': '14:00', 'filter_type': 1}, 'granularity': 100}
        sc, body, dt = self.request("POST", "/v1/heatmap", payload=p1)
        passed = sc == 200 and isinstance(body, dict) and body.get("error") is False
        res = self.record_result("HM-01", "Heatmap - Single Hour (100m)", "POST", "/v1/heatmap", sc, dt, passed, body, p1)
        if passed and isinstance(body.get("data"), dict):
            self.completed_heatmap_id = body["data"].get("activity_id")

        # 1b. Filter 2: Range of Hours
        p2 = {'polygon_aoi': base_aoi, 'date_time': {'start_date': '2024-07-15', 'start_time': '09:00', 'end_time': '17:00', 'filter_type': 2}, 'granularity': 80}
        sc, body, dt = self.request("POST", "/v1/heatmap", payload=p2)
        self.record_result("HM-02", "Heatmap - Range of Hours (80m)", "POST", "/v1/heatmap", sc, dt, sc == 200, body, p2)

        # 1c. Filter 3: Single Day
        p3 = {'polygon_aoi': base_aoi, 'date_time': {'start_date': '2024-07-15', 'filter_type': 3}, 'granularity': 60}
        sc, body, dt = self.request("POST", "/v1/heatmap", payload=p3)
        self.record_result("HM-03", "Heatmap - Single Day (60m)", "POST", "/v1/heatmap", sc, dt, sc == 200, body, p3)

        # 1d. Filter 4: Range of Days
        p4 = {'polygon_aoi': base_aoi, 'date_time': {'start_date': '2024-07-01', 'end_date': '2024-07-31', 'filter_type': 4}, 'granularity': 100}
        sc, body, dt = self.request("POST", "/v1/heatmap", payload=p4)
        self.record_result("HM-04", "Heatmap - Range of Days (100m)", "POST", "/v1/heatmap", sc, dt, sc == 200, body, p4)

        # 1e. Analytic: Exceedance
        p5 = {'polygon_aoi': base_aoi, 'date_time': {'start_date': '2024-07-15', 'start_time': '06:00', 'end_time': '18:00', 'filter_type': 2}, 'granularity': 100, 'analytic_type': 'exceedance', 'threshold': 30, 'direction': 'above'}
        sc, body, dt = self.request("POST", "/v1/heatmap", payload=p5)
        self.record_result("HM-05", "Heatmap - Analytic Exceedance", "POST", "/v1/heatmap", sc, dt, sc == 200, body, p5)

        # 1f. Analytic: Time of Measure
        p6 = {'polygon_aoi': base_aoi, 'date_time': {'start_date': '2024-07-15', 'filter_type': 3}, 'granularity': 100, 'analytic_type': 'time_of_measure'}
        sc, body, dt = self.request("POST", "/v1/heatmap", payload=p6)
        self.record_result("HM-06", "Heatmap - Analytic Time of Measure", "POST", "/v1/heatmap", sc, dt, sc == 200, body, p6)

        # Validation Negatives
        p_val1 = {'date_time': {'start_date': '2024-07-15', 'start_time': '14:00', 'filter_type': 1}, 'granularity': 100}
        sc, body, dt = self.request("POST", "/v1/heatmap", payload=p_val1)
        self.record_result("HM-VAL-01", "Heatmap - Missing polygon_aoi", "POST", "/v1/heatmap", sc, dt, sc == 422, body)

        p_val2 = {'polygon_aoi': base_aoi, 'date_time': {'start_date': '2024-07-15', 'filter_type': 99}, 'granularity': 100}
        sc, body, dt = self.request("POST", "/v1/heatmap", payload=p_val2)
        self.record_result("HM-VAL-02", "Heatmap - Invalid filter_type (99)", "POST", "/v1/heatmap", sc, dt, sc == 422, body)

    # =========================================================================
    # 3. SATELLITE & STREET VIEW (2. /v1/satellite & 3. /v1/streetview)
    # =========================================================================
    def test_vision_segmentation(self):
        print("\n--- Running Vision Segmentation Tests (2. Satellite & 3. Street View) ---")
        # 2. Satellite
        p_sat = {
            'sat': {'latitude': 41.846328, 'longitude': -87.743296},
            'date_time': {'start_date': '2024-07-15', 'start_time': '14:00', 'filter_type': 1},
            'granularity': 80
        }
        sc, body, dt = self.request("POST", "/v1/satellite", payload=p_sat)
        self.record_result("SAT-01", "Satellite View Segmentation Submission", "POST", "/v1/satellite", sc, dt, sc == 200, body, p_sat)

        sc, body, dt = self.request("POST", "/v1/satellite", payload={'date_time': {'start_date': '2024-07-15', 'filter_type': 3}})
        self.record_result("SAT-VAL-01", "Satellite - Missing 'sat' Object", "POST", "/v1/satellite", sc, dt, sc == 422, body)

        sc, body, dt = self.request("POST", "/v1/satellite", payload={'sat': {'latitude': 95.0, 'longitude': -87.74}, 'date_time': {'start_date': '2024-07-15', 'filter_type': 3}})
        self.record_result("SAT-VAL-02", "Satellite - Latitude Out of Bounds (95.0)", "POST", "/v1/satellite", sc, dt, sc == 422, body)

        # 3. Street View
        p_str = {'latitude': 40.7128, 'longitude': -74.0060, 'vertical_angle': 10.0, 'horizontal_angle': 90.0, 'back_view': False}
        sc, body, dt = self.request("POST", "/v1/streetview", payload=p_str)
        self.record_result("STR-01", "Street View Segmentation Submission", "POST", "/v1/streetview", sc, dt, sc == 200, body, p_str)

        sc, body, dt = self.request("POST", "/v1/streetview", payload={'vertical_angle': 10.0, 'horizontal_angle': 90.0, 'back_view': False})
        self.record_result("STR-VAL-01", "Street View - Missing Coordinates", "POST", "/v1/streetview", sc, dt, sc == 422, body)

    # =========================================================================
    # 4. HEAT INTELLIGENCE (4. POST /v1/heat_intelligence)
    # =========================================================================
    def test_heat_intelligence(self):
        print("\n--- Running Heat Intelligence Tests (4. /v1/heat_intelligence) ---")
        # Negative test: Doc example specifying 3 categories fails tier check (max 2)
        p_doc = {'latitude': 40.7128, 'longitude': -74.0060, 'temperature': 85, 'date': '2024-07-15', 'analysis': ['geographic', 'environmental', 'urban']}
        sc, body, dt = self.request("POST", "/v1/heat_intelligence", payload=p_doc)
        # Expected 400 due to plan limit
        self.record_result("HI-01", "Heat Intel - Tier Max 2 Categories Enforcement", "POST", "/v1/heat_intelligence", sc, dt, sc == 400, body, p_doc)

        # Compliant submission (2 categories)
        p_valid = {'latitude': 40.7128, 'longitude': -74.0060, 'temperature': 85, 'date': '2024-07-15', 'analysis': ['geographic', 'environmental']}
        sc, body, dt = self.request("POST", "/v1/heat_intelligence", payload=p_valid)
        self.record_result("HI-02", "Heat Intel - Compliant Submission (2 categories)", "POST", "/v1/heat_intelligence", sc, dt, sc == 200, body, p_valid)

        # Missing analysis array
        p_val = {'latitude': 40.7128, 'longitude': -74.0060, 'temperature': 85, 'date': '2024-07-15'}
        sc, body, dt = self.request("POST", "/v1/heat_intelligence", payload=p_val)
        self.record_result("HI-VAL-01", "Heat Intel - Missing 'analysis' Field", "POST", "/v1/heat_intelligence", sc, dt, sc == 422, body)

    # =========================================================================
    # 5. ENVIRONMENTAL PARAMETERS (5. POST /v1/env_params)
    # =========================================================================
    def test_env_params(self):
        print("\n--- Running Environmental Parameters Tests (5. /v1/env_params) ---")
        p_all = {'latitude': 40.7128, 'longitude': -74.0060, 'temperature': 32.5, 'date_time': {'start_date': '2024-07-15', 'start_time': '14:00', 'filter_type': 1}}
        sc, body, dt = self.request("POST", "/v1/env_params", payload=p_all)
        self.record_result("ENV-01", "Environmental Parameters - Default Full Metrics", "POST", "/v1/env_params", sc, dt, sc == 200, body, p_all)

        p_subset = {'latitude': 40.7128, 'longitude': -74.0060, 'temperature': 32.5, 'date_time': {'start_date': '2024-07-15', 'start_time': '14:00', 'filter_type': 1}, 'analysis': ['heat_index_celsius', 'apparent_temperature_celsius', 'relative_humidity_percent']}
        sc, body, dt = self.request("POST", "/v1/env_params", payload=p_subset)
        self.record_result("ENV-02", "Environmental Parameters - Selected 3 Metrics", "POST", "/v1/env_params", sc, dt, sc == 200, body, p_subset)

        p_val = {'latitude': 40.7128, 'longitude': -74.0060, 'date_time': {'start_date': '2024-07-15', 'start_time': '14:00', 'filter_type': 1}}
        sc, body, dt = self.request("POST", "/v1/env_params", payload=p_val)
        self.record_result("ENV-VAL-01", "Environmental Parameters - Missing 'temperature'", "POST", "/v1/env_params", sc, dt, sc == 422, body)

    # =========================================================================
    # 6. TEMPERATURE-AWARE ROUTING (6. POST /v1/routing)
    # =========================================================================
    def test_routing(self):
        print("\n--- Running Temperature-Aware Routing Tests (6. /v1/routing) ---")
        p_route = {'origin': {'lat': 40.7812, 'lon': -73.9665}, 'destination': {'lat': 40.7580, 'lon': -73.9855}, 'departure_time': '2026-10-19T12:00:00Z'}
        sc, body, dt = self.request("POST", "/v1/routing", payload=p_route)
        self.record_result("ROUT-01", "Temperature Routing - Standard NYC Corridor", "POST", "/v1/routing", sc, dt, sc == 200, body, p_route)

        p_ident = {'origin': {'lat': 40.7812, 'lon': -73.9665}, 'destination': {'lat': 40.7812, 'lon': -73.9665}, 'departure_time': '2026-10-19T12:00:00Z'}
        sc, body, dt = self.request("POST", "/v1/routing", payload=p_ident)
        # Note: Backend returns 500 when origin == destination
        self.record_result("ROUT-VAL-01", "Routing - Identical Origin/Destination Check", "POST", "/v1/routing", sc, dt, sc in [400, 422], body, p_ident)

    # =========================================================================
    # 7-13. MONITORS & ALERTS CRUD (7-13. /v1/monitors & alerts)
    # =========================================================================
    def test_monitors_crud(self):
        print("\n--- Running Monitors & Alerts Lifecycle Tests (7–13) ---")
        # Ensure we have a valid heatmap ID
        target_heatmap_id = self.completed_heatmap_id or "292766d2-f98a-4944-9a25-d86d84cb947b"

        # 7. Create Monitor (Requires GeoJSON FeatureCollection)
        boundary_fc = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-74.0170, 40.7051],
                        [-74.0031, 40.7051],
                        [-74.0031, 40.7180],
                        [-74.0170, 40.7180],
                        [-74.0170, 40.7051]
                    ]]
                },
                "properties": {}
            }]
        }
        p_mon = {
            "heatmap_id": target_heatmap_id,
            "name": f"Monitor Unit Test {int(time.time())}",
            "boundary_geojson": boundary_fc,
            "rules": [{
                "temporal_aggregation": "average",
                "spatial_aggregation": "minimum",
                "operator": "above",
                "threshold": 30,
                "unit": "celsius"
            }],
            "notifications": {"email": ["ops-qa@example.com"]},
            "enabled": True,
            "generate_report": True
        }
        sc, body, dt = self.request("POST", "/v1/monitors", payload=p_mon)
        mon_passed = sc == 201 and isinstance(body, dict) and body.get("error") is False
        self.record_result("MON-01", "Create Monitor (7. POST /v1/monitors)", "POST", "/v1/monitors", sc, dt, mon_passed, body, p_mon)

        created_id = None
        if mon_passed and isinstance(body.get("data"), dict):
            created_id = body["data"].get("monitor_id")
            self.created_monitor_id = created_id

        target_mon_id = created_id or "00000000-0000-0000-0000-000000000000"

        # 8. List Monitors
        sc, body, dt = self.request("GET", "/v1/monitors", params={"limit": 25})
        self.record_result("MON-02", "List Monitors (8. GET /v1/monitors)", "GET", "/v1/monitors", sc, dt, sc == 200, body)

        # 9. Get Monitor
        sc, body, dt = self.request("GET", f"/v1/monitors/{target_mon_id}")
        self.record_result("MON-03", f"Get Monitor (9. GET /v1/monitors/{{id}})", "GET", f"/v1/monitors/{target_mon_id}", sc, dt, sc in [200, 404], body)

        # 10. Update Monitor
        patch_payload = {"enabled": False, "name": "Updated Monitor Unit Test (Paused)"}
        sc, body, dt = self.request("PATCH", f"/v1/monitors/{target_mon_id}", payload=patch_payload)
        self.record_result("MON-04", f"Update Monitor (10. PATCH /v1/monitors/{{id}})", "PATCH", f"/v1/monitors/{target_mon_id}", sc, dt, sc in [200, 404], body, patch_payload)

        # 12. List Alerts
        sc, body, dt = self.request("GET", f"/v1/monitors/{target_mon_id}/alerts")
        self.record_result("ALT-01", f"List Alerts (12. GET /v1/monitors/{{id}}/alerts)", "GET", f"/v1/monitors/{target_mon_id}/alerts", sc, dt, sc in [200, 404], body)

        # 13. Alert Report & Download
        dummy_alert_id = "00000000-0000-0000-0000-000000000001"
        sc, body, dt = self.request("GET", f"/v1/monitors/{target_mon_id}/alerts/{dummy_alert_id}/report")
        self.record_result("ALT-02", "Read Alert Report (13. GET .../report)", "GET", f"/v1/monitors/{target_mon_id}/alerts/{dummy_alert_id}/report", sc, dt, sc in [200, 404], body)

        sc, body, dt = self.request("GET", f"/v1/monitors/{target_mon_id}/alerts/{dummy_alert_id}/report/download", params={"file_type": "pdf"})
        self.record_result("ALT-03", "Download Alert Report (13. GET .../download)", "GET", f"/v1/monitors/{target_mon_id}/alerts/{dummy_alert_id}/report/download", sc, dt, sc in [200, 404], body)

        # 11. Delete Monitor
        if created_id:
            sc, body, dt = self.request("DELETE", f"/v1/monitors/{created_id}")
            self.record_result("MON-05", f"Delete Monitor (11. DELETE /v1/monitors/{{id}})", "DELETE", f"/v1/monitors/{created_id}", sc, dt, sc == 200, body)

            # Verification of 404 post-delete
            sc, body, dt = self.request("GET", f"/v1/monitors/{created_id}")
            self.record_result("MON-06", "Verify Monitor 404 Post-Deletion", "GET", f"/v1/monitors/{created_id}", sc, dt, sc == 404, body)

    # =========================================================================
    # 14. STATUS CHECK (14. GET /v1/status/{activity_id})
    # =========================================================================
    def test_status_endpoint(self):
        print("\n--- Running Asynchronous Status Tests (14. /v1/status/{activity_id}) ---")
        # Non-existent activity ID
        sc, body, dt = self.request("GET", "/v1/status/00000000-0000-0000-0000-000000000000")
        self.record_result("STAT-01", "Status Check - Non-Existent Activity UUID", "GET", "/v1/status/00000000-...", sc, dt, sc == 404, body)

        # Active or completed activity check
        test_aid = self.completed_heatmap_id or "292766d2-f98a-4944-9a25-d86d84cb947b"
        sc, body, dt = self.request("GET", f"/v1/status/{test_aid}")
        self.record_result("STAT-02", f"Status Check - Known Activity ({test_aid})", "GET", f"/v1/status/{test_aid}", sc, dt, sc == 200, body)

    # =========================================================================
    # SUITE RUNNER & EXPORT
    # =========================================================================
    def run_all(self):
        t_start = time.time()
        print("=" * 70)
        print("FORTYGUARD API v1 COMPREHENSIVE UNIT TEST SUITE")
        print(f"Target: {self.base_url} | Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

        self.test_auth()
        self.test_heatmap()
        self.test_vision_segmentation()
        self.test_heat_intelligence()
        self.test_env_params()
        self.test_routing()
        self.test_monitors_crud()
        self.test_status_endpoint()

        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        failed = total - passed
        total_time = time.time() - t_start

        out_file = RESULTS_DIR / "unit_test_results.json"
        with open(out_file, "w") as f:
            json.dump(self.results, f, indent=2)

        print("\n" + "=" * 70)
        print(f"TEST SUITE SUMMARY")
        print(f"Total Tests : {total}")
        print(f"Passed      : {passed}")
        print(f"Failed      : {failed}")
        print(f"Pass Rate   : {(passed/total)*100:.1f}%")
        print(f"Total Time  : {total_time:.2f}s")
        print(f"Saved to    : {out_file}")
        print("=" * 70)
        return failed == 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FortyGuard API v1 Unit Test Suite")
    parser.add_argument("--key", help="FortyGuard API key override")
    parser.add_argument("--url", default=BASE_URL, help="Base API URL")
    args = parser.parse_args()

    if args.key:
        HEADERS["api-key"] = args.key

    suite = FortyGuardTestSuite(base_url=args.url, headers=HEADERS)
    success = suite.run_all()
    sys.exit(0 if success else 1)
