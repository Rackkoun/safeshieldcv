# file frontend/sscv-desktop-app/services/sscv_stats_service.py
# @author: Rackkoun
import requests
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class SSCVStatisticServices:
    """Client API service for registered incidents"""
    def __init__(self, backend_api_url: str):
        # logger.info(f"SSCVREPORTGEN INIT: api_url: {backend_api_url}")
        self.backend_api_url = backend_api_url.rstrip('/')
        self._last_incident_id: Optional[int] = None
    
    def get_incidents(self) -> List:
        """Fetch incidents from the backend."""
        try:
            response = requests.get(f"{self.backend_api_url}/incidents")
            return response.json() if response.status_code == 200 else []
        except Exception as e:
            logger.error(f"Error fetching incidents: {e}")
            return []

    def get_daily_stats(self) -> List:
        """Fetch daily incident statistics."""
        try:
            response = requests.get(f"{self.backend_api_url}/stats/daily-range")
            return response.json() if response.status_code == 200 else []
        except Exception as e:
            logger.error(f"Error fetching daily stats: {e}")
            return []