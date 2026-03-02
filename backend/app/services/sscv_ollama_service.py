# file backend/app/services/sscv_ollama_service.py
import requests
from typing import Optional
from app.configs.config import settings

class SSCVOllamaClientService:
    
    def __init__(self, base_url: str = settings.OLLAMA_BASE_URL):
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
    
    def generate_ppe_report(
            self, date_time: str, missing_items: list, image_ref: Optional[list] = None,
            location: str = "Site Area", model: str = "llama3:8b"
        ):
        prompt = f"""
        Create a short, formal incident report for a supervisor about a PPE violation.
        Include: time ({date_time}), missing items ({', '.join(missing_items)}), location ({location}), and evidence image {len(image_ref) if image_ref else 0} attached.
        Keep the report clear and under 150 characters.
        Report
        """

        payload = {
            "model": settings.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 200}
        }
        try:
            response = requests.post(f"{self.api_url}", json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            report_text = result.get("response", "Report generation failed.").strip()
            return report_text
        except requests.exceptions.RequestException as e:
            # Fallback message
            return f"PPE Violation: {', '.join(missing_items)} " \
            f"at {date_time}. Immediate action required."
    
    def health_check(self) -> bool:
        """Check if Ollama server is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

ollama_service = SSCVOllamaClientService()