---
description: Manual API Validation Workflow using Thunder Client
---

# API Validation Workflow (Thunder Client)

This workflow guides you through manually testing the SecureOps API using the Thunder Client VS Code extension.

## Prerequisites
1. **Extensions**: Install "Thunder Client" in VS Code.
2. **Backend**: Ensure the API server is running:
   ```bash
   cd secureops-backend
   ./venv/bin/uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
   ```

## Setup
1. **Open Thunder Client**: Click the lightning bolt icon in the sidebar.
2. **Import Collection**:
   - Go to the **Collections** tab.
   - Click the **menu (three dots) -> Import**.
   - Select `secureops-backend/tests/thunder_collection_secureops.json`.
   - You should see a new collection named **"SecureOps Safety API"**.

## Testing Steps

### 1. Upload Batch
- Open request **"1. Upload Batch (Images/PDF)"**.
- In the **Body** tab -> **Form-Data**:
  - The `files` field is pre-configured.
  - **Click the file icon** next to `files` and select one or more images (and/or 1 PDF) from your `test_data` or `downloads`.
- **Click Send**.
- **Verify**: Response should look like `{"video_id": "...", "status": "pending"}`.
- *Note*: This request automatically sets the `current_upload_id` environment variable for subsequent steps.

### 2. Poll Status
- Open request **"2. Poll Status"**.
- **Click Send**.
- **Verify**: Status should be `pending` or `processing`.
- URL is automatically populated with the ID from Step 1.

### 3. Read Results (Summary/Violations/Proximity)
- Once status is `completed` (or if using Seeded data), run requests 3, 4, and 5.
- **Verify**: 
  - Summary shows `accuracy` and counts.
  - Violations returns a list of safety events.
  - Proximity returns risk events.

### 4. Download Report
- Open request **"6. Download Report"**.
- **Click Send**.
- The PDF content will be returned. You can choose to "Save Response to File" in Thunder Client options if you wish to inspect it.

## Error Validation (Manual)
To test error cases:
1. Try uploading >100MB file in Step 1. Expect `413 Request Entity Too Large` or `400`.
2. Try uploading 2 PDFs. Expect `400 Bad Request` (depending on validations active).
