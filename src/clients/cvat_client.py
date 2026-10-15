"""CVAT API Client for LetmeQC"""
import logging
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class CVATAPI:
    """Helper class for CVAT API interactions with X-Organization header support"""

    JOBS_PATH = "/jobs/"

    def __init__(self, base_url: str, token: str, org_slug: str = None, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.org_slug = org_slug
        self.timeout = timeout

    def _get_headers(self) -> Dict[str, str]:
        """Get headers with Authorization and X-Organization if configured"""
        headers = {
            "Authorization": "Bearer " + self.token,
            "Content-Type": "application/json"
        }
        if self.org_slug:
            headers["X-Organization"] = self.org_slug
        return headers

    def get_job_annotations(self, job_id: int) -> Dict:
        """Fetch annotations for a job"""
        url = self.base_url + self.JOBS_PATH + str(job_id) + "/annotations"
        logger.info("Fetching annotations from: %s", url)

        try:
            response = requests.get(url, headers=self._get_headers(), timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            logger.exception("Failed to fetch annotations for job %s", job_id)
            raise

    def create_issue(self, job_id: int, frame: int, position: List[float],
                     message: str, assignee_id: Optional[int] = None) -> Dict:
        """Create a QC issue in CVAT with position [x1, y1, x2, y2]"""
        url = self.base_url + "/issues"
        issue_data = {
            "frame": int(frame),
            "position": position,
            "job": job_id,
            "message": message,
            "resolved": False
        }

        if assignee_id:
            issue_data["assignee"] = assignee_id

        logger.info("Creating issue for job %s, frame %s: %s", job_id, frame, message)

        try:
            response = requests.post(url, json=issue_data,
                                    headers=self._get_headers(), timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            response_text = e.response.text if hasattr(e, 'response') else ''
            logger.exception("Failed to create issue. CVAT Response: %s", response_text)
            raise

    def update_job_status(self, job_id: int, stage: str, state: str,
                          assignee_id: Optional[int] = None) -> Dict:
        """Update job status via PATCH"""
        url = self.base_url + self.JOBS_PATH + str(job_id)
        payload = {"stage": stage, "state": state}

        if assignee_id:
            payload["assignee"] = assignee_id

        try:
            response = requests.patch(url, json=payload,
                                     headers=self._get_headers(), timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            logger.exception("Failed to update job status for job %s", job_id)
            raise

    def get_job_info(self, job_id: int) -> Dict:
        """Get job information"""
        url = self.base_url + self.JOBS_PATH + str(job_id)

        try:
            response = requests.get(url, headers=self._get_headers(), timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            logger.exception("Failed to get job info for job %s", job_id)
            raise

    def get_job_labels(self, job_id: int) -> Dict[int, str]:
        """Fetch labels metadata for mapping ID to Name"""
        url = self.base_url + "/labels?job_id=" + str(job_id)
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=self.timeout)
            response.raise_for_status()
            results = response.json().get("results", [])
            return {item["id"]: item["name"] for item in results}
        except Exception:
            logger.exception("Failed to fetch labels for job %s", job_id)
            return {}
