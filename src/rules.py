"""QC Rules Engine - Implement tất cả rules Phase 1-3"""
from .models import Frame, Bbox, Polygon
from .error_templates import generate_error_payload
from .utils import calculate_iou, calculate_intersection_box, get_bbox_from_points, clamp_to_image, calculate_aspect_ratio
from typing import List, Dict, Any, Tuple, Optional
from shapely.geometry import Polygon as ShapelyPoly


class QCRulesEngine:
    """QC Rules Engine with comprehensive checks for Phase 1-3"""
    
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
        """Run QC checks on all frames and return list of errors"""
        all_errors = []
        for frame in frames:
            errors = self._check_single_frame(frame)
            if errors:
                all_errors.extend(errors)
        return all_errors

    def _check_single_frame(self, frame: Frame) -> List[Dict[str, Any]]:
        """Check a single frame with all Phase 1-3 rules"""
        errors = []
        
        # Phase 1: Critical checks
        errors.extend(self._check_bbox_out_of_bounds(frame))
        errors.extend(self._check_bbox_too_small(frame))
        errors.extend(self._check_polygon_point_count(frame))
        
        # Phase 2: Geometry & Logic checks
        errors.extend(self._check_overlapping_bboxes(frame))
        errors.extend(self._check_self_intersecting_polygons(frame))
        errors.extend(self._check_duplicate_objects(frame))
        
        # Phase 3: Advanced checks
        errors.extend(self._check_mask_out_of_bbox(frame))
        errors.extend(self._check_extreme_aspect_ratio(frame))
        errors.extend(self._check_label_consistency(frame))
        
        return errors

    # ==================== PHASE 1: CRITICAL CHECKS ====================
    
    def _check_bbox_out_of_bounds(self, frame: Frame) -> List[Dict]:
        """Check if bounding boxes are outside frame boundaries"""
        errors = []
        for box in frame.bboxes:
            is_out = (
                box.xtl < -self.bbox_tolerance or 
                box.ytl < -self.bbox_tolerance or
                box.xbr > frame.width + self.bbox_tolerance or 
                box.ybr > frame.height + self.bbox_tolerance
            )
            if is_out:
                position = clamp_to_image(
                    (box.xtl, box.ytl, box.xbr, box.ybr), 
                    frame.width, 
                    frame.height
                )
                errors.append(generate_error_payload(
                    frame.name, box.id, "Bbox_Out_Of_Bounds", list(position),
                    img_w=frame.width, img_h=frame.height, label=box.label,
                    bounds=[box.xtl, box.ytl, box.xbr, box.ybr]
                ))
        return errors

    def _check_bbox_too_small(self, frame: Frame) -> List[Dict]:
        """Check if bounding boxes are smaller than minimum allowed area"""
        errors = []
        for box in frame.bboxes:
            area = (box.xbr - box.xtl) * (box.ybr - box.ytl)
            if area < self.min_box_area:
                errors.append(generate_error_payload(
                    frame.name, box.id, "Bbox_Too_Small", 
                    [box.xtl, box.ytl, box.xbr, box.ybr],
                    area=area, min_area=self.min_box_area, label=box.label
                ))
        return errors

    def _check_polygon_point_count(self, frame: Frame) -> List[Dict]:
        """Check if polygons have minimum required points"""
        errors = []
        for poly in frame.polygons:
            if len(poly.points) < self.min_polygon_points:
                position = get_bbox_from_points(poly.points)
                errors.append(generate_error_payload(
                    frame.name, poly.id, "Polygon_Point_Count", list(position),
                    point_count=len(poly.points), 
                    min_points=self.min_polygon_points, 
                    label=poly.label
                ))
        return errors

    # ==================== PHASE 2: GEOMETRY & LOGIC CHECKS ====================

    def _check_overlapping_bboxes(self, frame: Frame) -> List[Dict]:
        """Check for overlapping bounding boxes of the same class"""
        errors = []
        label_groups = {}
        
        # Group bboxes by label
        for box in frame.bboxes:
            label_groups.setdefault(box.label, []).append(box)
        
        # Check overlaps within each label group
        for label, group in label_groups.items():
            if len(group) < 2:
                continue
            
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    box1, box2 = group[i], group[j]
                    iou = calculate_iou(
                        (box1.xtl, box1.ytl, box1.xbr, box1.ybr),
                        (box2.xtl, box2.ytl, box2.xbr, box2.ybr)
                    )
                    if iou > self.iou_threshold:
                        intersection = calculate_intersection_box(
                            (box1.xtl, box1.ytl, box1.xbr, box1.ybr),
                            (box2.xtl, box2.ytl, box2.xbr, box2.ybr)
                        )
                        position = list(intersection) if intersection else [box2.xtl, box2.ytl, box2.xbr, box2.ybr]
                        errors.append(generate_error_payload(
                            frame.name, 
                            f"{box1.id} & {box2.id}", 
                            "Bbox_Overlap", 
                            position,
                            count=2, 
                            label=label, 
                            obj_ids=f"{box1.id} & {box2.id}", 
                            iou=iou
                        ))
        return errors

    def _check_self_intersecting_polygons(self, frame: Frame) -> List[Dict]:
        """Check for self-intersecting polygons"""
        errors = []
        for poly in frame.polygons:
            if len(poly.points) < 3:
                continue
            try:
                shapely_poly = ShapelyPoly(poly.points)
                if not shapely_poly.is_valid:
                    position = get_bbox_from_points(poly.points)
                    errors.append(generate_error_payload(
                        frame.name, poly.id, "Polygon_Self_Intersect", list(position), 
                        label=poly.label
                    ))
            except Exception:
                continue
        return errors

    def _check_duplicate_objects(self, frame: Frame) -> List[Dict]:
        """Check for duplicate objects with same label and attributes"""
        errors = []
        label_groups = {}
        
        # Group bboxes by label
        for box in frame.bboxes:
            label_groups.setdefault(box.label, []).append(box)
        
        # Check for duplicates within each label group
        for label, group in label_groups.items():
            if len(group) < 2:
                continue
            
            checked = set()
            for i in range(len(group)):
                if i in checked:
                    continue
                for j in range(i + 1, len(group)):
                    box1, box2 = group[i], group[j]
                    iou = calculate_iou(
                        (box1.xtl, box1.ytl, box1.xbr, box1.ybr),
                        (box2.xtl, box2.ytl, box2.xbr, box2.ybr)
                    )
                    # Check if boxes have same attributes and high IoU
                    if iou >= self.duplicate_iou_threshold and box1.attributes == box2.attributes:
                        errors.append(generate_error_payload(
                            frame.name, 
                            f"{box1.id} & {box2.id}", 
                            "Duplicate_Objects",
                            [box2.xtl, box2.ytl, box2.xbr, box2.ybr],
                            obj_ids=f"{box1.id} & {box2.id}", 
                            label=label, 
                            iou=iou
                        ))
                        checked.add(j)
        return errors

    # ==================== PHASE 3: ADVANCED CHECKS ====================

    def _check_mask_out_of_bbox(self, frame: Frame) -> List[Dict]:
        """Check if polygon mask extends beyond its bounding box"""
        errors = []
        for poly in frame.polygons:
            if len(poly.points) < 3:
                continue
            
            # Find matching bbox with same ID
            matching_box = next((b for b in frame.bboxes if b.id == poly.id), None)
            if not matching_box:
                continue
            
            try:
                shapely_poly = ShapelyPoly(poly.points)
                min_x, min_y, max_x, max_y = shapely_poly.bounds
                
                is_out = (
                    min_x < matching_box.xtl - self.mask_tolerance or
                    min_y < matching_box.ytl - self.mask_tolerance or
                    max_x > matching_box.xbr + self.mask_tolerance or
                    max_y > matching_box.ybr + self.mask_tolerance
                )
                
                if is_out:
                    errors.append(generate_error_payload(
                        frame.name, poly.id, "Mask_Out_Of_Box", 
                        [min_x, min_y, max_x, max_y],
                        label=poly.label, 
                        tolerance=self.mask_tolerance
                    ))
            except Exception:
                continue
        return errors

    def _check_extreme_aspect_ratio(self, frame: Frame) -> List[Dict]:
        """Check for bounding boxes with extreme aspect ratios"""
        errors = []
        for box in frame.bboxes:
            ratio = calculate_aspect_ratio((box.xtl, box.ytl, box.xbr, box.ybr))
            if ratio > self.max_aspect_ratio or ratio < self.min_aspect_ratio:
                errors.append(generate_error_payload(
                    frame.name, box.id, "Extreme_Aspect_Ratio",
                    [box.xtl, box.ytl, box.xbr, box.ybr],
                    ratio=ratio, label=box.label
                ))
        return errors

    def _check_label_consistency(self, frame: Frame) -> List[Dict]:
        """Check for label consistency (e.g., pedestrian inside car)"""
        errors = []
        
        # Define label hierarchy: child labels should not be inside parent labels
        label_hierarchy = {
            "pedestrian": ["car", "truck", "bus"],
            "person": ["car", "truck", "bus"]
        }
        
        for child_label, parent_labels in label_hierarchy.items():
            child_boxes = [b for b in frame.bboxes if b.label == child_label]
            
            for child in child_boxes:
                child_box = (child.xtl, child.ytl, child.xbr, child.ybr)
                for parent_label in parent_labels:
                    parent_boxes = [b for b in frame.bboxes 
                                   if b.label == parent_label and b.id != child.id]
                    for parent in parent_boxes:
                        parent_box = (parent.xtl, parent.ytl, parent.xbr, parent.ybr)
                        iou = calculate_iou(child_box, parent_box)
                        if iou > 0.95:
                            errors.append(generate_error_payload(
                                frame.name, child.id, "Label_Consistency",
                                [child.xtl, child.ytl, child.xbr, child.ybr],
                                child_label=child_label, 
                                parent_label=parent_label
                            ))
        return errors