# 📋 LetmeQC - Next Steps (Tomorrow's Plan)

## 🎯 Background & Lessons from POC

From the first POC completion, we've learned:
- ✅ **Logic is minimal** - Current QC rules are basic and need expansion
- ✅ **Mock data only** - Haven't tested with real CVAT production data yet
- ✅ **Effectiveness unproven** - Need to validate that QC catches real annotation errors
- ✅ **Too much context overloading** - Cleaned up unused code to focus on core flow

## 🏗️ Cleanup Completed (Today)

### Removed Unused Code:
1. **app.py**
   - Removed unused `JSONResponse` import
   - Removed `update_job_status` method from `CVATAPI` (no longer called)
   - Enabled `assignee_id` in `create_issue` (was commented out)

2. **src/parser.py**
   - Removed `parse_coco_json` function (not used in webhook flow)
   - Removed test block at bottom (not used)
   - Simplified imports

3. **src/rules.py**
   - Removed unused `required_frame_tags` and `required_obj_attrs` configuration
   - Removed `_check_required_frame_attributes` and `_check_required_object_attributes` methods
   - Kept core QC logic: bbox bounds, bbox sizes, bbox overlap, polygon checks

### Result:
- Lean, focused codebase
- Only essential logic for webhook-based QC
- Reduced context overloading

---

## 🎯 Tomorrow's Goals (MVP Phase)

### 🔬 Priority 1: Validate with Real Data

**Objective:** Test the tool with actual CVAT production data to prove effectiveness

**Tasks:**
- [ ] Deploy webhook server with real CVAT token
- [ ] Create test jobs in CVAT with intentional errors:
  - Bbox out of bounds
  - Bbox too small (< 100px)
  - Overlapping bboxes (IoU > 0.95)
  - Self-intersecting polygons
  - Mask out of bbox
- [ ] Trigger webhook by changing job status to "validation"
- [ ] Verify issues are created correctly in CVAT
- [ ] **Measure:** Record detection rate for each error type

**Success Criteria:**
- ✅ All intentional errors are detected
- ✅ Issues created with correct frame and error details
- ✅ No false positives on clean data

---

### 📊 Priority 2: Implement Reporting & Metrics

**Objective:** Generate measurable reports to demonstrate QC effectiveness

**Tasks:**
- [ ] Add **QC Report Generation**
  - Create `src/reports.py` with Report class
  - Track metrics:
    ```python
    {
      "job_id": 123,
      "total_frames": 50,
      "frames_checked": 50,
      "total_errors": 5,
      "error_types": {
        "Bbox_Out_Of_Bounds": 1,
        "Bbox_Too_Small": 2,
        "Bbox_Overlap": 1,
        "Polygon_Self_Intersect": 1
      },
      "frames_with_errors": 3,
      "created_issues": 3,
      "detection_rate": "100%",  # If we know intentional errors
      "timestamp": "..."
    }
    ```
  
- [ ] Save reports to file or database
  - Option 1: JSON file per job in `reports/` directory
  - Option 2: Simple SQLite database
  - Option 3: Log to external monitoring system

- [ ] Add **API endpoint** to retrieve reports:
  ```python
  @app.get("/reports/{job_id}")
  async def get_report(job_id: int):
      # Return QC report for specific job
  
  @app.get("/reports")
  async def list_reports():
      # List all QC reports
  ```

**Success Criteria:**
- ✅ Reports generated for every QC run
- ✅ Metrics are accurate and actionable
- ✅ Can query historical reports

---

### 🛠️ Priority 3: Improve Error Details

**Objective:** Make error messages more actionable

**Tasks:**
- [ ] Enhance error messages with:
  - Suggested fixes
  - Severity levels (high/medium/low)
  - Affected object details (coordinates, size, etc.)

**Example Enhanced Error:**
```json
{
  "Frame": "frame_001.jpg",
  "Object_ID": 123,
  "Error_Type": "Bbox_Too_Small",
  "Message": "Diện tích box (50.0px) nhỏ hơn mức cho phép (100px)",
  "Severity": "high",
  "Suggestion": "Vẽ lại bbox to hơn hoặc chia nhỏ object",
  "Details": {
    "xtl": 100, "ytl": 200, "xbr": 110, "ybr": 210,
    "width": 10, "height": 10, "area": 100,
    "label": "car"
  }
}
```

**Success Criteria:**
- ✅ Annotators can understand and fix errors from messages
- ✅ Errors include all necessary context

---

### 📈 Priority 4: Add More QC Rules (If Time Permits)

**Objective:** Expand QC coverage based on real annotation patterns

**Potential New Rules:**
- [ ] **Duplicate Objects**: Same object annotated multiple times
- [ ] **Label Consistency**: Inconsistent labeling across frames
- [ ] **Aspect Ratio Check**: Detect extremely wide/tall bboxes
- [ ] **Polygon Point Count**: Minimum points for valid polygon
- [ ] **Frame Coverage**: Percentage of frame covered by annotations

**Success Criteria:**
- ✅ New rules catch real annotation errors
- ✅ Rules are configurable via environment variables

---

## 📅 Timeline (Tomorrow)

### Morning (9:00 - 12:00)
- [ ] **Test with Real Data** (Priority 1)
  - Set up test jobs in CVAT
  - Deploy webhook server
  - Run tests and validate detection
  - Document results

### Afternoon (13:00 - 17:00)
- [ ] **Implement Reporting** (Priority 2)
  - Create report generation logic
  - Add API endpoints
  - Test report generation

### Evening (17:00 - 18:00)
- [ ] **Improve Error Details** (Priority 3)
  - Enhance error format
  - Add severity and suggestions
  - Review and finalize

### Optional (If time permits)
- [ ] **Add New QC Rules** (Priority 4)
- [ ] **Document lessons learned**

---

## 📊 Success Metrics for Tomorrow

| Metric | Target | Measurement |
|--------|--------|-------------|
| Error Detection Rate | 100% | % of intentional errors caught |
| False Positive Rate | < 5% | % of clean jobs flagged as errors |
| Report Coverage | 100% | All QC runs have reports |
| Issue Creation Rate | 100% | All errors have CVAT issues |
| Deploy Success | ✅ | Webhook server running with real data |

---

## 🎯 MVP Definition

**Minimum Viable Product (End of Tomorrow):**
- ✅ Webhook server receives CVAT events
- ✅ Automatically runs QC on validation status
- ✅ Creates CVAT issues for detected errors
- ✅ Generates QC reports with metrics
- ✅ Validated with real production data
- ✅ Measurable effectiveness (>95% detection rate)

---

## 📝 Notes

### What We Have Now (After Today's Cleanup):
- Clean, focused codebase
- Webhook endpoint working
- Core QC rules implemented
- Issue creation working
- Ready for real data testing

### What We Need Tomorrow:
- **Proof of effectiveness** with real data
- **Metrics and reporting** to show value
- **Actionable error details** for annotators

### Blockers to Watch For:
- ⚠️ CVAT API rate limits
- ⚠️ Large job performance (many frames)
- ⚠️ Network connectivity issues
- ⚠️ Token expiration

---

## 💡 Quick Start for Tomorrow

```bash
# 1. Start webhook server
python app.py

# 2. Expose with ngrok (if local testing)
ngrok http 8000

# 3. Update CVAT webhook URL
# URL: https://<ngrok-id>.ngrok.io/webhook/cvat

# 4. Create test job in CVAT with intentional errors
# 5. Change job status to "validation"
# 6. Check logs and verify issues are created
```

---

## 📞 Support

- **Code Questions**: Check cleaned files (app.py, src/parser.py, src/rules.py)
- **CVAT Questions**: https://docs.cvat.ai/
- **FastAPI Questions**: https://fastapi.tiangolo.com/
