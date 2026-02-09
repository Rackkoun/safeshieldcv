# file safeshieldcv/frontend/run.py
import sys
from pathlib import Path

# setup paths
frontend = Path(__file__).parent
app_dir = frontend / "sscv-desktop-app"

# add to python path
sys.path.insert(0, str(app_dir))

from app import main

if __name__ == "__main__":
    main()