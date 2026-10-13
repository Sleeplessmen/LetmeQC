import json
from .models import Frame, Bbox, Polygon, FrameTag
from typing import List, Dict


def parse_coco_json(json_path: str) -> List[Frame]:
    with open(json_path, 'r', encoding='utf-8') as f:
        coco_data = json.load(f)
        
    # 1. Tạo từ điển mapping Category ID -> Tên Label
    categories = {cat['id']: cat['name'] for cat in coco_data.get('categories', [])}
    
    # 2. Khởi tạo danh sách các Frame (từ mảng images)
    frames_dict = {}
    for img in coco_data.get('images', []):
        frame_id = img.get('id')
        frames_dict[frame_id] = Frame(
            frame_id=frame_id,
            width=img.get('width', 1280),
            height=img.get('height', 720),
            name=img.get('file_name', 'unknown')
        )
        
    # 3. Đọc annotations và phân bổ về đúng Frame
    for ann in coco_data.get('annotations', []):
        image_id = ann.get('image_id')
        if image_id not in frames_dict:
            continue
            
        frame_obj = frames_dict[image_id]
        label = categories.get(ann.get('category_id'), "unknown")
        
        # Lấy attributes nếu CVAT có export ra
        attributes = ann.get('attributes', {})
        
        # Phân loại Segmentation (Polygon) hay Bbox
        segmentation = ann.get('segmentation', [])
        
        if segmentation and isinstance(segmentation, list) and len(segmentation) > 0 and isinstance(segmentation[0], list):
            # Polygon: COCO lưu dạng [[x1, y1, x2, y2, ...]]
            for poly_pts in segmentation:
                if len(poly_pts) >= 6:  # Ít nhất 3 điểm (tam giác)
                    points_list = [(poly_pts[i], poly_pts[i+1]) for i in range(0, len(poly_pts), 2)]
                    frame_obj.polygons.append(Polygon(
                        id=ann.get('id'),
                        label=label,
                        points=points_list,
                        attributes=attributes
                    ))
        if 'bbox' in ann:
            # Bbox: COCO lưu dạng [x_min, y_min, width, height]
            x, y, w, h = ann['bbox']
            frame_obj.bboxes.append(Bbox(
                id=ann.get('id'),
                label=label,
                xtl=float(x),
                ytl=float(y),
                xbr=float(x + w),
                ybr=float(y + h),
                attributes=attributes
            ))

    # Trả về danh sách các object Frame
    return list(frames_dict.values())


def parse_cvat_api_json(raw_data: dict, labels_mapping: dict) -> List[Frame]:
    """
    Parse dữ liệu JSON RAW trực tiếp từ API: /api/jobs/{id}/annotations
    labels_mapping: Dictionary map từ label_id (int) -> label_name (str)
    """
    frames_dict = {}
    
    # Hàm hỗ trợ khởi tạo Frame nếu chưa tồn tại
    def get_or_create_frame(frame_idx: int):
        if frame_idx not in frames_dict:
            frames_dict[frame_idx] = Frame(
                frame_id=frame_idx,
                width=1280,  # Lưu ý: Cần kích thước thật nếu rules OOB của bạn chặt
                height=720,
                name=str(frame_idx) # Đặt name chính là ID để lúc tạo Issue ko bị lỗi
            )
        return frames_dict[frame_idx]

    # Parse Shapes (Bbox và Polygon)
    for shape in raw_data.get('shapes', []):
        frame_idx = shape.get('frame', 0)
        frame_obj = get_or_create_frame(frame_idx)
        
        label_id = shape.get('label_id')
        label_name = labels_mapping.get(label_id, f"label_{label_id}")
        shape_type = shape.get('type')
        points = shape.get('points', [])
        
        # Parse thuộc tính (attributes)
        attrs = {str(attr['spec_id']): attr['value'] for attr in shape.get('attributes', [])}
        
        if shape_type == 'rectangle' and len(points) >= 4:
            frame_obj.bboxes.append(Bbox(
                id=shape.get('id'),
                label=label_name,
                xtl=float(points[0]),
                ytl=float(points[1]),
                xbr=float(points[2]),
                ybr=float(points[3]),
                attributes=attrs
            ))
            
        elif shape_type == 'polygon' and len(points) >= 6:
            points_list = [(points[i], points[i+1]) for i in range(0, len(points), 2)]
            frame_obj.polygons.append(Polygon(
                id=shape.get('id'),
                label=label_name,
                points=points_list,
                attributes=attrs
            ))

    # Parse Frame Tags (Thuộc tính toàn ảnh)
    for tag in raw_data.get('tags', []):
        frame_idx = tag.get('frame', 0)
        frame_obj = get_or_create_frame(frame_idx)
        label_id = tag.get('label_id')
        label_name = labels_mapping.get(label_id, f"tag_{label_id}")
        attrs = {str(attr['spec_id']): attr['value'] for attr in tag.get('attributes', [])}
        
        frame_obj.tags.append(FrameTag(label=label_name, attributes=attrs))

    return list(frames_dict.values())


# --- TEST THỬ TÍCH HỢP PARSER VÀ RULES ---
if __name__ == "__main__":
    from rules import QCRulesEngine
    import json
    
    # 1. Trỏ đến file COCO export từ CVAT
    # test_json_file = "../data/ground_truth/gt_clean_data.json" 
    test_json_file = "../data/test_cases/test_poly_errors.json" 

    
    print("Đang đọc dữ liệu...")
    parsed_frames = parse_coco_json(test_json_file)
    print(f"Đã đọc thành công {len(parsed_frames)} frames.")
    
    print("\nĐang chạy QC Check...")
    qc_engine = QCRulesEngine(min_box_area=100, iou_threshold=0.90)
    errors = qc_engine.run_qc_check(parsed_frames)
    
    if len(errors) == 0:
        print("✅ TUYỆT VỜI! Dữ liệu Ground Truth của bạn hoàn toàn sạch, không có lỗi.")
    else:
        print(f"❌ Phát hiện {len(errors)} lỗi:")
        print(json.dumps(errors, indent=4, ensure_ascii=False))
