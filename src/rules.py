from .models import Frame, Bbox
from typing import List, Dict
from shapely.geometry import Polygon as ShapelyPoly

class QCRulesEngine:
    def __init__(self, min_box_area=100, iou_threshold=0.95):
        self.min_box_area = min_box_area
        self.iou_threshold = iou_threshold
        
        # Cấu hình rule attributes (Ví dụ: Frame bắt buộc phải có Tag weather)
        self.required_frame_tags = ["weather"]
        # Cấu hình rule attributes cho Object (Ví dụ: class car bắt buộc có type, nếu bạn có setup)
        self.required_obj_attrs = {
            "car": [], 
            "pedestrian": []
        }

    def run_qc_check(self, frames: List[Frame]) -> List[Dict]:
        """Chạy kiểm tra trên toàn bộ frames và trả về danh sách lỗi."""
        all_errors = []
        for frame in frames:
            errors = self._check_single_frame(frame)
            if errors:
                all_errors.extend(errors)
        return all_errors

    def _check_single_frame(self, frame: Frame) -> List[Dict]:
        frame_errors = []

        # 1. Check bbox bounds and size
        frame_errors.extend(self._check_bbox_bounds(frame))
        frame_errors.extend(self._check_bbox_sizes(frame))

        # 2. Check overlapping bboxes
        frame_errors.extend(self._check_overlapping_bboxes(frame))

        # 3. Check polygons
        frame_errors.extend(self._check_polygons(frame))

        # 4. Check attributes
        frame_errors.extend(self._check_required_frame_attributes(frame))
        frame_errors.extend(self._check_required_object_attributes(frame))

        return frame_errors

    def _check_bbox_bounds(self, frame: Frame) -> List[Dict]:
        errors = []
        for box in frame.bboxes:
            is_out_of_bounds = (
                box.xtl < -2 or 
                box.ytl < -2 or 
                box.xbr > frame.width + 2 or 
                box.ybr > frame.height + 2
            )
            if is_out_of_bounds:
                errors.append(self._format_error(
                    frame.name, box.id, "Bbox_Out_Of_Bounds",
                    f"Box vượt quá kích thước ảnh ({frame.width}x{frame.height})"
                ))
        return errors

    def _check_bbox_sizes(self, frame: Frame) -> List[Dict]:
        errors = []
        for box in frame.bboxes:
            area = (box.xbr - box.xtl) * (box.ybr - box.ytl)
            if area < self.min_box_area:
                errors.append(self._format_error(
                    frame.name, box.id, "Bbox_Too_Small",
                    f"Diện tích box ({area:.1f}px) nhỏ hơn mức cho phép ({self.min_box_area}px)"
                ))
        return errors

    def _check_overlapping_bboxes(self, frame: Frame) -> List[Dict]:
        errors = []
        bboxes = frame.bboxes
        for i in range(len(bboxes)):
            for j in range(i + 1, len(bboxes)):
                box1 = bboxes[i]
                box2 = bboxes[j]
                if box1.label == box2.label:
                    iou = self._calculate_iou(box1, box2)
                    if iou > self.iou_threshold:
                        errors.append(self._format_error(
                            frame.name, f"{box1.id} & {box2.id}", "Bbox_Overlap",
                            f"Hai box class '{box1.label}' trùng lặp quá mức (IoU: {iou:.2f})"
                        ))
        return errors

    def _check_polygons(self, frame: Frame) -> List[Dict]:
        errors = []
        tolerance = 2.0
        for poly in frame.polygons:
            if len(poly.points) < 3:
                continue
            errors.extend(self._check_single_polygon(frame, poly, tolerance))
        return errors

    def _check_single_polygon(self, frame: Frame, poly: any, tolerance: float) -> List[Dict]:
        errors = []
        try:
            shapely_poly = ShapelyPoly(poly.points)
            if not shapely_poly.is_valid:
                errors.append(self._format_error(
                    frame.name, poly.id, "Polygon_Self_Intersect",
                    f"Polygon của class '{poly.label}' bị vặn chéo hoặc tự cắt các cạnh."
                ))
            matching_box = self._find_matching_bbox(frame, poly)
            if matching_box:
                errors.extend(self._check_polygon_mask_in_box(frame, poly, matching_box, shapely_poly, tolerance))
        except Exception as e:
            errors.append(self._format_error(
                frame.name, poly.id, "Polygon_Error",
                f"Lỗi tính toán hình học: {e}"
            ))
        return errors

    def _find_matching_bbox(self, frame: Frame, poly: any) -> any:
        return next((b for b in frame.bboxes if b.id == poly.id), None)

    def _check_polygon_mask_in_box(self, frame: Frame, poly: any, box: Bbox, shapely_poly: any, tolerance: float) -> List[Dict]:
        errors = []
        min_x, min_y, max_x, max_y = shapely_poly.bounds
        is_out_of_box = (
            min_x < box.xtl - tolerance or
            min_y < box.ytl - tolerance or
            max_x > box.xbr + tolerance or
            max_y > box.ybr + tolerance
        )
        if is_out_of_box:
            errors.append(self._format_error(
                frame.name, poly.id, "Mask_Out_Of_Box",
                f"Mask '{poly.label}' bị tràn ra ngoài Bounding Box tương ứng."
            ))
        return errors

    def _check_required_frame_attributes(self, frame: Frame) -> List[Dict]:
        errors = []
        frame_attr_keys = []
        for tag in frame.tags:
            frame_attr_keys.extend(tag.attributes.keys())
        for req_tag in self.required_frame_tags:
            if req_tag not in frame_attr_keys:
                errors.append(self._format_error(
                    frame.name, "Frame_Level", "Missing_Attribute",
                    f"Frame thiếu tag/thuộc tính bắt buộc: '{req_tag}'"
                ))
        return errors

    def _check_required_object_attributes(self, frame: Frame) -> List[Dict]:
        errors = []
        all_objects = frame.bboxes + frame.polygons
        for obj in all_objects:
            req_attrs = self.required_obj_attrs.get(obj.label, [])
            for attr in req_attrs:
                if attr not in obj.attributes:
                    errors.append(self._format_error(
                        frame.name, obj.id, "Missing_Attribute",
                        f"Object '{obj.label}' thiếu thuộc tính bắt buộc: '{attr}'"
                    ))
        return errors

    @staticmethod
    def _calculate_iou(box1: Bbox, box2: Bbox) -> float:
        """Thuật toán tính độ giao nhau (IoU) giữa 2 hình chữ nhật."""
        x_left = max(box1.xtl, box2.xtl)
        y_top = max(box1.ytl, box2.ytl)
        x_right = min(box1.xbr, box2.xbr)
        y_bottom = min(box1.ybr, box2.ybr)

        if x_right < x_left or y_bottom < y_top:
            return 0.0

        intersection_area = (x_right - x_left) * (y_bottom - y_top)
        box1_area = (box1.xbr - box1.xtl) * (box1.ybr - box1.ytl)
        box2_area = (box2.xbr - box2.xtl) * (box2.ybr - box2.ytl)
        union_area = box1_area + box2_area - intersection_area

        return intersection_area / union_area if union_area > 0 else 0

    @staticmethod
    def _format_error(frame_name: str, obj_id: any, error_type: str, message: str) -> Dict:
        return {
            "Frame": frame_name,
            "Object_ID": obj_id,
            "Error_Type": error_type,
            "Message": message
        }