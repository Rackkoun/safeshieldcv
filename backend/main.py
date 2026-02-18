# file safeshieldcv/backend/main.py
# @author: Rackkoun
"""Backend entry point"""
import warnings
# filter pydantic warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
import os
import uvicorn
from pathlib import Path
from dotenv import load_dotenv

# Load env variables
SSCV_ROOT = Path(__file__).resolve().parent
CONFIGS_DIR = SSCV_ROOT.resolve().parent / "configs"
BACKEND_CONFIG_FILE = CONFIGS_DIR / "backend_config.env"
# check if file exists
if BACKEND_CONFIG_FILE.exists():
    load_dotenv(BACKEND_CONFIG_FILE)
    print(f" Loaded config from: {BACKEND_CONFIG_FILE}")
else:
    print(f"  Config file not found: {BACKEND_CONFIG_FILE}")
    print("   Using default configuration")

if __name__ == "__main__":
    host = os.getenv("SSCV_API_HOST", "127.0.0.1")
    port = int(os.getenv("SSCV_API_PORT", "8000"))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    # start server
    print(f"\n{'='*60}")
    print(" SafeShieldCV Backend API Server")
    print(f"{'='*60}")
    print(f" Server: http://{host}:{port}")
    print(f" API Docs: http://{host}:{port}/sscv/docs")
    print(f" ReDoc: http://{host}:{port}/sscv/redoc")
    print(f" Debug Mode: {debug}")
    print(f"{'='*60}\n")

    uvicorn.run(
        "app.api.sscv_api:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if debug else "warning"
    )