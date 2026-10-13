from .models import Frame, Bbox, Polygon, FrameTag
from typing import List, Dict


def parse_cvat_api_json(raw_data: dict, labels_mapping: Dict[int, str]) -> List[Frame]:
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
