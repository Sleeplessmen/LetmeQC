# 📋 Kế hoạch Triển khai - CVAT QC Rule-Based Pipeline

**Tài liệu**: Kế hoạch chi tiết triển khai các tính năng từ [CVAT_API_ENDPOINT.md](./CVAT_API_ENDPOINT.md) và [QC_RULE_BASED_IMPLEMENTATION.md](./QC_RULE_BASED_IMPLEMENTATION.md).

**Ngày**: 2026-10-14  
**Trạng thái**: 🟡 Đang lập kế hoạch  
**Mục tiêu**: Hoàn thiện Pipeline QC Tầng 1 (Rule-Based).

---

## 🎯 Tóm tắt Tình trạng Hiện có

### ✅ Đã có
- `app.py`: Webhook server, CVAT API client cơ bản
- `src/rules.py`: Bbox bounds/sizes, Overlapping, Polygon checks
- `src/parser.py`: Parse CVAT API JSON (hardcoded 1280x720)
- `src/models.py`: Data classes hoàn chỉnh
- `src/main.py`: CLI entry point

### ❌ Thiếu sót
| Yêu cầu | Tài liệu | Trạng thái |
|---------|----------|------------|
| X-Organization header | CVAT_API_ENDPOINT | ❌ Chưa implement |
| Position calculation | QC_RULE_BASED_IMPLEMENTATION | ❌ Chưa implement |
| Error template system | QC_RULE_BASED_IMPLEMENTATION | ❌ Chưa có |
| Phase 1-3 Rules | QC_RULE_BASED_IMPLEMENTATION | ❌ Chỉ có 1 phần |
| Job status update | CVAT_API_ENDPOINT | ❌ Chưa implement |
| Actual frame dimensions | - | ❌ Hardcoded 1280x720 |
| Report generation | TODO.md | ❌ Chưa có |

---

## 📁 Cấu trúc File Mới/Được Cập nhật

```
LetmeQC/
├── app.py                    # ⭐ CẬP NHẬT
├── .env                      # ⭐ CẬP NHẬT (thêm CVAT_ORG_SLUG)
├── src/
│   ├── config.py             # ⭐ MỚI (cấu hình tập trung)
│   ├── utils.py              # ⭐ MỚI (helper functions)
│   ├── error_templates.py    # ⭐ MỚI (template system)
│   ├── reports.py            # ⭐ MỚI (báo cáo QC - tóm tắt ngắn gọn)
│   ├── parser.py             # ⭐ CẬP NHẬT
│   ├── rules.py              # ⭐ CẬP NHẬT (core)
│   └── main.py               # ⭐ CẬP NHẬT (tùy chọn)
└── tests/
    ├── test_rules.py         # ⭐ MỚI
    └── test_utils.py         # ⭐ MỚI
```

---

## 📌 Chi tiết Triển khai theo File

### 1. `.env` - Thêm cấu hình Organization
```env
CVAT_ORG_SLUG=your_organization_slug
```

---

### 2. `src/config.py` - ✨ FILE MỚI
**Mục đích**: Quản lý tất cả cấu hình tập trung

```python
"""Central configuration management"""
import os
from dataclasses import dataclass

@dataclass
class QCConfig:
    min_box_area: float = 100.0
    min_polygon_points: int = 3
    iou_threshold: float = 0.95
    duplicate_iou_threshold: float = 0.98
    max_aspect_ratio: float = 10.0
    min_aspect_ratio: float = 0.1
    mask_tolerance: float = 2.0
    bbox_tolerance: float = 2.0
    
    @classmethod
    def from_env(cls):
        return cls(
            min_box_area=float(os.getenv('MIN_BOX_AREA', '100')),
            min_polygon_points=int(os.getenv('MIN_POLYGON_POINTS', '3')),
            iou_threshold=float(os.getenv('IOU_THRESHOLD', '0.95')),
            duplicate_iou_threshold=float(os.getenv('DUPLICATE_IOU_THRESHOLD', '0.98')),
            max_aspect_ratio=float(os.getenv('MAX_ASPECT_RATIO', '10.0')),
            min_aspect_ratio=float(os.getenv('MIN_ASPECT_RATIO', '0.1')),
            mask_tolerance=float(os.getenv('MASK_TOLERANCE', '2.0')),
            bbox_tolerance=float(os.getenv('BBOX_TOLERANCE', '2.0')),
        )

@dataclass  
class CVATAPIConfig:
    base_url: str
    token: str
    org_slug: str = None
    timeout: int = 30
    
    @classmethod
    def from_env(cls):
        return cls(
            base_url=os.getenv('CVAT_API_URL', 'https://app.cvat.ai/api'),
            token=os.getenv('CVAT_TOKEN', ''),
            org_slug=os.getenv('CVAT_ORG_SLUG', None),
            timeout=int(os.getenv('CVAT_TIMEOUT', '30')),
        )

qc_config = QCConfig.from_env()
cvat_config = CVATAPIConfig.from_env()

def get_headers():
    headers = {"Authorization": f"Bearer {cvat_config.token}", "Content-Type": "application/json"}
    if cvat_config.org_slug:
        headers["X-Organization"] = cvat_config.org_slug
    return headers
```

---

### 3. `src/utils.py` - ✨ FILE MỚI
**Mục đích**: Helper functions dùng chung

```python
"""Utility functions"""
from typing import List, Tuple, Optional

def calculate_iou(box1: Tuple[float, float, float, float], box2: Tuple[float, float, float, float]) -> float:
    """Tính IoU giữa 2 bounding box"""
    inter_x1, inter_y1 = max(box1[0], box2[0]), max(box1[1], box2[1])
    inter_x2, inter_y2 = min(box1[2], box2[2]), min(box1[3], box2[3])
    if inter_x2 < inter_x1 or inter_y2 < inter_y1:
        return 0.0
    intersection_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
    box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union_area = box1_area + box2_area - intersection_area
    return intersection_area / union_area if union_area > 0 else 0.0

def calculate_intersection_box(box1, box2) -> Optional[Tuple]:
    """Tính tọa độ vùng giao nhau"""
    inter_x1, inter_y1 = max(box1[0], box2[0]), max(box1[1], box2[1])
    inter_x2, inter_y2 = min(box1[2], box2[2]), min(box1[3], box2[3])
    if inter_x2 < inter_x1 or inter_y2 < inter_y1:
        return None
    return (inter_x1, inter_y1, inter_x2, inter_y2)

def get_bbox_from_points(points: List[Tuple[float, float]]) -> Tuple:
    """Tính bounding box từ danh sách points"""
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    return (min(xs), min(ys), max(xs), max(ys))

def clamp_to_image(bbox: Tuple, img_width: int, img_height: int) -> Tuple:
    """Khống chế tọa độ bbox trong phạm vi ảnh"""
    return (max(0, min(bbox[0], img_width)), max(0, min(bbox[1], img_height)),
            max(0, min(bbox[2], img_width)), max(0, min(bbox[3], img_height)))

def calculate_aspect_ratio(bbox: Tuple) -> float:
    """Tính aspect ratio (width/height)"""
    width, height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    return width / height if height > 0 else float('inf')
```

---

### 4. `src/error_templates.py` - ✨ FILE MỚI
**Mục đích**: Sinh message, severity, suggestion theo template

```python
"""Error message template system"""
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ErrorTemplate:
    severity: str  # high, medium, low
    message: str
    suggestion: str

ERROR_TEMPLATES: Dict[str, ErrorTemplate] = {
    "Bbox_Out_Of_Bounds": ErrorTemplate(
        severity="high",
        message="Box vượt ngoài viền ảnh ({img_w}x{img_h}). Tọa độ xbr/ybr vượt quá giới hạn.",
        suggestion="Kéo viền box thu gọn vào bên trong viền ảnh."
    ),
    "Bbox_Too_Small": ErrorTemplate(
        severity="high",
        message="Diện tích box ({area:.1f}px) nhỏ hơn mức cho phép ({min_area}px).",
        suggestion="Hãy phóng to khu vực này. Nếu là object thật, vẽ sát viền; nếu là rác, hãy xóa."
    ),
    "Polygon_Point_Count": ErrorTemplate(
        severity="high",
        message="Polygon chỉ có {point_count} điểm, cần ≥ 3 điểm.",
        suggestion="Thêm ít nhất 1 điểm nữa."
    ),
    "Bbox_Overlap": ErrorTemplate(
        severity="medium",
        message="Phát hiện {count} box '{label}' (ID {obj_ids}) trùng lắp {iou:.0%} IoU.",
        suggestion="Gộp các box trùng lắp hoặc chia tách nếu là các object riêng biệt."
    ),
    "Polygon_Self_Intersect": ErrorTemplate(
        severity="high",
        message="Polygon của class '{label}' bị tự cắt chéo nét.",
        suggestion="Xóa điểm vắt chéo hoặc dùng công cụ Split/Edit polygon."
    ),
    "Duplicate_Objects": ErrorTemplate(
        severity="high",
        message="Duplicate Object: Trùng lặp hoàn toàn với ID {obj_ids}.",
        suggestion="Xóa bớt các bản sao trùng lặp."
    ),
    "Mask_Out_Of_Box": ErrorTemplate(
        severity="medium",
        message="Mask '{label}' bị lem ra ngoài Bbox > {tolerance}px.",
        suggestion="Điều chỉnh Polygon/Mask cho khớp với Bounding Box."
    ),
    "Extreme_Aspect_Ratio": ErrorTemplate(
        severity="low",
        message="Aspect ratio bất thường (Ratio = {ratio:.1f}).",
        suggestion="Kiểm tra lại object. Nếu là lỗi, điều chỉnh kích thước."
    ),
    "Label_Consistency": ErrorTemplate(
        severity="medium",
        message="Class '{child_label}' nằm trong Class '{parent_label}' - không phù hợp.",
        suggestion="Kiểm tra lại nhãn."
    ),
    "UNKNOWN": ErrorTemplate(
        severity="medium", message="Phát hiện lỗi không xác định.",
        suggestion="Kiểm tra lại nhãn theo Guidelines."
    )
}

def format_error_message(template_key: str, **kwargs) -> str:
    template = ERROR_TEMPLATES.get(template_key, ERROR_TEMPLATES["UNKNOWN"])
    try:
        return template.message.format(**kwargs)
    except KeyError:
        return template.message

def get_error_template(template_key: str) -> ErrorTemplate:
    return ERROR_TEMPLATES.get(template_key, ERROR_TEMPLATES["UNKNOWN"])

def generate_error_payload(frame_name: str, obj_id: Any, error_type: str,
                           position: Optional[List[float]] = None, **extra_info) -> Dict[str, Any]:
    template = get_error_template(error_type)
    payload = {
        "Frame": str(frame_name), "Object_ID": str(obj_id),
        "Error_Type": error_type,
        "Message": format_error_message(error_type, **extra_info),
        "Severity": template.severity, "Suggestion": template.suggestion,
        "Details": {}
    }
    if position is not None:
        payload["Position"] = position
    if extra_info:
        payload["Details"].update(extra_info)
    return payload
```

---

### 5. `src/parser.py` - CẬP NHẬT
**Thay đổi**: Lấy kích thước frame thực tế từ metadata

```python
from .models import Frame, Bbox, Polygon, FrameTag
from typing import List, Dict

def parse_cvat_api_json(raw_data: dict, labels_mapping: Dict[int, str]) -> List[Frame]:
    frames_dict = {}
    default_width, default_height = 1280, 720
    if 'meta' in raw_data and 'size' in raw_data.get('meta', {}):
        meta = raw_data['meta']['size']
        default_width = int(meta.get('width', default_width))
        default_height = int(meta.get('height', default_height))
    
    def get_or_create_frame(frame_idx: int):
        if frame_idx not in frames_dict:
            frames_dict[frame_idx] = Frame(
                frame_id=frame_idx, width=default_width,
                height=default_height, name=str(frame_idx)
            )
        return frames_dict[frame_idx]
    
    for shape in raw_data.get('shapes', []):
        frame_idx = shape.get('frame', 0)
        frame_obj = get_or_create_frame(frame_idx)
        label_id = shape.get('label_id')
        label_name = labels_mapping.get(label_id, f"label_{label_id}")
        shape_type = shape.get('type')
        points = shape.get('points', [])
        attrs = {str(attr['spec_id']): attr['value'] for attr in shape.get('attributes', [])}
        
        if shape_type == 'rectangle' and len(points) >= 4:
            frame_obj.bboxes.append(Bbox(
                id=shape.get('id'), label=label_name,
                xtl=float(points[0]), ytl=float(points[1]),
                xbr=float(points[2]), ybr=float(points[3]), attributes=attrs
            ))
        elif shape_type == 'polygon' and len(points) >= 6:
            points_list = [(points[i], points[i+1]) for i in range(0, len(points), 2)]
            frame_obj.polygons.append(Polygon(
                id=shape.get('id'), label=label_name,
                points=points_list, attributes=attrs
            ))
        elif shape_type == 'polyline':
            points_list = [(points[i], points[i+1]) for i in range(0, len(points), 2)]
            frame_obj.polygons.append(Polygon(
                id=shape.get('id'), label=label_name,
                points=points_list, attributes=attrs
            ))
    
    for tag in raw_data.get('tags', []):
        frame_idx = tag.get('frame', 0)
        frame_obj = get_or_create_frame(frame_idx)
        label_id = tag.get('label_id')
        label_name = labels_mapping.get(label_id, f"tag_{label_id}")
        attrs = {str(attr['spec_id']): attr['value'] for attr in tag.get('attributes', [])}
        frame_obj.tags.append(FrameTag(label=label_name, attributes=attrs))
    
    return list(frames_dict.values())

---

### 6. `src/rules.py` - CẬP NHẬT HOÀN TOÀN
**Thay đổi**: Implement tất cả rules Phase 1-3

```python
"""QC Rules Engine - Implement tất cả rules Phase 1-3"""
from .models import Frame, Bbox, Polygon
from .error_templates import generate_error_payload
from .utils import calculate_iou, calculate_intersection_box, get_bbox_from_points, clamp_to_image, calculate_aspect_ratio
from typing import List, Dict, Any, Tuple, Optional
from shapely.geometry import Polygon as ShapelyPoly

class QCRulesEngine:
    def __init__(self, min_box_area=100.0, iou_threshold=0.95,
                 duplicate_iou_threshold=0.98, min_polygon_points=3,
                 max_aspect_ratio=10.0, min_aspect_ratio=0.1,
                 mask_tolerance=2.0, bbox_tolerance=2.0):
        self.min_box_area = min_box_area
        self.iou_threshold = iou_threshold
        self.duplicate_iou_threshold = duplicate_iou_threshold
        self.min_polygon_points = min_polygon_points
        self.max_aspect_ratio = max_aspect_ratio
        self.min_aspect_ratio = min_aspect_ratio
        self.mask_tolerance = mask_tolerance
        self.bbox_tolerance = bbox_tolerance

    def run_qc_check(self, frames: List[Frame]) -> List[Dict[str, Any]]:
        all_errors = []
        for frame in frames:
            errors = self._check_single_frame(frame)
            if errors:
                all_errors.extend(errors)
        return all_errors

    def _check_single_frame(self, frame: Frame) -> List[Dict[str, Any]]:
        errors = []
        # Phase 1
        errors.extend(self._check_bbox_out_of_bounds(frame))
        errors.extend(self._check_bbox_too_small(frame))
        errors.extend(self._check_polygon_point_count(frame))
        # Phase 2
        errors.extend(self._check_overlapping_bboxes(frame))
        errors.extend(self._check_self_intersecting_polygons(frame))
        errors.extend(self._check_duplicate_objects(frame))
        # Phase 3
        errors.extend(self._check_mask_out_of_bbox(frame))
        errors.extend(self._check_extreme_aspect_ratio(frame))
        errors.extend(self._check_label_consistency(frame))
        return errors

    # PHASE 1: CRITICAL
    def _check_bbox_out_of_bounds(self, frame: Frame) -> List[Dict]:
        errors = []
        for box in frame.bboxes:
            is_out = (box.xtl < -self.bbox_tolerance or box.ytl < -self.bbox_tolerance or
                      box.xbr > frame.width + self.bbox_tolerance or box.ybr > frame.height + self.bbox_tolerance)
            if is_out:
                position = clamp_to_image((box.xtl, box.ytl, box.xbr, box.ybr), frame.width, frame.height)
                errors.append(generate_error_payload(
                    frame.name, box.id, "Bbox_Out_Of_Bounds", list(position),
                    img_w=frame.width, img_h=frame.height, label=box.label,
                    bounds=[box.xtl, box.ytl, box.xbr, box.ybr]
                ))
        return errors

    def _check_bbox_too_small(self, frame: Frame) -> List[Dict]:
        errors = []
        for box in frame.bboxes:
            area = (box.xbr - box.xtl) * (box.ybr - box.ytl)
            if area < self.min_box_area:
                errors.append(generate_error_payload(
                    frame.name, box.id, "Bbox_Too_Small", [box.xtl, box.ytl, box.xbr, box.ybr],
                    area=area, min_area=self.min_box_area, label=box.label
                ))
        return errors

    def _check_polygon_point_count(self, frame: Frame) -> List[Dict]:
        errors = []
        for poly in frame.polygons:
            if len(poly.points) < self.min_polygon_points:
                position = get_bbox_from_points(poly.points)
                errors.append(generate_error_payload(
                    frame.name, poly.id, "Polygon_Point_Count", list(position),
                    point_count=len(poly.points), min_points=self.min_polygon_points, label=poly.label
                ))
        return errors

    # PHASE 2: GEOMETRY & LOGIC
    def _check_overlapping_bboxes(self, frame: Frame) -> List[Dict]:
        errors = []
        label_groups = {}
        for box in frame.bboxes:
            label_groups.setdefault(box.label, []).append(box)
        for label, group in label_groups.items():
            if len(group) < 2:
                continue
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    box1, box2 = group[i], group[j]
                    iou = calculate_iou((box1.xtl, box1.ytl, box1.xbr, box1.ybr),
                                       (box2.xtl, box2.ytl, box2.xbr, box2.ybr))
                    if iou > self.iou_threshold:
                        intersection = calculate_intersection_box(
                            (box1.xtl, box1.ytl, box1.xbr, box1.ybr),
                            (box2.xtl, box2.ytl, box2.xbr, box2.ybr)
                        )
                        position = list(intersection) if intersection else [box2.xtl, box2.ytl, box2.xbr, box2.ybr]
                        errors.append(generate_error_payload(
                            frame.name, f"{box1.id} & {box2.id}", "Bbox_Overlap", position,
                            count=2, label=label, obj_ids=f"{box1.id} & {box2.id}", iou=iou
                        ))
        return errors

    def _check_self_intersecting_polygons(self, frame: Frame) -> List[Dict]:
        errors = []
        for poly in frame.polygons:
            if len(poly.points) < 3:
                continue
            try:
                shapely_poly = ShapelyPoly(poly.points)
                if not shapely_poly.is_valid:
                    position = get_bbox_from_points(poly.points)
                    errors.append(generate_error_payload(
                        frame.name, poly.id, "Polygon_Self_Intersect", list(position), label=poly.label
                    ))
            except Exception:
                continue
        return errors

    def _check_duplicate_objects(self, frame: Frame) -> List[Dict]:
        errors = []
        label_groups = {}
        for box in frame.bboxes:
            label_groups.setdefault(box.label, []).append(box)
        for label, group in label_groups.items():
            if len(group) < 2:
                continue
            checked = set()
            for i in range(len(group)):
                if i in checked:
                    continue
                for j in range(i + 1, len(group)):
                    box1, box2 = group[i], group[j]
                    iou = calculate_iou((box1.xtl, box1.ytl, box1.xbr, box1.ybr),
                                       (box2.xtl, box2.ytl, box2.xbr, box2.ybr))
                    if iou >= self.duplicate_iou_threshold and box1.attributes == box2.attributes:
                        errors.append(generate_error_payload(
                            frame.name, f"{box1.id} & {box2.id}", "Duplicate_Objects",
                            [box2.xtl, box2.ytl, box2.xbr, box2.ybr],
                            obj_ids=f"{box1.id} & {box2.id}", label=label, iou=iou
                        ))
                        checked.add(j)
        return errors

    # PHASE 3: ADVANCED
    def _check_mask_out_of_bbox(self, frame: Frame) -> List[Dict]:
        errors = []
        for poly in frame.polygons:
            if len(poly.points) < 3:
                continue
            matching_box = next((b for b in frame.bboxes if b.id == poly.id), None)
            if not matching_box:
                continue
            try:
                shapely_poly = ShapelyPoly(poly.points)
                min_x, min_y, max_x, max_y = shapely_poly.bounds
                is_out = (min_x < matching_box.xtl - self.mask_tolerance or
                          min_y < matching_box.ytl - self.mask_tolerance or
                          max_x > matching_box.xbr + self.mask_tolerance or
                          max_y > matching_box.ybr + self.mask_tolerance)
                if is_out:
                    errors.append(generate_error_payload(
                        frame.name, poly.id, "Mask_Out_Of_Box", [min_x, min_y, max_x, max_y],
                        label=poly.label, tolerance=self.mask_tolerance
                    ))
            except Exception:
                continue
        return errors

    def _check_extreme_aspect_ratio(self, frame: Frame) -> List[Dict]:
        errors = []
        for box in frame.bboxes:
            ratio = calculate_aspect_ratio((box.xtl, box.ytl, box.xbr, box.ybr))
            if ratio > self.max_aspect_ratio or ratio < self.min_aspect_ratio:
                errors.append(generate_error_payload(
                    frame.name, box.id, "Extreme_Aspect_Ratio", [box.xtl, box.ytl, box.xbr, box.ybr],
                    ratio=ratio, label=box.label
                ))
        return errors

    def _check_label_consistency(self, frame: Frame) -> List[Dict]:
        errors = []
        label_hierarchy = {"pedestrian": ["car", "truck", "bus"], "person": ["car", "truck", "bus"]}
        for child_label, parent_labels in label_hierarchy.items():
            child_boxes = [b for b in frame.bboxes if b.label == child_label]
            for child in child_boxes:
                child_box = (child.xtl, child.ytl, child.xbr, child.ybr)
                for parent_label in parent_labels:
                    parent_boxes = [b for b in frame.bboxes if b.label == parent_label and b.id != child.id]
                    for parent in parent_boxes:
                        parent_box = (parent.xtl, parent.ytl, parent.xbr, parent.ybr)
                        iou = calculate_iou(child_box, parent_box)
                        if iou > 0.95:
                            errors.append(generate_error_payload(
                                frame.name, child.id, "Label_Consistency",
                                [child.xtl, child.ytl, child.xbr, child.ybr],
                                child_label=child_label, parent_label=parent_label
                            ))
        return errors
```

---

### 7. `app.py` - CẬP NHẬT HOÀN TOÀN

**Thay đổi 1**: Import và cấu hình

```python
from src.config import cvat_config, qc_config, get_headers
from src.error_templates import generate_error_payload
from src.reports import QCReport

MIN_BOX_AREA = qc_config.min_box_area
IOU_THRESHOLD = qc_config.iou_threshold
```

**Thay đổi 2**: Cập nhật class CVATAPI

```python
class CVATAPI:
    def __init__(self, base_url: str, token: str, org_slug: str = None):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.org_slug = org_slug
        self.timeout = 30
    
    def _get_headers(self) -> Dict[str, str]:
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        if self.org_slug:
            headers["X-Organization"] = self.org_slug
        return headers

    def create_issue(self, job_id: int, frame: int, position: List[float],
                     message: str, assignee_id: int = None) -> Dict:
        """POST /api/issues - Tạo issue với position đúng"""
        url = f"{self.base_url}/issues"
        issue_data = {
            "frame": int(frame),
            "position": position,  # ⭐ CẬP NHẬT: Thêm position [x1,y1,x2,y2]
            "job": job_id,
            "message": message,
            "resolved": False
        }
        if assignee_id:
            issue_data["assignee"] = assignee_id
        try:
            response = requests.post(url, json=issue_data,
                                    headers=self._get_headers(), timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create issue: {e.response.text if hasattr(e, 'response') else ''}")
            raise

    def update_job_status(self, job_id: int, stage: str, state: str, assignee_id: int = None) -> Dict:
        """
        PATCH /api/jobs/{id} - Cập nhật job status
        CẬP NHẬT: Pass giữ nguyên stage=validation, Reject: stage=annotation, state=rejected
        """
        url = f"{self.base_url}/jobs/{job_id}"
        payload = {"stage": stage, "state": state}
        if assignee_id:
            payload["assignee"] = assignee_id
        try:
            response = requests.patch(url, json=payload,
                                     headers=self._get_headers(), timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise

    def get_job_annotations(self, job_id: int) -> Dict:
        """GET /api/jobs/{id}/annotations"""
        url = f"{self.base_url}/jobs/{job_id}/annotations"
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch annotations: {e}")
            raise

    def get_job_labels(self, job_id: int) -> Dict[int, str]:
        """GET /api/labels?job_id={id}"""
        url = f"{self.base_url}/labels?job_id={job_id}"
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=self.timeout)
            response.raise_for_status()
            results = response.json().get("results", [])
            return {item["id"]: item["name"] for item in results}
        except Exception as e:
            logger.error(f"Failed to fetch labels: {e}")
            return {}

    def get_job_info(self, job_id: int) -> Dict:
        """GET /api/jobs/{id}"""
        url = f"{self.base_url}/jobs/{job_id}"
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get job info: {e}")
            raise
```

**Thay đổi 3**: Cập nhật webhook endpoint

```python
@app.post("/webhook/cvat")
async def cvat_webhook(request: Request):
    # 1. Nhận payload
    payload = await request.json()
    logger.info(f"📥 Received webhook payload")
    
    if WEBHOOK_SECRET:
        secret = request.headers.get("X-CVAT-Webhook-Secret")
        if secret and secret != WEBHOOK_SECRET:
            raise HTTPException(status_code=401, detail="Invalid webhook secret")
    
    event = payload.get("event")
    if event == "ping":
        return {"message": "Ping received"}
    if event != "update:job":
        return {"message": f"Skipped event: {event}", "status": "skipped"}
    
    job = payload.get("job", {})
    job_id = job.get("id")
    status = job.get("status")
    assignee = job.get("assignee") or {}
    assignee_id = assignee.get("id")
    
    logger.info(f"🔔 Job Update: ID={job_id} | Status={status}")
    
    # Chỉ trigger khi status = validation
    if status != "validation":
        return {"message": f"Job {job_id} status update received", "job_id": job_id, "action": "none"}
    
    # Khởi tạo report
    report = QCReport(job_id=job_id)
    
    # Lấy annotations
    raw_data = cvat_api.get_job_annotations(job_id)
    report.total_annotations = len(raw_data.get('annotations', []))
    
    # Lấy label mapping
    labels_mapping = cvat_api.get_job_labels(job_id)
    
    # Parse
    frames = parse_cvat_api_json(raw_data, labels_mapping)
    report.total_frames = len(frames)
    
    # Chạy QC
    qc_engine = QCRulesEngine(
        min_box_area=MIN_BOX_AREA, iou_threshold=IOU_THRESHOLD,
        duplicate_iou_threshold=0.98, min_polygon_points=3,
        max_aspect_ratio=10.0, min_aspect_ratio=0.1,
        mask_tolerance=2.0, bbox_tolerance=2.0
    )
    errors = qc_engine.run_qc_check(frames)
    
    for error in errors:
        report.add_error(error["Error_Type"], error["Message"])
    
    # XỬ LÝ KẾT QUẢ
    if errors:
        # Có lỗi - Tạo issues cho TỪNG LỖI
        report.status = "failed"
        for error in errors:
            position = error.get("Position", [0, 0, 0, 0])
            message = error.get("Message", "Unknown error")
            frame_name = error.get("Frame", "0")
            try:
                cvat_api.create_issue(
                    job_id=job_id, frame=int(frame_name),
                    position=position, message=message, assignee_id=assignee_id
                )
                report.issues_created += 1
            except Exception as e:
                report.failed_issue_creations += 1
        
        # Cập nhật job status = REJECTED
        cvat_api.update_job_status(
            job_id=job_id, stage="annotation", state="rejected"
        )
        report.job_status_updated = "rejected"
        
        report_path = report.save()
        return {
            "message": f"QC failed - {len(errors)} errors",
            "job_id": job_id, "total_errors": len(errors),
            "error_types": report.get_error_type_counts(),
            "created_issues": report.issues_created,
            "action": "rejected", "report_path": report_path,
            "timestamp": datetime.now().isoformat()
        }
    else:
        # Không lỗi - QC passed
        report.status = "passed"
        # ⭐ CẬP NHẬT: Giữ nguyên stage=validation, không thay đổi state
        cvat_api.update_job_status(
            job_id=job_id, stage="validation", state=""
        )
        report.job_status_updated = "validation"
        
        report_path = report.save()
        return {
            "message": "QC passed", "job_id": job_id,
            "frames_checked": len(frames),
            "total_bboxes": sum(len(f.bboxes) for f in frames),
            "total_polygons": sum(len(f.polygons) for f in frames),
            "action": "passed", "report_path": report_path,
            "timestamp": datetime.now().isoformat()
        }
```

---

### 8. `src/reports.py` - ✨ FILE MỚI
**Mục đích**: Tóm tắt ngắn gọn các issue sau mỗi lượt QC run, lưu file JSON, giữ tối đa 5 report

```python
"""
QC Report - Tóm tắt ngắn gọn các issue sau mỗi lượt QC run
- Lưu file JSON
- Folder chỉ giữ tối đa 5 report
- File tóm tắt ngắn gọn, tối đa 50 dòng
"""
import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import os


class QCReport:
    """Lớp quản lý báo cáo QC"""
    
    def __init__(self, job_id: int, job_name: str = "unknown"):
        self.job_id = job_id
        self.job_name = job_name
        self.timestamp = datetime.now().isoformat()
        self.status = "pending"  # pending, passed, failed
        
        # Metrics cơ bản
        self.total_frames = 0
        self.total_annotations = 0
        self.errors: List[Dict] = []
        self.error_type_counts: Dict[str, int] = {}
        self.issues_created = 0
        self.failed_issue_creations = 0
        self.job_status_updated: Optional[str] = None
    
    def add_error(self, error_type: str, message: str):
        """Thêm lỗi vào báo cáo"""
        self.errors.append({
            "type": error_type,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        self.error_type_counts[error_type] = self.error_type_counts.get(error_type, 0) + 1
    
    def get_error_type_counts(self) -> Dict[str, int]:
        """Trả về đếm lỗi theo loại"""
        return self.error_type_counts
    
    def to_summary_dict(self) -> Dict:
        """
        Convert report to summary dictionary (ngắn gọn, tối đa 50 dòng)
        Chỉ bao gồm thông tin tóm tắt, không bao gồm full error details
        """
        return {
            "job_id": self.job_id,
            "job_name": self.job_name,
            "timestamp": self.timestamp,
            "status": self.status,
            "summary": {
                "total_frames": self.total_frames,
                "total_annotations": self.total_annotations,
                "total_errors": len(self.errors),
                "error_type_counts": self.error_type_counts,
                "issues_created": self.issues_created,
                "failed_issue_creations": self.failed_issue_creations,
                "job_status": self.job_status_updated
            }
        }
    
    def save(self, reports_dir: str = "reports") -> str:
        """
        Lưu báo cáo vào file JSON
        - Tạo thư mục nếu chưa có
        - Giữ tối đa 5 report (xóa các file cũ nhất)
        - Lưu file tóm tắt ngắn gọn
        """
        # Tạo thư mục
        Path(reports_dir).mkdir(parents=True, exist_ok=True)
        
        # Danh sách các file report hiện có
        existing_reports = sorted(
            Path(reports_dir).glob("report_job_*.json"),
            key=lambda p: p.stat().st_mtime
        )
        
        # Xóa các report cũ nhất nếu vượt quá 5
        while len(existing_reports) >= 5:
            oldest = existing_reports.pop(0)
            oldest.unlink()
        
        # Tạo tên file
        filename = f"report_job_{self.job_id}_{self.timestamp.replace(':', '-').replace('.', '-')}.json"
        filepath = Path(reports_dir) / filename
        
        # Lưu file tóm tắt
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_summary_dict(), f, indent=2, ensure_ascii=False)
        
        return str(filepath)
    
    @staticmethod
    def load(filepath: str) -> Optional['QCReport']:
        """Load report từ file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            report = QCReport(data["job_id"], data.get("job_name", "unknown"))
            report.timestamp = data["timestamp"]
            report.status = data["status"]
            report.total_frames = data["summary"].get("total_frames", 0)
            report.total_annotations = data["summary"].get("total_annotations", 0)
            report.error_type_counts = data["summary"].get("error_type_counts", {})
            report.issues_created = data["summary"].get("issues_created", 0)
            report.failed_issue_creations = data["summary"].get("failed_issue_creations", 0)
            report.job_status_updated = data["summary"].get("job_status")
            return report
        except Exception:
            return None
    
    @staticmethod
    def get_all_reports(reports_dir: str = "reports") -> List['QCReport']:
        """Lấy tất cả reports trong thư mục"""
        reports = []
        if Path(reports_dir).exists():
            for filepath in sorted(Path(reports_dir).glob("report_job_*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
                report = QCReport.load(str(filepath))
                if report:
                    reports.append(report)
        return reports

---

## 📊 Kế hoạch Triển khai theo Phase

### 🔴 PHASE 1: Core Infrastructure (1 ngày)
**Mục tiêu**: Hoàn thiện hệ thống cơ sở

| Task | File | Thời gian | Trạng thái |
|------|------|-----------|------------|
| Tạo config.py | `src/config.py` | 1g | ⬜ Todo |
| Tạo utils.py | `src/utils.py` | 1g | ⬜ Todo |
| Tạo error_templates.py | `src/error_templates.py` | 1g | ⬜ Todo |
| Cập nhật parser.py | `src/parser.py` | 1g | ⬜ Todo |
| Cập nhật CVATAPI class | `app.py` | 2g | ⬜ Todo |
| Cập nhật webhook endpoint | `app.py` | 2g | ⬜ Todo |
| **Test cơ bản** | - | 2g | ⬜ Todo |

**Deliverables**:
- ✅ Tất cả API calls có X-Organization header
- ✅ Issues với position [x1,y1,x2,y2] đúng
- ✅ Messages sinh bằng template
- ✅ Job status update: Reject → stage="annotation", state="rejected"; Pass → stage="validation" (không thay đổi state)

---

### 🟡 PHASE 2: Complete Rules Engine (1 ngày)
**Mục tiêu**: Implement tất cả rules Phase 1-3

| Task | File | Thời gian | Trạng thái |
|------|------|-----------|------------|
| Phase 1 rules | `src/rules.py` | 2g | ⬜ Todo |
| Phase 2 rules | `src/rules.py` | 3g | ⬜ Todo |
| Phase 3 rules | `src/rules.py` | 2g | ⬜ Todo |
| Error format | `src/rules.py` | 1g | ⬜ Todo |
| **Test rules** | - | 2g | ⬜ Todo |

**Deliverables**: 10 rules hoạt động, error payload đầy đủ (Severity, Suggestion, Details, Position)

---

### 🟢 PHASE 3: Reporting System (0.5 ngày)
**Mục tiêu**: Hệ thống báo cáo tóm tắt ngắn gọn

| Task | File | Thời gian | Trạng thái |
|------|------|-----------|------------|
| Tạo reports.py | `src/reports.py` | 2g | ⬜ Todo |
| Tích hợp webhook | `app.py` | 1g | ⬜ Todo |
| **Test báo cáo** | - | 1g | ⬜ Todo |

**Deliverables**:
- ✅ Reports lưu file JSON sau mỗi QC run
- ✅ Folder chỉ giữ tối đa 5 report (xóa cũ nhất)
- ✅ File tóm tắt ngắn gọn, tối đa 50 dòng
- ✅ Chỉ lưu summary (không lưu full error details)

---

### 📝 PHASE 4: Testing & Documentation (1 ngày)
**Mục tiêu**: Đảm bảo chất lượng

| Task | File | Thời gian | Trạng thái |
|------|------|-----------|------------|
| Unit tests | `tests/` | 4g | ⬜ Todo |
| Cập nhật README | `README.md` | 1g | ⬜ Todo |
| **Integration test** | - | 2g | ⬜ Todo |

**Deliverables**: Unit tests, integration tests, tài liệu hoàn chỉnh

---

## 📅 Timeline Tổng thể

| Phase | Thời gian | Mục tiêu |
|-------|----------|----------|
| Phase 1 | Ngày 1 | Core Infrastructure |
| Phase 2 | Ngày 2 | Complete Rules Engine |
| Phase 3 | Nửa ngày 3 | Reporting System |
| Phase 4 | Nửa ngày 4 | Testing & Documentation |
| **Total** | **4 ngày** | Hoàn thiện |

---

## ✅ Success Criteria

### Technical
- [ ] Tất cả CVAT API calls có X-Organization header
- [ ] Issues với position [x1,y1,x2,y2] đúng theo bảng quy định
- [ ] Messages sinh bằng template (Severity, Suggestion, Details)
- [ ] 10 rules (Phase 1-3) hoạt động
- [ ] Job status update: Reject → stage="annotation", state="rejected"; Pass → stage="validation" (không đổi state)
- [ ] Reports lưu file JSON, folder max 5 reports

### Quality
- [ ] Code clean, well-documented
- [ ] Unit tests coverage > 80%
- [ ] No false positives trên clean data
- [ ] Detection rate > 95% trên test data
- [ ] Latency < 2 giây

---

## 📌 Checklist Trước Triển khai

- [ ] CVAT_TOKEN set trong .env
- [ ] CVAT_ORG_SLUG set (nếu dùng organization)
- [ ] WEBHOOK_SECRET set (optional)
- [ ] Webhook đăng ký trên CVAT trỏ đến `/webhook/cvat`
- [ ] Token có quyền Maintainer/Owner/Reviewer
- [ ] Test với mock data
- [ ] Test với real CVAT data

---

## 📚 Tài liệu Tham khảo

1. [CVAT_API_ENDPOINT.md](./CVAT_API_ENDPOINT.md)
2. [QC_RULE_BASED_IMPLEMENTATION.md](./QC_RULE_BASED_IMPLEMENTATION.md)
3. [TODO.md](../TODO.md)

---

*Kế hoạch triển khai cho hệ thống LetmeQC - QC Rule-Based Pipeline*
```
```
