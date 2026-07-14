# test_pipeline.py
import os
import time
import requests

API_URL = "http://localhost:8000/api/v1/automation/process"
STATUS_URL = "http://localhost:8000/api/v1/automation/status/"

def run_integration_test():
    # 1. Create mock files on the fly for validation testing
    form_path = "test_form.png"
    excel_path = "test_ledger.xlsx"

    with open(form_path, "wb") as f:
        f.write(b"Fake binary content for handwritten document image")

    # Create a minimal valid Excel payload structure
    import pandas as pd
    df = pd.DataFrame([{"account_id": "ACC123", "balance": 5000}])
    df.to_excel(excel_path, index=False)

    print("🚀 Triggering production pipeline execution...")

    payload = {'target_url': 'https://example.com'}
    files = [
      ('form_document', (form_path, open(form_path, 'rb'), 'image/png')),
      ('excel_ledger', (excel_path, open(excel_path, 'rb'), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))
    ]

    # 2. Fire multi-part form request to FastAPI endpoint
    response = requests.post(API_URL, data=payload, files=files)

    # Clean up local unsubmitted mock instances instantly
    for f in files: f[1][1].close()
    os.remove(form_path)
    os.remove(excel_path)

    if response.status_code != 202:
        print(f"❌ Initial request rejected: {response.text}")
        return

    job_id = response.json()["job_id"]
    print(f"✅ Job accepted. Tracking ID assigned: {job_id}")

    # 3. Poll the relational database status route until completion or failure
    while True:
        status_res = requests.get(f"{STATUS_URL}{job_id}").json()
        current_state = status_res["status"]
        print(f"⏱️ Current Pipeline Status: [{current_state}]")

        if current_state == "COMPLETED":
            print("\n🎉 Success! AI Synthesis Output Reconciled:")
            import json
            print(json.dumps(status_res["summary_output"], indent=2))
            break
        elif current_state == "FAILED":
            print(f"\n❌ Pipeline failed. Error log:\n{status_res['error_log']}")
            break

        time.sleep(3)

if __name__ == "__main__":
    run_integration_test()
