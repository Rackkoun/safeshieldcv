# file frontend/sscv-desktop-app/configs/sscv_config.py
# @author: Rackkoun

# import os
import json
from pathlib import Path
from typing import Dict, Any, List

class SSCVConfig:
    """SSCV frontend config manager"""
    def __init__(self, config_dir=None):
        # navigate to project root
        project_root = Path(__file__).parents[3]
        self.config_dir = project_root / "configs"
        # print(f"[DEBUG DIR] at: {self.config_dir}")
        
        self.config_file = self.config_dir / "frontend_config.json"
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load frontend config"""
        # load file
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                return config
            except Exception as e:
                print(f"[CONFIG] Error loading frontend config file: {e}")
    
    # props
    @property
    def api_url(self) -> str:
        return self.config["backend"]["api_url"]
    
    @property
    def default_location(self) -> str:
        return self.config["ui"]["default_location"]
    
    @property
    def default_recipients(self) -> List[str]:
        return self.config["ui"].get("default_recipients", [])
    
    @property
    def evidence_dir(self) -> str:
        return self.config["detection"]["evidence_dir"]

# singleton instance
_config_instance = None

def get_config(config_dir: str=None) -> SSCVConfig:
    global _config_instance
    if _config_instance is None:
        _config_instance = SSCVConfig(config_dir)
    return _config_instance