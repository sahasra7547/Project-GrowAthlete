# Sprint 1 Minimal Setup

Use this instead of Bazel. Sprint 1 only needs video ingestion, MediaPipe Pose landmarks, and lower-body angle metrics.

This uses the prebuilt Python package plus one small `pose_landmarker_lite.task` model. It does not build MediaPipe from source.

## Setup

From the repository root:

```powershell
cd C:\Users\sahasra7547\Downloads\mediapipe-master\mediapipe-master
.\.venv\Scripts\Activate.ps1
```

The needed packages are already installed. If you recreate the environment later:

```powershell
pip install -r sprint1\requirements-minimal.txt
```

## Run The Preferred Sprint 1 Test

Use the full-body sports-running clip:

```powershell
python sprint1\pose_pipeline.py "sprint1\input_videos\special_olympics_running.webm" --output "sprint1\outputs\special_olympics_running_enhanced.csv"
```

Or run your own athlete video:

```powershell
python sprint1\pose_pipeline.py "C:\path\to\athlete_sprint_clip.mp4"
```

The CSV will be saved to:

```text
sprint1/outputs/special_olympics_running_enhanced.csv
```

The pipeline also creates:

```text
sprint1/outputs/special_olympics_running_enhanced_overlay.mp4
sprint1/outputs/special_olympics_running_enhanced_summary.md
```

## What It Extracts

- All 33 MediaPipe body landmarks with `x`, `y`, `z`, and `visibility`
- Right and left knee flexion angles
- Hip alignment / pelvic tilt angle
- Ankle deviation angles
- Foot rotation angles
- Frame-by-frame CSV data
- Annotated skeleton overlay video
- Biomechanical summary report

Do not run Bazel for Sprint 1. Bazel builds MediaPipe from source and downloads TensorFlow, LLVM, toolchains, and many native dependencies.

If Bazel is currently running in another PowerShell window, stop it with `Ctrl+C`.

## Test Video Credit

`sprint1/input_videos/special_olympics_running.webm` is from Wikimedia Commons:
https://commons.wikimedia.org/wiki/File:Special_Olympics_Basketball_running_2024.webm

Author: DavidforDance. License: CC BY 4.0.

`sprint1/input_videos/running_form.ogv` is from Wikimedia Commons:
https://commons.wikimedia.org/wiki/File:Running_form.ogv

Author: Bill Sodeman. License: CC BY-SA 2.0.
