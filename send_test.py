import urllib.request
import json
import base64

payload = json.dumps({
    "project_id": "e9b4b060-1a9f-4322-93b8-490a4efcbeb2",
    "document_id": "5acb9440-325d-4b88-9f67-adf3b90cddd6",
    "gcs_path": "projects/e9b4b060-1a9f-4322-93b8-490a4efcbeb2/documents/5acb9440-325d-4b88-9f67-adf3b90cddd6/ADSA new.pdf"
}).encode("utf-8")

b64_data = base64.b64encode(payload).decode("utf-8")

req = urllib.request.Request(
    "http://127.0.0.1:8001/ingest/",
    data=json.dumps({"message": {"data": b64_data}}).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req) as response:
        print(response.read().decode("utf-8"))
except Exception as e:
    print(e)
