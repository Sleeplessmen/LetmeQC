# CVAT Webhook Integration Guide

**Hướng dẫn tích hợp LetmeQC với CVAT thông qua webhook để tự động chạy QC khi annotator hoàn thành công việc.**

LetmeQC hoạt động như một **web service** nhận webhook từ CVAT.
Hướng dẫn này sẽ hướng dẫn bạn setup webhook server và cấu hình trong CVAT.

---

## Yêu cầu

Trước khi bắt đầu, đảm bảo bạn có:

- Python 3.10+ đã cài đặt
- Dự án LetmeQC đã clone và cài đặt dependencies (xem [README.md](README.md))
- Tài khoản CVAT với quyền admin/manager
- CVAT API Token (lấy từ **Profile → Settings → API Token**)

---

## Bước 1: Cấu hình Environment

1. Tạo file `.env`

Copy file mẫu và điền thông tin:

```bash
# Từ thư mục dự án
cp .env.example .env
```

Mở `.env` và chỉnh sửa:

```ini
# === BẮT BUỘC === CVAT API Configuration
CVAT_API_URL=https://app.cvat.ai/api
CVAT_TOKEN=your_cvat_api_token_here

# === TÙY CHỌN === Webhook Configuration (cho security)
WEBHOOK_SECRET=your_super_secure_secret_key_123

# === TÙY CHỌN === QC Configuration (có thể override trong code)
MIN_BOX_AREA=100
IOU_THRESHOLD=0.95

# === TÙY CHỌN === Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
```

**QUAN TRỌNG:**

- `CVAT_TOKEN` **bắt buộc** - Lấy từ CVAT: **Profile → Settings → API Token**
- `WEBHOOK_SECRET` **khuyến nghị** - Để bảo vệ webhook khỏi các request không mong muốn
- Nếu dùng CVAT self-hosted (không phải app.cvat.ai), đổi `CVAT_API_URL` tương ứng

---

## Bước 2: Chạy Webhook Server

### 2.1 Chạy server local

**Phương thức 1: Chạy trực tiếp với Python**

```bash
python app.py
```

**Phương thức 2: Chạy với uvicorn (recommended)**

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Server sẽ khởi động và hiển thị:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReloader
```

### 2.2 Verify server đang chạy

Mở trình duyệt hoặc dùng curl để test:

```bash
# Health check
curl http://localhost:8000/health

# Xem API documentation (Swagger UI)
# Mở: http://localhost:8000/docs

# Xem cấu hình hiện tại
curl http://localhost:8000/config
```

Kết quả expect:

```json
{
  "status": "healthy",
  "timestamp": "2024-10-13T10:00:00.000000",
  "cvat_api_configured": true,
  "qc_engine_ready": true
}
```

Nếu `cvat_api_configured` là `false`, kiểm tra lại `CVAT_TOKEN` trong `.env`.

---

## Bước 3: Expose Server ra Internet với ngrok

CVAT cần gửi webhook đến server của bạn, nhưng server đang chạy local (`localhost:8000`). Bạn cần expose nó ra internet.

### 3.1 Cài đặt ngrok

1. Download ngrok từ: https://ngrok.com/download
2. Giải nén file
3. Thêm ngrok vào PATH hoặc chạy trực tiếp

**Windows:**

- Giải nén vào `C:\ngrok`
- Thêm `C:\ngrok` vào PATH

**Linux/Mac:**

```bash
# Giải nén và di chuyển
unzip ngrok.zip
mv ngrok /usr/local/bin/
```

### 3.2 Chạy ngrok

**Windows (PowerShell):**

```powershell
ngrok http 8000
```

**Linux/Mac:**

```bash
ngrok http 8000
```

Kết quả hiển thị:

```
ngrok by @inconshreveable

Session Status                online
Account                       Your Account (Plan: Free)
Version                       3.x.x
Region                        United States (us)
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abc123.ngrok.io -> http://localhost:8000

Connections                   ttl     opn     rt1     rt2     rt3     rt4
                              0       0       0.00    0.00    0.00    0.00
```

### 3.3 Lấy URL webhook

Từ output trên, bạn sẽ thấy dòng:

```
Forwarding: https://abc123.ngrok.io -> http://localhost:8000
```

**URL webhook của bạn là:** `https://abc123.ngrok.io/webhook/cvat`

### 3.4 ngrok Dashboard

Bạn có thể xem tất cả requests đến server qua ngrok dashboard:

- Mở: http://localhost:4040
- Xem đầy đủ request history
- Inspect payload, headers, response

---

## Bước 4: Cấu hình Webhook trong CVAT

### 4.1 Đăng nhập CVAT

Mở trình duyệt và đăng nhập vào CVAT:

- https://app.cvat.ai (nếu dùng CVAT cloud)
- Hoặc URL của CVAT self-hosted

### 4.2 Đi đến Webhook Settings

Có 2 cách:

**Cách 1:**

1. Click vào avatar (góc phải trên) → **Webhooks**

**Cách 2:**

1. Click vào **Menu** (góc trái trên)
2. Chọn **Webhooks** (hoặc **Settings → Webhooks**)

### 4.3 Tạo Webhook mới

Click **Create Webhook** (hoặc **Add Webhook**)

### 4.4 Điền thông tin Webhook

| Field            | Value                                  | Ghi chú                               |
| ---------------- | -------------------------------------- | ------------------------------------- |
| **Name**         | `LetmeQC Auto QC`                      | Tên tuỳ ý, dễ nhận biết               |
| **URL**          | `https://abc123.ngrok.io/webhook/cvat` | URL từ ngrok (Bước 3.3)               |
| **Method**       | `POST`                                 | ✅ Bắt buộc chọn POST                 |
| **Content Type** | `application/json`                     | ✅ Bắt buộc chọn JSON                 |
| **Events**       | ✅ **Job: Updated**                    | Chọn sự kiện job update               |
| **Secret Key**   | `your_super_secure_secret_key_123`     | Giá trị của WEBHOOK_SECRET trong .env |

**QUAN TRỌNG:**

- URL **phải đúng chính xác** (bao gồm `https://` và `/webhook/cvat`)
- Nếu bạn set `WEBHOOK_SECRET` trong `.env`, hãy điền cùng giá trị vào **Secret Key**
- Nếu không set `WEBHOOK_SECRET`, có thể để trống

### 4.5 Test Webhook

Trước khi save, bạn có thể test webhook:

1. Trong CVAT, **tạo 1 job mới** (hoặc dùng job hiện có)
2. **Thêm một vài annotations** (hoặc dùng job có sẵn annotations)
3. **Chuyển status job sang "validation"**
   - Vào job detail page
   - Click **"Actions"** → **"Change status"** → **"Validation"**

4. **Kiểm tra terminal** chạy `app.py`:
   ```
   2024-10-13 10:00:00 - INFO - 📥 Received webhook payload
   2024-10-13 10:00:00 - INFO - 🔔 Job Update: ID=123 | Name='test_job' | Status='validation' | Assignee=456
   2024-10-13 10:00:01 - INFO - 🚀 Starting automatic QC process for Job 123...
   ```

Nếu thấy logs trên, **webhook đã hoạt động thành công!**

### 4.6 Save Webhook

Sau khi test thành công, click **Save** (hoặc **Create**) để lưu webhook.

---

## Webhook Security (Tùy chọn)

### Sử dụng WEBHOOK_SECRET

Để bảo vệ webhook khỏi các request giả mạo, bạn có thể cấu hình secret key:

1. Trong `.env`:

   ```ini
   WEBHOOK_SECRET=your_super_secure_secret_key_123
   ```

2. Trong CVAT webhook settings:
   - Điền cùng giá trị vào **Secret Key** field

3. CVAT sẽ gửi header:

   ```
   X-CVAT-Webhook-Secret: your_super_secure_secret_key_123
   ```

4. Server sẽ verify header với giá trị trong `.env`

**Nếu secret không khớp**, server trả về:

```
401 Unauthorized: Invalid webhook secret
```

### Cấu hình HTTPS

Ngrok tự động cung cấp HTTPS endpoint. Nếu bạn deploy server trên production (không dùng ngrok), đảm bảo:

- Server chạy với HTTPS (không HTTP)
- Có SSL certificate hợp lệ
- CVAT chỉ gửi webhook đến HTTPS endpoints

---

## Troubleshooting

### Common Issues & Solutions

| Vấn đề                        | Nguyên nhân               | Giải pháp                                                                                             |
| ----------------------------- | ------------------------- | ----------------------------------------------------------------------------------------------------- |
| **Webhook không đến server**  | ngrok không chạy          | Kiểm tra `ngrok http 8000` đang chạy                                                                  |
|                               | URL sai                   | Kiểm tra URL webhook trong CVAT                                                                       |
|                               | Firewall chặn             | Tắt firewall tạm thời hoặc cho phép port 8000                                                         |
| **401 Unauthorized**          | WEBHOOK_SECRET không khớp | Kiểm tra secret trong `.env` và CVAT                                                                  |
|                               | Không gửi secret header   | Đảm bảo CVAT gửi `X-CVAT-Webhook-Secret`                                                              |
| **500 Internal Server Error** | CVAT_TOKEN sai            | Kiểm tra `CVAT_TOKEN` trong `.env`                                                                    |
|                               | CVAT_API_URL sai          | Kiểm tra `CVAT_API_URL`                                                                               |
|                               | Job không có annotations  | Job trống hoặc chưa được annotate                                                                     |
| **ConnectionError**           | Mạng không ổn định        | Kiểm tra kết nối internet                                                                             |
|                               | CVAT API không trả về     | Thử access API thủ công: `curl -H "Authorization: Token YOUR_TOKEN" https://app.cvat.ai/api/jobs/123` |
| **ModuleNotFoundError**       | Thiếu dependencies        | `pip install -r requirements.txt`                                                                     |

### Debug Webhook

1. Kiểm tra ngrok Inspector
2. Kiểm tra Server Logs
3. Test Webhook thủ công
4. Kiểm tra CVAT API

---

## API Reference

### LetmeQC Webhook Server Endpoints

| Method | Endpoint        | Mô tả                          |
| ------ | --------------- | ------------------------------ |
| GET    | `/`             | Service info                   |
| GET    | `/health`       | Health check                   |
| GET    | `/config`       | Hiển thị cấu hình hiện tại     |
| GET    | `/docs`         | Swagger UI (API documentation) |
| POST   | `/webhook/cvat` | CVAT webhook endpoint          |

### CVAT API Endpoints

| Endpoint                     | Method | Mô tả                         | Authentication |
| ---------------------------- | ------ | ----------------------------- | -------------- |
| `/api/jobs`                  | GET    | Lấy danh sách jobs            | Token          |
| `/api/jobs/{id}`             | GET    | Lấy thông tin job             | Token          |
| `/api/jobs/{id}`             | PATCH  | Cập nhật job status           | Token          |
| `/api/jobs/{id}/annotations` | GET    | Lấy annotations (COCO format) | Token          |
| `/api/labels`                | GET    | Lấy danh sách labels          | Token          |
| `/api/labels?job_id={id}`    | GET    | Lấy labels cho job            | Token          |
| `/api/issues`                | POST   | Tạo issue mới                 | Token          |
| `/api/issues`                | GET    | Lấy danh sách issues          | Token          |

**Authentication Header:**

```
Authorization: Bearer YOUR_CVAT_TOKEN
```

---

## Example Workflow

Scenario: Annotator Submit Job for Review

**1. Annotator hoàn thành annotation**

- Job ID: 456
- Status: "annotation" → **chuyển sang "validation"**

**2. CVAT gửi webhook**

```json
POST https://abc123.ngrok.io/webhook/cvat
Content-Type: application/json
X-CVAT-Webhook-Secret: your_super_secure_secret_key_123

{
  "event": "update:job",
  "job": {
    "id": 456,
    "status": "validation",
    "name": "traffic_signs_001",
    "assignee": {"id": 789}
  }
}
```

**3. LetmeQC xử lý**

```
- Parse payload: job_id=456, status=validation
- Fetch annotations từ CVAT API
- Parse annotations thành 50 frames
- Chạy QC checks với min_box_area=100, iou_threshold=0.95
- Phát hiện 3 lỗi:
  * Frame 0: Bbox quá nhỏ (diện tích 50px)
  * Frame 5: Hai bbox "car" overlap (IoU=0.98)
  * Frame 10: Polygon self-intersect
```

**4. LetmeQC tạo issues**

```
- Tạo issue cho frame 0:
  * Job: 456
  * Frame: 0
  * Comment: "QC Check Failed: 1 error(s) found\nError types: Bbox_Too_Small\nFrame: 0"
  * Assignee: 789

- Tạo issue cho frame 5:
  * Job: 456
  * Frame: 5
  * Comment: "QC Check Failed: 1 error(s) found\nError types: Bbox_Overlap\nFrame: 5"
  * Assignee: 789

- Tạo issue cho frame 10:
  * Job: 456
  * Frame: 10
  * Comment: "QC Check Failed: 1 error(s) found\nError types: Polygon_Self_Intersect\nFrame: 10"
  * Assignee: 789
```

**5. LetmeQC cập nhật job status**

```
PATCH https://app.cvat.ai/api/jobs/456
Authorization: Token YOUR_CVAT_TOKEN

{
  "status": "annotation"
}
```

**6. Kết quả**

- Annotator (ID: 789) nhận được 3 issues
- Job 456 quay trở lại status "annotation"
- Annotator có thể xem issues và sửa lỗi

---

## Production Deployment

**Deploy trên VPS (DigitalOcean, AWS, etc.)**

```bash
# SSH vào server
ssh user@your-server-ip

# Clone repository
git clone <repository-url>
cd LetmeQC

# Tạo virtual environment
python -m venv venv
source venv/bin/activate

# Cài dependencies
pip install -r requirements.txt

# Chạy với gunicorn + nginx (recommended)
# Hoặc chạy trực tiếp:
uvicorn app:app --host 0.0.0.0 --port 8000
```
