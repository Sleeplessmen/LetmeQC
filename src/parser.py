from .models import Frame, Bbox, Polygon, FrameTag
from typing import List, Dict


def parse_cvat_api_json(raw_data: dict, labels_mapping: Dict[int, str]) -> List[Frame]:
    """
    Parse dữ liệu JSON RAW trực tiếp từ API: /api/jobs/{id}/annotations
    Hỗ trợ cả 2 định dạng:
    - Shapes (cho image annotation)
    - Tracks (cho video annotation)
    
    labels_mapping: Dictionary map từ label_id (int) -> label_name (str)
    """
    frames_dict = {}
    default_width, default_height = 1280, 720
    
    # Lấy kích thước default từ metadata nếu có
    if 'meta' in raw_data and 'size' in raw_data.get('meta', {}):
        meta = raw_data['meta']['size']
        default_width = int(meta.get('width', default_width))
        default_height = int(meta.get('height', default_height))
    
    # Lấy metadata cho từng frame nếu có
    frames_meta = {}
    if 'meta' in raw_data and 'frames' in raw_data.get('meta', {}):
        for frame_info in raw_data['meta']['frames']:
            frame_idx = frame_info.get('index')
            if frame_idx is not None:
                frames_meta[str(frame_idx)] = frame_info
    
    # Hàm hỗ trợ khởi tạo Frame nếu chưa tồn tại
    def get_or_create_frame(frame_idx: int, frame_name: str = None):
        frame_key = frame_idx
        if frame_key not in frames_dict:
            # Lấy metadata của frame
            frame_meta = frames_meta.get(str(frame_idx), {})
            actual_width = int(frame_meta.get('width', default_width))
            actual_height = int(frame_meta.get('height', default_height))
            
            # Dùng tên frame từ metadata nếu có, không thì dùng name parameter, không thì dùng index
            actual_name = (frame_name or 
                          frame_meta.get('name') or 
                          str(frame_idx))
            
            frames_dict[frame_key] = Frame(
                frame_id=frame_idx,
                width=actual_width,
                height=actual_height,
                name=actual_name
            )
        return frames_dict[frame_key]

    # Helper function to parse a single shape
    def parse_shape(shape: dict, frame_idx: int, frame_name: str = None):
        """Parse a single shape and add to the appropriate frame"""
        label_id = shape.get('label_id')
        label_name = labels_mapping.get(label_id, f"label_{label_id}")
        shape_type = shape.get('type')
        points = shape.get('points', [])
        
        # Parse attributes
        attrs = {str(attr['spec_id']): attr['value'] for attr in shape.get('attributes', [])}
        
        # Get frame name from shape if available
        shape_frame_name = frame_name or shape.get('frame_name') or shape.get('name')
        frame_obj = get_or_create_frame(frame_idx, shape_frame_name)
        
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
            
        elif shape_type in ('polygon', 'polyline') and len(points) >= 6:
            points_list = [(points[i], points[i+1]) for i in range(0, len(points), 2)]
            frame_obj.polygons.append(Polygon(
                id=shape.get('id'),
                label=label_name,
                points=points_list,
                attributes=attrs
            ))

    # Parse Shapes (cho image annotation)
    for shape in raw_data.get('shapes', []):
        frame_idx = shape.get('frame', 0)
        parse_shape(shape, frame_idx)
    
    # Parse Tracks (cho video annotation)
    for track in raw_data.get('tracks', []):
        for shape in track.get('shapes', []):
            frame_idx = shape.get('frame', 0)
            parse_shape(shape, frame_idx)

    # Parse Frame Tags (Thuộc tính toàn ảnh)
    for tag in raw_data.get('tags', []):
        frame_idx = tag.get('frame', 0)
        frame_name = tag.get('frame_name') or tag.get('name')
        frame_obj = get_or_create_frame(frame_idx, frame_name)
        label_id = tag.get('label_id')
        label_name = labels_mapping.get(label_id, f"tag_{label_id}")
        attrs = {str(attr['spec_id']): attr['value'] for attr in tag.get('attributes', [])}
        
        frame_obj.tags.append(FrameTag(label=label_name, attributes=attrs))

    return list(frames_dict.values())
