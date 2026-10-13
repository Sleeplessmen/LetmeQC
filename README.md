# LetmeQC - Quality Control Tool for COCO & CVAT Annotations

**LetmeQC** là công cụ tự động kiểm tra chất lượng (Quality Control) cho annotations định dạng COCO, được thiết kế đặc biệt cho hoạt động annotation trên nền tảng CVAT. Công cụ này giúp phát hiện sớm các lỗi phổ biến trong annotation như bounding box quá nhỏ, vượt ngoài khung ảnh, overlap quá mức, polygon tự cắt, v.v.

---

## 🎯 Tính năng chính

### ✅ Kiểm tra Bounding Box
- **Out of Bounds**: Phát hiện bbox vượt ngoài kích thước frame/ảnh
- **Minimum Size**: Phát hiện bbox có diện tích quá nhỏ (configurable)
- **Overlap Detection**: Phát hiện các bbox cùng class overlap quá mức (dựa trên IoU threshold)

### ✅ Kiểm tra Polygon/Segmentation
- **Self-Intersection**: Phát hiện polygon bị vặn chéo hoặc tự cắt các cạnh
- **Mask Out of Box**: Phát hiện mask (polygon) tràn ra ngoài bounding box tương ứng
- **Geometry Validation**: Kiểm tra tính hợp lệ của hình học polygon

### ✅ Kiểm tra Attributes
- **Required Frame Tags**: Kiểm tra frame có thiếu tag bắt buộc
- **Required Object Attributes**: Kiểm tra object có thiếu attribute bắt buộc

### ✅ Tích hợp CVAT
- **Webhook Server**: Nhận sự kiện từ CVAT và tự động trigger QC
- **Auto Issue Creation**: Tự động tạo issue trong CVAT khi phát hiện lỗi
- **Auto Status Update**: Tự động quay lại status "annotation" khi QC fail

---

## 📁 Cấu trúc dự án

```
LetmeQC/
├── app.py                      # FastAPI webhook server
├── .env                        # Environment variables (không commit)
├── .env.example                # Mẫu file .env
├── requirements.txt            # Python dependencies
├── pyproject.toml              # Project configuration
├── README.md                   # Documentation (file này)
├── CVAT_WEBHOOK_GUIDE.md       # Hướng dẫn setup webhook
├── src/
│   ├── __init__.py
│   ├── main.py                 # CLI entry point (chạy offline)
│   ├── models.py               # Data models (Bbox, Polygon, Frame, FrameTag)
│   ├── parser.py               # Parser cho COCO JSON & CVAT API JSON
│   └── rules.py                # QC Rules Engine
├── data/                       # Dữ liệu test & sample
│   ├── test_cases/             # Test cases với các lỗi mẫu
│   └── ...
└── venv/                       # Python virtual environment
```

---

## ⚡ Bắt đầu nhanh

### 📋 Điều kiện tiền đề

- Python 3.10+
- pip 23.0+
- Git

### 💻 Cài đặt

#### 1. Clone repository

```bash
git clone <repository-url>
cd LetmeQC
```

#### 2. Tạo virtual environment

```bash
python -m venv venv
```

#### 3. Kích hoạt virtual environment

**Windows (CMD/PowerShell):**
```bash
.\venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

#### 4. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

#### 5. Verify installation

```bash
python -c "from src.parser import parse_coco_json; from src.rules import QCRulesEngine; print('✅ Installation successful')"
```

---

## 🚀 Sử dụng

LetmeQC hỗ trợ **2 chế độ hoạt động**:

### 🔧 Chế độ 1: CLI (Offline Mode)

Chạy QC trực tiếp trên file COCO JSON đã export từ CVAT.

#### Cú pháp

```bash
python src/main.py <path_to_coco_json> [options]
```

#### Ví dụ

```bash
# Chạy QC với cấu hình mặc định
python src/main.py data/test_cases/test_poly_errors.json

# Chạy QC với threshold tùy chỉnh
python src/main.py data/test_cases/test_bbox_overlap.json \
    --min-area 50 \
    --iou-threshold 0.85 \
    --output errors.json

# Hiển thị help
python src/main.py --help
```

#### Tham số

| Tham số | Mặc định | Mô tả |
|---------|----------|------|
| `--min-area` | 100 | Diện tích bbox tối thiểu (pixels) |
| `--iou-threshold` | 0.95 | Ngưỡng IoU cho overlap detection |
| `--output, -o` | None | File đầu ra lưu lỗi (JSON) |
| `--verbose, -v` | False | Hiển thị chi tiết |

---

### 🌐 Chế độ 2: Webhook Server (Online Mode)

Chạy server nhận webhook từ CVAT và tự động trigger QC.

#### 1. Cấu hình môi trường

Copy `.env.example` sang `.env` và chỉnh sửa:

```bash
cp .env.example .env
```

Mở `.env` và điền các giá trị:

```ini
# CVAT API Configuration (BẮT BUỘC)
CVAT_API_URL=https://app.cvat.ai/api
CVAT_TOKEN=your_cvat_api_token_here

# Webhook Configuration (Tùy chọn - cho security)
WEBHOOK_SECRET=your_super_secure_secret_key

# QC Configuration (Tùy chọn - có thể override trong code)
MIN_BOX_AREA=100
IOU_THRESHOLD=0.95

# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
```

**Lưu ý:** Lấy `CVAT_TOKEN` từ CVAT: **Profile** → **Settings** → **API Token**

#### 2. Chạy webhook server

**Phương thức 1: Chạy trực tiếp**
```bash
python app.py
```

**Phương thức 2: Chạy với uvicorn**
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Server sẽ chạy tại: `http://0.0.0.0:8000`

#### 3. Test server

```bash
# Health check
curl http://localhost:8000/health

# Xem Swagger UI (API documentation)
# Mở trình duyệt: http://localhost:8000/docs

# Xem config hiện tại
curl http://localhost:8000/config
```

#### 4. Expose server ra internet với ngrok

Cài đặt ngrok: https://ngrok.com/download

```bash
# Chạy ngrok
ngrok http 8000
```

Kết quả sẽ hiển thị như:
```
Forwarding: https://abc123.ngrok.io -> http://localhost:8000
```

**✅ URL webhook của bạn:** `https://abc123.ngrok.io/webhook/cvat`

---

## 🔍 Chi tiết QC Rules Engine

### Cấu hình QCRulesEngine

```python
from src.rules import QCRulesEngine

qc_engine = QCRulesEngine(
    min_box_area=100,      # Diện tích bbox tối thiểu (pixels)
    iou_threshold=0.95     # Ngưỡng IoU cho overlap (0-1)
)
```

### Các loại lỗi được phát hiện

| Error Type | Mô tả | Giải pháp |
|------------|-------|-----------|
| `Bbox_Out_Of_Bounds` | Bbox vượt ngoài kích thước frame | Di chuyển bbox vào trong frame |
| `Bbox_Too_Small` | Bbox có diện tích < min_box_area | Vẽ lại bbox to hơn |
| `Bbox_Overlap` | Hai bbox cùng class overlap > iou_threshold | Xóa bỏ bbox overlap hoặc merge |
| `Polygon_Self_Intersect` | Polygon bị vặn chéo/ tự cắt | Vẽ lại polygon đúng chuẩn |
| `Mask_Out_Of_Box` | Polygon tràn ra ngoài bbox tương ứng | Đảm bảo polygon nằm trong bbox |
| `Polygon_Error` | Lỗi hình học polygon chung | Kiểm tra lại các điểm |
| `Missing_Attribute` | Thiếu attribute bắt buộc | Thêm attribute còn thiếu |

### Cấu hình Required Attributes

Trong `rules.py`, bạn có thể cấu hình:

```python
# Frame-level required tags
self.required_frame_tags = ["weather", "time_of_day"]

# Object-level required attributes
self.required_obj_attrs = {
    "car": ["occluded", "truncated"],
    "pedestrian": ["occluded"]
}
```

---

## 📊 Output Format

### CLI Mode Output

Khi chạy với CLI, kết quả sẽ được in ra console:

```json
{
  "Frame": "frame_001.jpg",
  "Object_ID": 123,
  "Error_Type": "Bbox_Too_Small",
  "Message": "Diện tích box (50.0px) nhỏ hơn mức cho phép (100px)"
}
```

Hoặc lưu vào file JSON nếu sử dụng `--output`:

```bash
python src/main.py data/test.json --output errors.json
```

### Webhook Mode Response

Khi nhận webhook từ CVAT, server trả về:

**Nếu QC Pass:**
```json
{
  "message": "QC passed - No errors found",
  "job_id": 123,
  "frames_checked": 10,
  "total_bboxes": 50,
  "total_polygons": 15,
  "action": "approved",
  "timestamp": "2024-10-13T10:00:00.000000"
}
```

**Nếu QC Fail:**
```json
{
  "message": "QC failed - 5 errors found",
  "job_id": 123,
  "total_errors": 5,
  "frames_with_errors": 2,
  "created_issues": 2,
  "errors": [...],
  "action": "rejected",
  "timestamp": "2024-10-13T10:00:00.000000"
}
```

---

## 🧪 Test Cases

Thư mục `data/test_cases/` chứa các file mẫu với lỗi có chủ đích:

| File | Lỗi | Mô tả |
|------|-----|-------|
| `test_bbox_size_oob.json` | Bbox Out of Bounds + Too Small | Bbox vượt khung và quá nhỏ |
| `test_bbox_overlap.json` | Bbox Overlap | Hai bbox cùng class ở cùng vị trí |
| `test_missing_attr.json` | Missing Attribute | Thiếu attribute bắt buộc |
| `test_poly_errors.json` | Polygon Errors | Self-intersect + mask out of box |

**Chạy test case:**
```bash
python src/main.py data/test_cases/test_poly_errors.json
```

---

## 📖 Programmatic Usage

Bạn có thể integrate LetmeQC trực tiếp vào code Python:

```python
from src.parser import parse_coco_json, parse_cvat_api_json
from src.rules import QCRulesEngine
from src.models import Frame

# Parse COCO JSON file
frames = parse_coco_json("path/to/annotations.json")

# Hoặc parse trực tiếp từ CVAT API JSON
raw_data = requests.get("https://app.cvat.ai/api/jobs/123/annotations", headers={"Authorization": "Token YOUR_TOKEN"}).json()
labels_mapping = {1: "car", 2: "person"}  # Lấy từ /api/labels?job_id=123
frames = parse_cvat_api_json(raw_data, labels_mapping)

# Run QC checks
qc_engine = QCRulesEngine(
    min_box_area=100,
    iou_threshold=0.95
)
errors = qc_engine.run_qc_check(frames)

# Xử lý kết quả
if errors:
    print(f"❌ Found {len(errors)} errors")
    for error in errors:
        print(f"  - {error['Error_Type']}: {error['Message']}")
else:
    print("✅ No errors found!")
```

---

## 🛠️ Development

### Running Tests

```bash
# Cài dev dependencies
pip install -r requirements.txt pytest

# Chạy tests
pytest

# Chạy tests với coverage
pytest --cov=src --cov-report=term-missing
```

### Code Formatting

```bash
# Cài black
pip install black

# Format code
black src/

# Hoặc tự động format khi commit (see pyproject.toml)
```

### Type Checking

```bash
pip install mypy
mypy src/
```

---

## 📚 CVAT Integration Guide

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
- ✅ Tự động tạo issue trong CVAT cho mỗi frame có lỗi
- ✅ Tự động quay lại status "annotation" để annotator sửa
- ✅ Gửi thông báo chi tiết về lỗi

---

## 🐛 Troubleshooting

### Common Issues

| Vấn đề | Giải pháp |
|--------|-----------|
| `ModuleNotFoundError: shapely` | `pip install shapely` |
| `AttributeError: 'NoneType' object has no attribute 'get'` | Kiểm tra payload webhook có trường "job" không |
| `ConnectionError: CVAT API` | Kiểm tra CVAT_TOKEN và CVAT_API_URL |
| `ngrok not found` | Cài đặt ngrok: https://ngrok.com/download |
| Port 8000 đã được sử dụng | Đổi SERVER_PORT trong .env |

### Debug Webhook

1. **Check ngrok inspector**: http://localhost:4040
2. **Xem logs server**: Server in ra console đầy đủ logs
3. **Test với curl**:
   ```bash
   curl -X POST http://localhost:8000/webhook/cvat \
     -H "Content-Type: application/json" \
     -d '{"event": "ping"}'
   ```

---

## 📝 Environment Variables

| Biên | Mặc định | Bắt buộc | Mô tả |
|------|----------|----------|-------|
| `CVAT_API_URL` | `https://app.cvat.ai/api` | ✅ | CVAT API base URL |
| `CVAT_TOKEN` | `` | ✅ | CVAT API token |
| `WEBHOOK_SECRET` | `None` | ❌ | Secret key cho webhook verification |
| `MIN_BOX_AREA` | `100` | ❌ | Diện tích bbox tối thiểu |
| `IOU_THRESHOLD` | `0.95` | ❌ | Ngưỡng IoU cho overlap |
| `SERVER_HOST` | `0.0.0.0` | ❌ | Server host |
| `SERVER_PORT` | `8000` | ❌ | Server port |

---

## 🎓 Ví dụ Workflow

### Workflow 1: Offline QC

```bash
# Export annotations từ CVAT (COCO format)
# Chạy QC trên file export
python src/main.py cvat_export.json --min-area 150 --output qc_errors.json

# Kết quả: qc_errors.json chứa danh sách lỗi
# Annotator sửa lỗi dựa trên file này
```

### Workflow 2: Automatic QC with Webhook

```
1. Annotator hoàn thành annotation → Chuyển job sang "validation"
2. CVAT gửi webhook → LetmeQC server nhận signal
3. Server fetch annotations từ CVAT API
4. Server chạy QC checks
5. Nếu có lỗi:
   - Tạo issue trong CVAT
   - Quay lại status "annotation"
   - Annotator nhận được thông báo và sửa
6. Nếu không lỗi:
   - Job giữ status "validation"
   - Sẵn sàng cho review/approval
```

---

## 📄 Tài liệu liên quan

- [CVAT Documentation](https://docs.cvat.ai/)
- [COCO Format Specification](https://cocodataset.org/#format-data)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [ngrok Documentation](https://ngrok.com/docs)

---

## 🤝 Contributing

1. Fork repository
2. Tạo branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -m 'Add new feature'`
4. Push: `git push origin feature/new-feature`
5. Tạo Pull Request

---

## 📜 License

Dự án thuộc sở hữu của VinAI. Vui lòng liên hệ team trước khi sử dụng cho mục đích thương mại.

---

## 💬 Contact

- **Internal Documentation**: Xem tài liệu nội bộ VinAI
- **Team**: Liên hệ với project maintainers
- **Issues**: Báo cáo lỗi qua internal ticket system
