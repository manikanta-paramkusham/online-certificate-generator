"""Local smoke tests — run: python test_local.py"""
from app import app

client = app.test_client()
passed = failed = 0


def test(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        print(f"  FAIL  {name}  {detail}")


print("=== CERTIFY LOCAL TEST SUITE ===\n")

r = client.get("/health")
test("Health endpoint", r.status_code == 200 and r.get_json().get("status") == "ok")

r = client.get("/")
test("Home page loads", r.status_code == 200 and b"Create Certificates" in r.data)

r = client.get("/favicon.ico")
test("Favicon (no 404)", r.status_code == 204)

r = client.post("/api/batches", json={
    "company_name": "Test Company",
    "title": "Python Bootcamp",
    "template": "modern",
    "students": [
        {"name": "Alice", "course": "Java", "date": "2026-06-30"},
        {"name": "Bob"},
        {"name": "Charlie", "date": "2026-07-01"},
    ],
})
data = r.get_json() if r.is_json else {}
test("Create batch API", r.status_code == 200 and data.get("count") == 3, str(data))
uid = data.get("certificates", [{}])[0].get("unique_id", "")

r = client.get(f"/cert/{uid}")
test("View certificate", r.status_code == 200 and b"Alice" in r.data and b"Java" in r.data)

r = client.get(f"/cert/{uid}/download")
test("PDF download", r.status_code == 200 and r.mimetype == "application/pdf" and len(r.data) > 500)

r = client.get("/cert/notvalid!")
test("Invalid ID returns 404", r.status_code == 404)

r = client.post("/api/batches", json={"company_name": "", "title": "", "students": []})
test("Rejects empty data", r.status_code == 400)

r = client.post("/api/batches", json={
    "company_name": "X", "title": "Y", "template": "hacker", "students": [{"name": "Z"}]
})
test("Rejects bad template", r.status_code == 400)

batch_id = data.get("batch_id")
if batch_id:
    r = client.get(f"/api/batches/{batch_id}")
    test("Get batch API", r.status_code == 200 and len(r.get_json().get("certificates", [])) == 3)

for tpl in ("classic", "modern", "elegant"):
    r = client.post("/api/batches", json={
        "company_name": "Co", "title": "Course", "template": tpl, "students": [{"name": "Test"}]
    })
    ok = r.status_code == 200
    if ok:
        tuid = r.get_json()["certificates"][0]["unique_id"]
        r2 = client.get(f"/cert/{tuid}/download")
        ok = r2.status_code == 200 and r2.mimetype == "application/pdf"
    test(f"Template: {tpl}", ok)

print(f"\n=== RESULT: {passed} passed, {failed} failed ===")
if failed:
    raise SystemExit(1)
print("\nAll tests passed! Project is working fine locally.")
