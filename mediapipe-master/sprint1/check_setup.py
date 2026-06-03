import sys
import os
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(REPO_ROOT / ".tmp" / "matplotlib"))
sys.path = [path for path in sys.path if Path(path or ".").resolve() != REPO_ROOT]

import cv2
import mediapipe as mp
import numpy as np


print("Sprint 1 minimal setup is ready.")
print(f"Python: {sys.version.split()[0]}")
print(f"OpenCV: {cv2.__version__}")
print(f"NumPy: {np.__version__}")
print(f"MediaPipe package: {Path(mp.__file__).parent}")
print(f"MediaPipe Tasks available: {hasattr(mp, 'tasks')}")
