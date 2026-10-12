"""
LetmeQC - A Quality Control Tool for COCO Format Annotations

This package provides tools for parsing and validating COCO format annotation files,
particularly for computer vision tasks like object detection and segmentation.
"""

from .models import Bbox, Polygon, Frame, FrameTag
from .parser import parse_coco_json
from .rules import QCRulesEngine

__version__ = "0.1.0"
__all__ = ["Bbox", "Polygon", "Frame", "FrameTag", "parse_coco_json", "QCRulesEngine"]
