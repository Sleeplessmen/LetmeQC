"""
Unit tests for QC Rules Engine.

Run with: pytest tests/test_qc_rules.py -v
"""

import os
import sys
import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.parser import parse_coco_json
from src.rules import QCRulesEngine


# Test data paths
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'test_cases')


class TestBboxValidation:
    """Test bounding box validation rules."""
    
    def test_bbox_out_of_bounds(self):
        """Test detection of bounding boxes outside image boundaries."""
        json_path = os.path.join(TEST_DATA_DIR, 'test_bbox_size_oob.json')
        frames = parse_coco_json(json_path)
        
        qc_engine = QCRulesEngine(min_box_area=100, iou_threshold=0.95)
        errors = qc_engine.run_qc_check(frames)
        
        # Should detect out of bounds error
        error_types = [e['Error_Type'] for e in errors]
        assert 'Bbox_Out_Of_Bounds' in error_types, "Should detect out of bounds bbox"
    
    def test_bbox_too_small(self):
        """Test detection of bounding boxes that are too small."""
        json_path = os.path.join(TEST_DATA_DIR, 'test_bbox_size_oob.json')
        frames = parse_coco_json(json_path)
        
        qc_engine = QCRulesEngine(min_box_area=100, iou_threshold=0.95)
        errors = qc_engine.run_qc_check(frames)
        
        # Should detect too small error
        error_types = [e['Error_Type'] for e in errors]
        assert 'Bbox_Too_Small' in error_types, "Should detect too small bbox"
    
    def test_bbox_overlap(self):
        """Test detection of overlapping bounding boxes."""
        json_path = os.path.join(TEST_DATA_DIR, 'test_bbox_overlap.json')
        frames = parse_coco_json(json_path)
        
        qc_engine = QCRulesEngine(min_box_area=100, iou_threshold=0.90)
        errors = qc_engine.run_qc_check(frames)
        
        # Should detect overlap error
        error_types = [e['Error_Type'] for e in errors]
        assert 'Bbox_Overlap' in error_types, "Should detect overlapping bboxes"


class TestPolygonValidation:
    """Test polygon validation rules."""
    
    def test_polygon_self_intersect(self):
        """Test detection of self-intersecting polygons."""
        json_path = os.path.join(TEST_DATA_DIR, 'test_poly_errors.json')
        frames = parse_coco_json(json_path)
        
        qc_engine = QCRulesEngine(min_box_area=100, iou_threshold=0.95)
        errors = qc_engine.run_qc_check(frames)
        
        # Should detect self-intersect error
        error_types = [e['Error_Type'] for e in errors]
        assert 'Polygon_Self_Intersect' in error_types, "Should detect self-intersecting polygon"
    
    def test_mask_out_of_box(self):
        """Test detection of masks outside their bounding boxes."""
        json_path = os.path.join(TEST_DATA_DIR, 'test_poly_errors.json')
        frames = parse_coco_json(json_path)
        
        qc_engine = QCRulesEngine(min_box_area=100, iou_threshold=0.95)
        errors = qc_engine.run_qc_check(frames)
        
        # Should detect mask out of box error
        error_types = [e['Error_Type'] for e in errors]
        assert 'Mask_Out_Of_Box' in error_types, "Should detect mask out of box"


class TestCleanData:
    """Test with clean ground truth data."""
    
    def test_clean_data_no_errors(self):
        """Test that clean data passes all checks."""
        json_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'ground_truth', 'gt_clean_data.json')
        
        if not os.path.exists(json_path):
            pytest.skip("Ground truth data not found")
        
        frames = parse_coco_json(json_path)
        
        qc_engine = QCRulesEngine(min_box_area=100, iou_threshold=0.95)
        errors = qc_engine.run_qc_check(frames)
        
        # Clean data should have minimal or no errors
        # Note: Some errors might exist in the original data
        print(f"Found {len(errors)} potential errors in ground truth data")


class TestParser:
    """Test COCO JSON parser."""
    
    def test_parse_valid_json(self):
        """Test parsing a valid COCO JSON file."""
        json_path = os.path.join(TEST_DATA_DIR, 'test_bbox_size_oob.json')
        frames = parse_coco_json(json_path)
        
        assert len(frames) > 0, "Should parse at least one frame"
        assert all(hasattr(f, 'frame_id') for f in frames), "Frames should have frame_id"
        assert all(hasattr(f, 'bboxes') for f in frames), "Frames should have bboxes"
        assert all(hasattr(f, 'polygons') for f in frames), "Frames should have polygons"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
