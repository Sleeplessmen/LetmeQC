# CVAT Webhook Integration Guide

Hướng dẫn tích hợp LetmeQC với CVAT thông qua webhook để tự động chạy QC khi annotator hoàn thành công việc.

## 📋 Cấu trúc

```
LetmeQC/
├── app.py                    # FastAPI webhook server
├── src/
│   ├── parser.py            # COCO JSON parser
│   ├── rules.py             # QC rules engine
│   └── models.py            # Data models
└── venv/
```

---

## 🚀 Quick Start

### 1. Cài đặt dependencies

```bash
# Đã cài trong venv
pip install fastapi uvicorn requests
```

### 2. Chạy webhook server

**Phương thức 1: Chạy trực tiếp**
```bash
cd E:/VinAI/LetmeQC
python app.py
```

**Phương thức 2: Chạy với uvicorn**
```bash
cd E:/VinAI/LetmeQC
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Server sẽ chạy tại: `http://0.0.0.0:8000`

### 3. Test server

```bash
# Health check
curl http://localhost:8000/health

# Hoặc mở trình duyệt
http://localhost:8000/docs  # Swagger UI
```

---

## 🌐 Expose Server với ngrok

### Cài đặt ngrok

1. Download ngrok từ: https://ngrok.com/download
2. Giải nén và thêm vào PATH

### Chạy ngrok

**Windows (PowerShell):**
```powershell
ngrok http 8000
```

**Linux/Mac:**
```bash
ngrok http 8000
```

### Kết quả

```
Session Status                online
Account                       Your Account (Plan: Free)
Version                       3.x.x
Region                        United States (us)
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abc123.ngrok.io -> http://localhost:8000
```

✅ **URL webhook của bạn:** `https://abc123.ngrok.io/webhook/cvat`

---

## 🔗 Cấu hình CVAT Webhook

### Bước 1: Tạo Webhook trong CVAT

1. Mở CVAT: https://app.cvat.ai
2. Vào **Menu** → **Webhooks** (hoặc **Settings** → **Webhooks**)
3. Click **Create Webhook**

### Bước 2: Điền thông tin

| Field | Value |
|-------|-------|
| **Name** | LetmeQC Auto QC |
| **URL** | `https://abc123.ngrok.io/webhook/cvat` |
| **Method** | POST |
| **Content Type** | application/json |
| **Events** | ✅ `Job: Updated` |
| **Secret Key** | (Tùy chọn) `your-secret-key` |

### Bước 3: Test webhook

1. Trong CVAT, tạo 1 job mới
2. Chuyển status sang **validation**
3. Kiểm tra terminal chạy `app.py` - sẽ thấy log:
   ```
   🔔 Received signal from Job ID: 123 | Status: validation
   🚀 Starting automatic QC process for Job 123...
   ```

---

## 🛠️ Implement Full QC Logic

Mở file `app.py` và thay thế phần **TODO** với code sau:

### 1. Thêm imports

```python
import requests
from src.parser import parse_coco_json
from src.rules import QCRulesEngine
import os
```

### 2. Thêm biến môi trường

Tạo file `.env`:
```bash
CVAT_API_URL=https://app.cvat.ai/api
CVAT_TOKEN=your_cvat_api_token_here
WEBHOOK_SECRET=your_secret_key  # nếu có
```

### 3. Implement full webhook logic

```python
@app.post("/webhook/cvat")
async def cvat_webhook(request: Request):
    # ... (code hiện có)
    
    if status == "validation":
        logger.info(f"🚀 Starting QC for Job {job_id}...")
        
        # 1. Fetch annotations from CVAT
        cvat_api_url = f"{os.getenv('CVAT_API_URL')}/jobs/{job_id}/annotations"
        headers = {"Authorization": f"Token {os.getenv('CVAT_TOKEN')}"}
        
        response = requests.get(cvat_api_url, headers=headers)
        response.raise_for_status()
        raw_data = response.json()
        
        # 2. Parse COCO JSON
        frames = parse_coco_json(raw_data)
        
        # 3. Run QC checks
        qc_engine = QCRulesEngine(min_box_area=100, iou_threshold=0.95)
        errors = qc_engine.run_qc_check(frames)
        
        # 4. Handle errors
        if errors:
            logger.warning(f"Found {len(errors)} QC errors in Job {job_id}")
            
            # Create issue in CVAT
            issue_url = f"{os.getenv('CVAT_API_URL')}/issues"
            issue_data = {
                "assignee": job.get("assignee", {}).get("id"),
                "job": job_id,
                "frame": errors[0]['Frame'],  # Lấy frame đầu tiên
                "comment": f"QC Check Failed: {len(errors)} errors found",
                "status": "open"
            }
            
            issue_response = requests.post(issue_url, json=issue_data, headers=headers)
            logger.info(f"Created CVAT issue: {issue_response.json()}")
            
            # Change job status back to annotation
            update_url = f"{os.getenv('CVAT_API_URL')}/jobs/{job_id}"
            update_data = {"status": "annotation"}
            update_response = requests.patch(update_url, json=update_data, headers=headers)
            logger.info(f"Job {job_id} status changed back to 'annotation'")
            
            return {
                "message": f"QC failed - {len(errors)} errors found",
                "job_id": job_id,
                "errors": errors,
                "action": "rejected"
            }
        else:
            logger.info(f"✅ QC passed for Job {job_id}")
            return {
                "message": "QC passed - No errors found",
                "job_id": job_id,
                "action": "approved"
            }
```

---

## 🔍 Debugging & Logging

### Xem logs

Server sẽ in logs ra console:
```
2024-10-13 10:00:00 - INFO - Received webhook payload: {...}
2024-10-13 10:00:01 - INFO - 🔔 Received signal from Job ID: 123 | Status: validation
2024-10-13 10:00:01 - INFO - 🚀 Starting automatic QC process for Job 123...
```

### Kiểm tra webhook payload

Sử dụng **webhook.site** hoặc **ngrok inspector** (http://localhost:4040):
- Xem tất cả requests đến server
- Debug payload

---

## 📚 API Reference

### CVAT API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/jobs/{id}/annotations` | GET | Lấy annotations (COCO format) |
| `/api/issues` | POST | Tạo issue mới |
| `/api/jobs/{id}` | PATCH | Cập nhật job status |

### Authentication

```bash
Headers: Authorization: Token YOUR_API_TOKEN
```

Lấy token: **CVAT Profile** → **Settings** → **API Token**

---

## 🎯 Example Workflow

1. **Annotator** hoàn thành annotation → chuyển job sang **validation**
2. **CVAT** gửi webhook → `https://your-ngrok-url.ngrok.io/webhook/cvat`
3. **LetmeQC** nhận webhook → fetch annotations → chạy QC
4. **Nếu có lỗi**: Tạo issue + quay lại status **annotation**
5. **Nếu không lỗi**: Job giữ status **validation** → sẵn sàng cho review

---

## ⚠️ Troubleshooting

### 1. ngrok không hoạt động
```bash
# Kiểm tra ngrok đã chạy
curl http://localhost:4040/api/tunnels
```

### 2. Webhook không đến server
- Kiểm tra URL webhook đúng
- Kiểm tra ngrok tunnel hoạt động
- Kiểm tra firewall/antivirus

### 3. CVAT API lỗi
- Kiểm tra token còn hạn
- Kiểm tra URL API (https://app.cvat.ai vs custom CVAT instance)

### 4. SSL Certificate Error
```python
# Thêm vào requests call
response = requests.get(url, headers=headers, verify=False)
```

---

## 📞 Support

- CVAT Documentation: https://docs.cvat.ai/
- FastAPI Documentation: https://fastapi.tiangolo.com/
- ngrok Documentation: https://ngrok.com/docs
