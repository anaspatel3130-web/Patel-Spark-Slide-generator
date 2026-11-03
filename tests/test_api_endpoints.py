"""
tests/test_api_endpoints.py
---------------------------
Full integration test covering FastAPI endpoints:
- Health check
- User access request flow
- Master admin login & request approval
- Candidate user account activation
- Excel upload & presentation generation via REST API
"""

import sys
import uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from backend.main import app, seed_administrator
from backend.database import Base, engine
from backend.config import DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD

def test_full_api_workflow():
    print("Testing Full API Workflow...")

    # Ensure tables and master admin exist
    Base.metadata.create_all(bind=engine)
    seed_administrator()

    with TestClient(app) as client:
        # 1. Health check
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "healthy"
        print(" [OK] Health Check")

        # 2. Master Admin Login
        res = client.post("/api/auth/login", json={
            "email": DEFAULT_ADMIN_EMAIL,
            "password": DEFAULT_ADMIN_PASSWORD
        })
        assert res.status_code == 200, f"Login failed: {res.text}"
        admin_token = res.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        print(" [OK] Master Admin Authentication")

        # 2b. Direct Owner Access (anaspatel3130@gmail.com)
        res_owner = client.post("/api/auth/direct-owner-access")
        assert res_owner.status_code == 200, f"Owner direct access failed: {res_owner.text}"
        owner_data = res_owner.json()
        assert owner_data["email"] == "anaspatel3130@gmail.com"
        assert owner_data["role"] == "admin"
        assert "access_token" in owner_data
        print(" [OK] Direct Owner Access (anaspatel3130@gmail.com)")

        # 2c. Social Login (Google & Guest)
        res_google = client.post("/api/auth/social-login", json={"provider": "google"})
        assert res_google.status_code == 200
        assert "access_token" in res_google.json()
        print(" [OK] 1-Click Social Sign-in (Google)")

        res_guest = client.post("/api/auth/social-login", json={"provider": "guest"})
        assert res_guest.status_code == 200
        assert "access_token" in res_guest.json()
        print(" [OK] 1-Click Instant Guest Sign-in")

        # 3. Prospective User submits Access Request
        candidate_email = f"candidate.{uuid.uuid4().hex[:6]}@operations.internal"
        res = client.post("/api/auth/request-access", json={
            "name": "Cousin Analyst",
            "email": candidate_email,
            "department": "Air Operations Division",
            "reason": "Requires automated C-suite deck generation from daily manifests."
        })
        assert res.status_code in [200, 201]
        req_data = res.json()
        req_id = req_data["id"]
        print(f" [OK] Candidate Access Request Submitted (ID: {req_id})")

        # 4. Admin lists requests and approves candidate
        res = client.get("/api/admin/requests", headers=admin_headers)
        assert res.status_code == 200
        requests = res.json()
        assert any(r["id"] == req_id for r in requests)

        res = client.post(f"/api/admin/requests/{req_id}/action", headers=admin_headers, json={"action": "APPROVE"})
        assert res.status_code == 200
        approved_req = res.json()
        invite_token = approved_req["invite_token"]
        assert invite_token is not None
        print(f" [OK] Admin Approved Candidate (Token: {invite_token[:12]}...)")

        # 5. Candidate activates account with new password
        res = client.post("/api/auth/activate", json={
            "invite_token": invite_token,
            "password": "CousinSecurePassword2026!",
            "full_name": "Cousin Senior Analyst"
        })
        assert res.status_code == 200, f"Activation failed: {res.status_code} {res.text}"
        print(" [OK] Candidate Activated Account with Custom Password")

        # 6. Activated User signs in
        res = client.post("/api/auth/login", json={
            "email": candidate_email,
            "password": "CousinSecurePassword2026!"
        })
        assert res.status_code == 200
        user_token = res.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}
        print(" [OK] User Signed in with Newly Activated Credentials")

        # 7. User uploads sample Excel workbook
        sample_file_path = Path("sample_ups_data/UPS_Global_Express_Shipments.xlsx")
        with open(sample_file_path, "rb") as f:
            res = client.post(
                "/api/excel/upload",
                headers=user_headers,
                files={"file": ("UPS_Global_Express_Shipments.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            )
        assert res.status_code == 200, f"Upload failed: {res.text}"
        upload_info = res.json()
        file_id = upload_info["file_id"]
        active_sheet = upload_info["active_sheet"]
        print(f" [OK] File Upload & Schema Inspection (File ID: {file_id}, Sheet: {active_sheet})")

        # 8. User generates presentation (4 slides)
        res = client.post(
            "/api/generator/create",
            headers=user_headers,
            json={
                "file_id": file_id,
                "sheet_name": active_sheet,
                "slide_count": 4,
                "custom_title": "Global Air Operations Review"
            }
        )
        assert res.status_code == 200, f"Generate failed: {res.text}"
        gen_data = res.json()
        assert gen_data["success"] is True
        assert gen_data["slide_count"] == 4
        download_url = gen_data["download_url"]
        excel_download_url = gen_data.get("excel_download_url")
        assert excel_download_url is not None
        assert "validation_report" in gen_data
        assert gen_data["validation_report"]["overall_status"] == "VERIFIED"
        print(f" [OK] PowerPoint Presentation Compiled (Download URL: {download_url})")
        print(f" [OK] Formatted Excel Output Compiled (Download URL: {excel_download_url})")
        print(f" [OK] Cross-Validation Report Verified (Status: {gen_data['validation_report']['overall_status']})")

        # 9. Verify unauthenticated download is blocked (401) and authenticated download succeeds
        unauth_res = client.get(download_url)
        assert unauth_res.status_code == 401
        res = client.get(download_url, headers=user_headers)
        assert res.status_code == 200
        assert "application/vnd.openxmlformats" in res.headers["content-type"]
        assert len(res.content) > 5000
        print(f" [OK] Authenticated PowerPoint Download & Ownership Guard Verified ({len(res.content)} bytes)")

        # 10. Verify Formatted Excel download endpoint with query token auth
        res = client.get(f"{excel_download_url}?token={user_token}")
        assert res.status_code == 200
        assert "application/vnd.openxmlformats" in res.headers["content-type"]
        assert len(res.content) > 2000
        print(f" [OK] Formatted Excel (.xlsx) Download Verified ({len(res.content)} bytes)")

        # 10b. Verify Complete Data Preservation mode & invalid file rejection
        bad_res = client.post(
            "/api/excel/upload",
            headers=user_headers,
            files={"file": ("corrupt.xlsx", b"NOT_A_VALID_ZIP_HEADER", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
        assert bad_res.status_code == 400
        print(" [OK] Invalid Magic-Byte Upload Rejection Verified (HTTP 400)")

        comp_res = client.post(
            "/api/generator/preview",
            headers=user_headers,
            json={
                "file_id": file_id,
                "sheet_name": active_sheet,
                "slide_count": 0,
                "slide_mode": "auto",
                "detail_level": "complete",
                "include_full_data_tables": True,
            }
        )
        assert comp_res.status_code == 200
        comp_plan = comp_res.json()
        assert any(s["layout_type"] == "full_data_table" for s in comp_plan["slides"])
        print(f" [OK] Complete Data Preservation Mode Verified ({comp_plan['actual_slides']} slides with paginated source tables)")

        # 11. Verify Delete / Cancel generated presentation endpoint
        res = client.get("/api/generator/history", headers=user_headers)
        assert res.status_code == 200
        history = res.json()
        assert len(history) > 0
        latest_id = history[0]["id"]

        del_res = client.delete(f"/api/generator/{latest_id}", headers=user_headers)
        assert del_res.status_code == 200
        assert del_res.json()["success"] is True
        print(f" [OK] Presentation Record #{latest_id} & Files Deleted via DELETE endpoint")

        print("\n================ ALL API INTEGRATION TESTS PASSED ================")

if __name__ == "__main__":
    test_full_api_workflow()
