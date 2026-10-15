# LetmeQC - Quality Control Web Service for CVAT Annotations

**LetmeQC** là công cụ tự động kiểm tra chất lượng (Quality Control) cho annotations trên nền tảng CVAT. Công cụ này giúp phát hiện sớm các lỗi phổ biến trong annotation như bounding box quá nhỏ, vượt ngoài khung ảnh, overlap quá mức, polygon tự cắt, v.v.

---

## Tính năng chính

### Kiểm tra Bounding Box

- **Out of Bounds**: Phát hiện bbox vượt ngoài kích thước frame/ảnh
- **Minimum Size**: Phát hiện bbox có diện tích quá nhỏ (configurable)
- **Overlap Detection**: Phát hiện các bbox cùng class overlap quá mức (dựa trên IoU threshold)

### Kiểm tra Polygon/Segmentation

- **Self-Intersection**: Phát hiện polygon bị vặn chéo hoặc tự cắt các cạnh
- **Mask Out of Box**: Phát hiện mask (polygon) tràn ra ngoài bounding box tương ứng
- **Geometry Validation**: Kiểm tra tính hợp lệ của hình học polygon

### Kiểm tra Attributes

- **Required Frame Tags**: Kiểm tra frame có thiếu tag bắt buộc
- **Required Object Attributes**: Kiểm tra object có thiếu attribute bắt buộc

### Tích hợp CVAT

- **Webhook Server**: Nhận sự kiện từ CVAT và tự động trigger QC
- **Auto Issue Creation**: Tự động tạo issue trong CVAT khi phát hiện lỗi
- **Auto Status Update**: Tự động quay lại status "annotation" khi QC fail
- **Rich Metadata**: Báo cáo chứa đầy đủ thông tin job và annotation statistics

---

## Bắt đầu nhanh

### 1. Clone repository

```bash
git clone <repository-url>
cd LetmeQC
```

### 2. Tạo virtual environment

```bash
python -m venv venv
```

### 3. Kích hoạt virtual environment

**Windows (CMD/PowerShell):**

```bash
.\venv\Scripts\activate
```

**Linux/Mac:**

```bash
source venv/bin/activate
```

### 4. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 5. Verify installation

```bash
python -c "from src.app.main import app; print('Installation successful')"
```

---

## Sử dụng

LetmeQC hoạt động như một **web service** nhận webhook từ CVAT

### 1. Cấu hình môi trường

Copy `.env.example` sang `.env` và chỉnh sửa:

```bash
cp .env.example .env
```

Mở `.env` và điền các giá trị:

```ini
# CVAT API Configuration (BẮT BUỘC)
CVAT_API_URL=https://app.cvat.ai/api
CVAT_TOKEN=your_cvat_api_token_here

# Organization (Tùy chọn - cho X-Organization header)
CVAT_ORG_SLUG=your_organization_slug

# Webhook Configuration (Tùy chọn - cho security)
WEBHOOK_SECRET=your_super_secure_secret_key

# QC Configuration (Tùy chọn - có thể override trong code)
MIN_BOX_AREA=100
IOU_THRESHOLD=0.95
DUPLICATE_IOU_THRESHOLD=0.98
MIN_POLYGON_POINTS=3
MAX_ASPECT_RATIO=10.0
MIN_ASPECT_RATIO=0.1
MASK_TOLERANCE=2.0
BBOX_TOLERANCE=2.0

# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# Logging Configuration
JSON_LOGGING=false
```

**Lưu ý:** Lấy `CVAT_TOKEN` từ CVAT: **Profile** → **Settings** → **API Token**

### 2. Chạy webhook server

**Phương thức 1: Chạy trực tiếp**

```bash
python app.py
```

**Phương thức 2: Chạy với uvicorn**

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Server sẽ chạy tại: `http://0.0.0.0:8000`

### 3. Test server

```bash
# Health check
curl http://localhost:8000/health

# Xem Swagger UI (API documentation)
# Mở trình duyệt: http://localhost:8000/docs

# Xem config hiện tại
curl http://localhost:8000/config

# Xem metrics
curl http://localhost:8000/metrics
```

### 4. Expose server ra internet với ngrok

Cài đặt ngrok: https://ngrok.com/download

```bash
# Chạy ngrok
ngrok http 8000
```

Kết quả sẽ hiển thị như:

```
Forwarding: https://abc123.ngrok.io -> http://localhost:8000
```

**URL webhook của bạn:** `https://abc123.ngrok.io/webhook/cvat`

---

## Chi tiết QC Rules Engine

### Cấu hình QCRulesEngine

```python
from src.rules import QCRulesEngine

qc_engine = QCRulesEngine(
    min_box_area=100,           # Diện tích bbox tối thiểu (pixels)
    iou_threshold=0.95,        # Ngưỡng IoU cho overlap (0-1)
    duplicate_iou_threshold=0.98,  # Ngưỡng IoU cho duplicate
    min_polygon_points=3,      # Số điểm polygon tối thiểu
    max_aspect_ratio=10.0,     # Tỷ lệ khung hình max
    min_aspect_ratio=0.1,      # Tỷ lệ khung hình min
    mask_tolerance=2.0,        # Độ dung sai mask (pixels)
    bbox_tolerance=2.0         # Độ dung sai bbox (pixels)
)
```

### Các loại lỗi được phát hiện

| Error Type                    | Severity | Mô tả                                       | Giải pháp                      |
| ----------------------------- | -------- | ------------------------------------------- | ------------------------------ |
| `Bbox_Out_Of_Bounds`          | HIGH     | Bbox vượt ngoài kích thước frame            | Di chuyển bbox vào trong frame |
| `Bbox_Too_Small`              | HIGH     | Bbox có diện tích < min_box_area            | Vẽ lại bbox to hơn             |
| `Bbox_Overlap`                | MEDIUM   | Hai bbox cùng class overlap > iou_threshold | Xóa bỏ bbox overlap hoặc merge |
| `Polygon_Self_Intersect`      | HIGH     | Polygon bị vặn chéo/ tự cắt                 | Vẽ lại polygon đúng chuẩn      |
| `Mask_Out_Of_Box`             | MEDIUM   | Polygon tràn ra ngoài bbox tương ứng        | Đảm bảo polygon nằm trong bbox |
| `Duplicate_Objects`           | HIGH     | Hai objects trùng lặp hoàn toàn             | Xóa bớt các bản sao            |
| `Missing_Required_Attributes` | HIGH     | Thiếu attribute bắt buộc                    | Thêm attribute còn thiếu       |
| `Extreme_Aspect_Ratio`        | LOW      | Tỷ lệ khung hình bất thường                 | Kiểm tra lại object            |
| `Label_Consistency`           | MEDIUM   | Class con nằm trong class cha               | Kiểm tra lại nhãn              |

---

## Output Format & Reports

### Webhook Response

Khi nhận webhook từ CVAT, server trả về:

**Nếu QC Pass:**

```json
{
  "message": "QC passed - No errors found",
  "job_id": 123,
  "job_name": "my_job",
  "frames_checked": 10,
  "total_bboxes": 50,
  "total_polygons": 15,
  "action": "passed",
  "report_path": "reports/report_job_123_....json",
  "timestamp": "2024-10-15T10:00:00.000000"
}
```

**Nếu QC Fail:**

```json
{
  "message": "QC failed - 5 errors found",
  "job_id": 123,
  "total_errors": 5,
  "error_types": {
    "Bbox_Too_Small": 2,
    "Bbox_Out_Of_Bounds": 3
  },
  "created_issues": 5,
  "action": "rejected",
  "report_path": "reports/report_job_123_....json",
  "timestamp": "2024-10-15T10:00:00.000000"
}
```

### Report Structure

Mỗi báo cáo QC được lưu trong thư mục `reports/` với cấu trúc:

```json
{
  "job_id": 123,
  "job_name": "my_job",
  "timestamp": "2024-10-15T10:00:00.000000",
  "status": "failed",
  "job_info": {
    "project_id": 456,
    "project_name": "my_project",
    "assignee_id": 789,
    "assignee_name": "annotator_1",
    "created_date": "2024-10-14T09:00:00",
    "updated_date": "2024-10-15T10:00:00",
    "stage": "validation",
    "state": "annotation"
  },
  "annotation_statistics": {
    "image_width": 1920,
    "image_height": 1080,
    "total_shapes": 50,
    "total_tracks": 0,
    "total_tags": 2,
    "frame_count": 10,
    "total_frames": 10,
    "total_annotations": 50
  },
  "qc_results": {
    "total_errors": 5,
    "error_type_counts": {
      "Bbox_Too_Small": 2,
      "Bbox_Out_Of_Bounds": 3
    },
    "issues_created": 5,
    "failed_issue_creations": 0,
    "job_status_updated": "rejected"
  }
}
```

---

## CVAT Integration Guide

Xem chi tiết trong file: **[CVAT_WEBHOOK_GUIDE.md](CVAT_WEBHOOK_GUIDE.md)**

### Quick Setup

1. **Chạy webhook server** (xem phía trên)
2. **Expose với ngrok**: `ngrok http 8000`
3. **Tạo webhook trong CVAT**:
   - URL: `https://abc123.ngrok.io/webhook/cvat`
   - Event: `Job: Updated`
   - Method: POST
   - Content Type: application/json
4. **Test**: Chuyển job sang status "validation" trong CVAT

### Automatic Actions

Khi QC fail:

- Tự động tạo issue trong CVAT cho mỗi frame có lỗi
- Tự động quay lại status "annotation" với state "rejected" để annotator sửa
- Gửi thông báo báo cáo chi tiết về lỗi

---

## Environment Variables

| Biên                      | Mặc định                  | Bắt buộc | Mô tả                               |
| ------------------------- | ------------------------- | -------- | ----------------------------------- |
| `CVAT_API_URL`            | `https://app.cvat.ai/api` | ✅       | CVAT API base URL                   |
| `CVAT_TOKEN`              | ``                        | ✅       | CVAT API token                      |
| `CVAT_ORG_SLUG`           | `None`                    | ❌       | CVAT organization slug              |
| `WEBHOOK_SECRET`          | `None`                    | ❌       | Secret key cho webhook verification |
| `MIN_BOX_AREA`            | `100`                     | ❌       | Diện tích bbox tối thiểu            |
| `IOU_THRESHOLD`           | `0.95`                    | ❌       | Ngưỡng IoU cho overlap              |
| `DUPLICATE_IOU_THRESHOLD` | `0.98`                    | ❌       | Ngưỡng IoU cho duplicate            |
| `MIN_POLYGON_POINTS`      | `3`                       | ❌       | Số điểm polygon tối thiểu           |
| `MAX_ASPECT_RATIO`        | `10.0`                    | ❌       | Tỷ lệ khung hình max                |
| `MIN_ASPECT_RATIO`        | `0.1`                     | ❌       | Tỷ lệ khung hình min                |
| `MASK_TOLERANCE`          | `2.0`                     | ❌       | Độ dung sai mask (pixels)           |
| `BBOX_TOLERANCE`          | `2.0`                     | ❌       | Độ dung sai bbox (pixels)           |
| `SERVER_HOST`             | `0.0.0.0`                 | ❌       | Server host                         |
| `SERVER_PORT`             | `8000`                    | ❌       | Server port                         |
| `JSON_LOGGING`            | `false`                   | ❌       | Bật JSON logging format             |

---

## Workflow: Automatic QC with Webhook

```
1. Annotator hoàn thành annotation → Chuyển job sang "validation"
2. CVAT gửi webhook → LetmeQC server nhận signal
3. Server fetch annotations từ CVAT API
4. Server chạy QC checks trên tất cả frames
5. Nếu có lỗi:
   - Tạo issue trong CVAT cho từng frame có lỗi
   - Quay lại status "annotation" để annotator sửa
   - Annotator nhận được thông báo và sửa lỗi
   - Lặp lại workflow
6. Nếu không lỗi:
   - Job giữ status "validation"
   - Sẵn sàng cho review/approval
   - Báo cáo QC được lưu trong thư mục reports/
```

---

## Monitoring & Metrics

Hệ thống cung cấp endpoints cho monitoring:

- **GET `/health`**: Kiểm tra sức khỏe hệ thống
- **GET `/metrics`**: Xem metrics (request count, error count, job processed, etc.)
- **GET `/config`**: Xem configuration hiện tại

### Available Metrics

- `http_requests_total`: Tổng số requests
- `http_errors_total`: Tổng số errors
- `http_request_duration_seconds`: Thời gian xử lý request
- `jobs_processed_total`: Tổng jobs được xử lý
- `jobs_failed_total`: Jobs fail QC
- `jobs_passed_total`: Jobs pass QC
- `issues_created_total`: Tổng issues được tạo
- `qc_errors_total`: Tổng errors phát hiện

---
