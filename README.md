# LetmeQC - COCO Annotation Quality Control Tool

A Python tool for validating and quality-checking COCO format annotation files, particularly for computer vision tasks like object detection and segmentation.

## Features

- ✅ **Bounding Box Validation**
  - Out of bounds detection
  - Minimum size validation
  - Overlap detection (IoU-based)
  
- ✅ **Polygon/Segmentation Validation**
  - Self-intersection detection
  - Mask out of bounding box detection
  
- ✅ **COCO Format Support**
  - Parse COCO JSON annotations
  - Support for bbox, polygon, and attributes

## Project Structure

```
LetmeQC/
├── README.md              # This file
├── GUIDELINE.md           # Project guidelines
├── requirements.txt       # Python dependencies
├── pyproject.toml        # Project configuration (optional)
├── src/
│   ├── __init__.py        # Package initialization
│   ├── main.py            # CLI entry point
│   ├── models.py          # Data models (Bbox, Polygon, Frame)
│   ├── parser.py          # COCO JSON parser
│   └── rules.py           # Quality check rules engine
├── data/
│   ├── cvat_exports/      # Original CVAT exports
│   ├── ground_truth/      # Ground truth data
│   ├── poc_images/        # Sample images
│   └── test_cases/        # Test cases for QC validation
└── venv/                  # Python virtual environment
```

## Quick Start

### Prerequisites

- Python 3.10+
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd LetmeQC
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment**
   - **Windows (CMD/PowerShell):**
     ```bash
     .\venv\Scripts\activate
     ```
   - **Linux/Mac:**
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Verify installation**
   ```bash
   python -c "from src import parse_coco_json, QCRulesEngine; print('✓ Installation successful')"
   ```

## Usage

### Command Line Interface

```bash
# Run QC check on a COCO JSON file
python src/main.py data/ground_truth/gt_clean_data.json

# With custom parameters
python src/main.py data/test_cases/test_poly_errors.json \
    --min-area 50 \
    --iou-threshold 0.85 \
    --output errors.json

# Show help
python src/main.py --help
```

### Programmatic Usage

```python
from src.parser import parse_coco_json
from src.rules import QCRulesEngine

# Parse COCO JSON
frames = parse_coco_json("path/to/annotations.json")

# Run QC checks
qc_engine = QCRulesEngine(
    min_box_area=100,
    iou_threshold=0.95
)
errors = qc_engine.run_qc_check(frames)

# Process errors
if errors:
    for error in errors:
        print(f"{error['Error_Type']}: {error['Message']}")
else:
    print("No errors found!")
```

## Configuration

### QCRulesEngine Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `min_box_area` | float | 100 | Minimum area (in pixels) for a valid bounding box |
| `iou_threshold` | float | 0.95 | IoU threshold for detecting overlapping boxes |

### Error Types

| Error Type | Description |
|------------|-------------|
| `Bbox_Out_Of_Bounds` | Bounding box extends outside image boundaries |
| `Bbox_Too_Small` | Bounding box area is below minimum threshold |
| `Bbox_Overlap` | Two boxes of same class have high IoU overlap |
| `Polygon_Self_Intersect` | Polygon has self-intersecting edges |
| `Mask_Out_Of_Box` | Polygon mask extends outside its bounding box |
| `Polygon_Error` | General polygon geometry error |

## Test Cases

The `data/test_cases/` directory contains sample files with intentional errors for testing:

| File | Error Type | Description |
|------|------------|-------------|
| `test_bbox_size_oob.json` | Bbox Out of Bounds + Too Small | Box exceeds image dimensions and is too small |
| `test_bbox_overlap.json` | Bbox Overlap | Two boxes of same class at same location |
| `test_missing_attr.json` | Missing Attribute | Missing required `occluded` attribute |
| `test_poly_errors.json` | Polygon Errors | Self-intersecting polygon + mask out of box |

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -r requirements.txt pytest

# Run tests
pytest
```

### Code Formatting

```bash
# Install black
pip install black

# Format code
black src/
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is proprietary to VinAI.

## Contact

For questions or support, please refer to the internal team documentation or contact the project maintainers.
