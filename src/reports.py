"""
QC Report - Summary system for QC runs
- Save JSON files
- Keep only max 5 reports (delete oldest)
- Short summary files, max 50 lines
"""
import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import os


class QCReport:
    """Class for managing QC reports"""
    
    def __init__(self, job_id: int, job_name: str = "unknown"):
        self.job_id = job_id
        self.job_name = job_name
        self.timestamp = datetime.now().isoformat()
        self.status = "pending"  # pending, passed, failed
        
        # Basic metrics
        self.total_frames = 0
        self.total_annotations = 0
        self.errors: List[Dict] = []
        self.error_type_counts: Dict[str, int] = {}
        self.issues_created = 0
        self.failed_issue_creations = 0
        self.job_status_updated: Optional[str] = None
    
    def add_error(self, error_type: str, message: str):
        """Add an error to the report"""
        self.errors.append({
            "type": error_type,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        self.error_type_counts[error_type] = self.error_type_counts.get(error_type, 0) + 1
    
    def get_error_type_counts(self) -> Dict[str, int]:
        """Get error counts by type"""
        return self.error_type_counts
    
    def to_summary_dict(self) -> Dict:
        """
        Convert report to summary dictionary (short, max 50 lines)
        Only includes summary information, not full error details
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
        Save report to JSON file
        - Create directory if not exists
        - Keep only max 5 reports (delete oldest)
        - Save short summary file
        """
        # Create directory
        Path(reports_dir).mkdir(parents=True, exist_ok=True)
        
        # List existing report files
        existing_reports = sorted(
            Path(reports_dir).glob("report_job_*.json"),
            key=lambda p: p.stat().st_mtime
        )
        
        # Delete oldest reports if more than 5
        while len(existing_reports) >= 5:
            oldest = existing_reports.pop(0)
            oldest.unlink()
        
        # Create filename
        filename = f"report_job_{self.job_id}_{self.timestamp.replace(':', '-').replace('.', '-')}.json"
        filepath = Path(reports_dir) / filename
        
        # Save summary file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_summary_dict(), f, indent=2, ensure_ascii=False)
        
        return str(filepath)
    
    @staticmethod
    def load(filepath: str) -> Optional['QCReport']:
        """Load report from file"""
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
        """Get all reports from directory"""
        reports = []
        if Path(reports_dir).exists():
            for filepath in sorted(
                Path(reports_dir).glob("report_job_*.json"), 
                key=lambda p: p.stat().st_mtime, 
                reverse=True
            ):
                report = QCReport.load(str(filepath))
                if report:
                    reports.append(report)
        return reports