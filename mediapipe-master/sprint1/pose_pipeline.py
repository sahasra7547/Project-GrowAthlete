import argparse
import csv
import os
import sys
import urllib.request
from pathlib import Path

import cv2
import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(REPO_ROOT / ".tmp" / "matplotlib"))
sys.path = [
    path
    for path in sys.path
    if Path(path or ".").resolve() != REPO_ROOT
]

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
    "pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"
)
DEFAULT_MODEL = REPO_ROOT / "sprint1" / "models" / "pose_landmarker_lite.task"

LANDMARK_NAMES = [
    "nose",
    "left_eye_inner",
    "left_eye",
    "left_eye_outer",
    "right_eye_inner",
    "right_eye",
    "right_eye_outer",
    "left_ear",
    "right_ear",
    "mouth_left",
    "mouth_right",
    "left_shoulder",
    "right_shoulder",
    "left_elbow",
    "right_elbow",
    "left_wrist",
    "right_wrist",
    "left_pinky",
    "right_pinky",
    "left_index",
    "right_index",
    "left_thumb",
    "right_thumb",
    "left_hip",
    "right_hip",
    "left_knee",
    "right_knee",
    "left_ankle",
    "right_ankle",
    "left_heel",
    "right_heel",
    "left_foot_index",
    "right_foot_index",
]

LEFT_HIP = 23
RIGHT_HIP = 24
LEFT_KNEE = 25
RIGHT_KNEE = 26
LEFT_ANKLE = 27
RIGHT_ANKLE = 28
LEFT_HEEL = 29
RIGHT_HEEL = 30
LEFT_FOOT_INDEX = 31
RIGHT_FOOT_INDEX = 32

POSE_CONNECTIONS = [
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 7),
    (0, 4),
    (4, 5),
    (5, 6),
    (6, 8),
    (9, 10),
    (11, 12),
    (11, 13),
    (13, 15),
    (15, 17),
    (15, 19),
    (15, 21),
    (17, 19),
    (12, 14),
    (14, 16),
    (16, 18),
    (16, 20),
    (16, 22),
    (18, 20),
    (11, 23),
    (12, 24),
    (23, 24),
    (23, 25),
    (25, 27),
    (27, 29),
    (29, 31),
    (27, 31),
    (24, 26),
    (26, 28),
    (28, 30),
    (30, 32),
    (28, 32),
]

LOWER_BODY_CONNECTIONS = {
    (23, 24),
    (23, 25),
    (25, 27),
    (27, 29),
    (29, 31),
    (27, 31),
    (24, 26),
    (26, 28),
    (28, 30),
    (30, 32),
    (28, 32),
}


def joint_angle(a, b, c):
    a = np.array(a[:3], dtype=np.float32)
    b = np.array(b[:3], dtype=np.float32)
    c = np.array(c[:3], dtype=np.float32)

    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(
        a[1] - b[1], a[0] - b[0]
    )
    angle = abs(radians * 180.0 / np.pi)
    return 360.0 - angle if angle > 180.0 else angle


def segment_angle(a, b):
    return float(np.degrees(np.arctan2(b[1] - a[1], b[0] - a[0])))


def pelvic_tilt_angle(left_hip, right_hip):
    dx = abs(right_hip[0] - left_hip[0])
    dy = right_hip[1] - left_hip[1]
    return float(np.degrees(np.arctan2(dy, dx)))


def distance_2d(a, b):
    return float(np.linalg.norm(np.array(a[:2]) - np.array(b[:2])))


def point(landmarks, index):
    item = landmarks[index]
    return [item.x, item.y, item.z, item.visibility]


def ensure_model(model_path):
    if model_path.exists():
        return model_path

    model_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading minimal pose model to: {model_path}")
    try:
        urllib.request.urlretrieve(MODEL_URL, model_path)
    except Exception as exc:
        raise RuntimeError(
            "Could not download the minimal pose model. Check your internet "
            f"connection, or download it manually from {MODEL_URL}"
        ) from exc
    return model_path


def landmark_fields():
    fields = []
    for name in LANDMARK_NAMES:
        fields.extend([f"{name}_x", f"{name}_y", f"{name}_z", f"{name}_visibility"])
    return fields


def csv_fields():
    return [
        "frame",
        "time_sec",
        "pose_detected",
        "right_knee_angle",
        "left_knee_angle",
        "knee_angle_difference",
        "hip_alignment_angle",
        "hip_alignment_abs_angle",
        "hip_y_difference",
        "hip_width_norm",
        "right_ankle_angle",
        "left_ankle_angle",
        "right_ankle_deviation_angle",
        "left_ankle_deviation_angle",
        "right_foot_rotation_angle",
        "left_foot_rotation_angle",
    ] + landmark_fields()


def landmark_values(landmarks):
    values = {}
    for index, name in enumerate(LANDMARK_NAMES):
        current = point(landmarks, index)
        values[f"{name}_x"] = current[0]
        values[f"{name}_y"] = current[1]
        values[f"{name}_z"] = current[2]
        values[f"{name}_visibility"] = current[3]
    return values


def compute_metrics(landmarks):
    right_hip = point(landmarks, RIGHT_HIP)
    right_knee = point(landmarks, RIGHT_KNEE)
    right_ankle = point(landmarks, RIGHT_ANKLE)
    right_heel = point(landmarks, RIGHT_HEEL)
    right_foot = point(landmarks, RIGHT_FOOT_INDEX)

    left_hip = point(landmarks, LEFT_HIP)
    left_knee = point(landmarks, LEFT_KNEE)
    left_ankle = point(landmarks, LEFT_ANKLE)
    left_heel = point(landmarks, LEFT_HEEL)
    left_foot = point(landmarks, LEFT_FOOT_INDEX)

    right_knee_angle = joint_angle(right_hip, right_knee, right_ankle)
    left_knee_angle = joint_angle(left_hip, left_knee, left_ankle)
    right_ankle_angle = joint_angle(right_knee, right_ankle, right_foot)
    left_ankle_angle = joint_angle(left_knee, left_ankle, left_foot)

    hip_alignment_angle = pelvic_tilt_angle(left_hip, right_hip)
    right_foot_rotation = segment_angle(right_heel, right_foot)
    left_foot_rotation = segment_angle(left_heel, left_foot)

    return {
        "right_knee_angle": right_knee_angle,
        "left_knee_angle": left_knee_angle,
        "knee_angle_difference": abs(right_knee_angle - left_knee_angle),
        "hip_alignment_angle": hip_alignment_angle,
        "hip_alignment_abs_angle": abs(hip_alignment_angle),
        "hip_y_difference": right_hip[1] - left_hip[1],
        "hip_width_norm": distance_2d(left_hip, right_hip),
        "right_ankle_angle": right_ankle_angle,
        "left_ankle_angle": left_ankle_angle,
        "right_ankle_deviation_angle": abs(180.0 - right_ankle_angle),
        "left_ankle_deviation_angle": abs(180.0 - left_ankle_angle),
        "right_foot_rotation_angle": right_foot_rotation,
        "left_foot_rotation_angle": left_foot_rotation,
    }


def rounded_metrics(metrics):
    return {key: round(value, 4) for key, value in metrics.items()}


def pixel_point(landmark, width, height):
    x = int(np.clip(landmark.x, 0, 1) * width)
    y = int(np.clip(landmark.y, 0, 1) * height)
    return x, y


def draw_pose_overlay(frame, landmarks, metrics):
    height, width = frame.shape[:2]

    for start, end in POSE_CONNECTIONS:
        p1 = pixel_point(landmarks[start], width, height)
        p2 = pixel_point(landmarks[end], width, height)
        color = (0, 220, 255) if (start, end) in LOWER_BODY_CONNECTIONS else (90, 170, 255)
        thickness = 3 if (start, end) in LOWER_BODY_CONNECTIONS else 2
        cv2.line(frame, p1, p2, color, thickness)

    for index, landmark in enumerate(landmarks):
        p = pixel_point(landmark, width, height)
        color = (0, 255, 140) if index >= LEFT_HIP else (255, 210, 80)
        cv2.circle(frame, p, 4, color, -1)

    panel = frame.copy()
    cv2.rectangle(panel, (16, 16), (470, 150), (0, 0, 0), -1)
    frame[:] = cv2.addWeighted(panel, 0.42, frame, 0.58, 0)

    lines = [
        f"R Knee: {metrics['right_knee_angle']:.1f} deg",
        f"L Knee: {metrics['left_knee_angle']:.1f} deg",
        f"Hip Align: {metrics['hip_alignment_angle']:.1f} deg",
        (
            "Ankle Dev R/L: "
            f"{metrics['right_ankle_deviation_angle']:.1f} / "
            f"{metrics['left_ankle_deviation_angle']:.1f} deg"
        ),
    ]
    for i, text in enumerate(lines):
        cv2.putText(
            frame,
            text,
            (30, 48 + i * 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.72,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )


def safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return np.nan


def metric_series(rows, key):
    values = [safe_float(row.get(key)) for row in rows if row.get("pose_detected") == 1]
    values = [value for value in values if not np.isnan(value)]
    return np.array(values, dtype=np.float32)


def stat_line(rows, key, label, unit="deg"):
    values = metric_series(rows, key)
    if values.size == 0:
        return f"- {label}: not available"
    return (
        f"- {label}: mean {values.mean():.2f} {unit}, "
        f"min {values.min():.2f} {unit}, max {values.max():.2f} {unit}"
    )


def write_summary(rows, summary_path, video_path, output_csv, overlay_path):
    total_frames = len(rows)
    detected_frames = sum(1 for row in rows if row.get("pose_detected") == 1)
    coverage = (detected_frames / total_frames * 100.0) if total_frames else 0.0

    lines = [
        "# Sprint 1 Biomechanical Summary",
        "",
        f"- Input video: `{video_path}`",
        f"- Enhanced CSV: `{output_csv}`",
        f"- Overlay video: `{overlay_path}`" if overlay_path else "- Overlay video: not generated",
        f"- Frames analyzed: {total_frames}",
        f"- Pose-detected frames: {detected_frames} ({coverage:.1f}%)",
        "",
        "## Knee Flexion",
        "",
        stat_line(rows, "right_knee_angle", "Right knee angle"),
        stat_line(rows, "left_knee_angle", "Left knee angle"),
        stat_line(rows, "knee_angle_difference", "Left-right knee angle difference"),
        "",
        "## Hip Alignment",
        "",
        stat_line(rows, "hip_alignment_angle", "Signed hip alignment angle"),
        stat_line(rows, "hip_alignment_abs_angle", "Absolute hip alignment angle"),
        stat_line(rows, "hip_y_difference", "Right-left hip vertical offset", "norm units"),
        stat_line(rows, "hip_width_norm", "Hip width", "norm units"),
        "",
        "## Ankle And Foot Mechanics",
        "",
        stat_line(rows, "right_ankle_deviation_angle", "Right ankle deviation"),
        stat_line(rows, "left_ankle_deviation_angle", "Left ankle deviation"),
        stat_line(rows, "right_foot_rotation_angle", "Right foot rotation"),
        stat_line(rows, "left_foot_rotation_angle", "Left foot rotation"),
        "",
        "## Research Note",
        "",
        (
            "These metrics are frame-level movement descriptors for Sprint 1. "
            "They are not clinical injury predictions yet; they prepare the "
            "kinematic feature table needed for later fatigue and telemetry modeling."
        ),
    ]

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text("\n".join(lines), encoding="utf-8")


def process_video(video_path, output_csv, model_path, overlay_video, summary_output, draw_overlay):
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise FileNotFoundError(f"Could not open video: {video_path}")

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    if overlay_video:
        overlay_video.parent.mkdir(parents=True, exist_ok=True)
    model_path = ensure_model(model_path)

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    writer_video = None
    if draw_overlay and overlay_video:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer_video = cv2.VideoWriter(str(overlay_video), fourcc, fps, (width, height))
        if not writer_video.isOpened():
            writer_video.release()
            writer_video = None
            print("Warning: could not create overlay video. CSV and summary will still be saved.")

    options = vision.PoseLandmarkerOptions(
        base_options=python.BaseOptions(model_asset_path=str(model_path)),
        running_mode=vision.RunningMode.VIDEO,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    rows = []
    with vision.PoseLandmarker.create_from_options(options) as landmarker, output_csv.open(
        "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields())
        writer.writeheader()

        frame_index = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            row = {
                "frame": frame_index,
                "time_sec": round(frame_index / fps, 4),
                "pose_detected": 0,
            }

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            timestamp_ms = int((frame_index / fps) * 1000)
            results = landmarker.detect_for_video(image, timestamp_ms)

            if results.pose_landmarks:
                landmarks = results.pose_landmarks[0]
                metrics = compute_metrics(landmarks)
                row.update({"pose_detected": 1})
                row.update(rounded_metrics(metrics))
                row.update(landmark_values(landmarks))
                if writer_video:
                    draw_pose_overlay(frame, landmarks, metrics)

            writer.writerow(row)
            rows.append(row)

            if writer_video:
                writer_video.write(frame)

            frame_index += 1

    cap.release()
    overlay_created = bool(writer_video)
    if writer_video:
        writer_video.release()

    write_summary(
        rows,
        summary_output,
        video_path,
        output_csv,
        overlay_video if overlay_created else None,
    )
    return output_csv, overlay_video, summary_output


def default_overlay_path(output_csv):
    return output_csv.with_name(f"{output_csv.stem}_overlay.mp4")


def default_summary_path(output_csv):
    return output_csv.with_name(f"{output_csv.stem}_summary.md")


def main():
    parser = argparse.ArgumentParser(description="Sprint 1 athlete pose pipeline")
    parser.add_argument("video", help="Path to athlete video file")
    parser.add_argument(
        "--output",
        default="sprint1/outputs/pose_angles.csv",
        help="Enhanced CSV output path",
    )
    parser.add_argument(
        "--overlay-output",
        default=None,
        help="Annotated overlay video output path",
    )
    parser.add_argument(
        "--summary-output",
        default=None,
        help="Biomechanical summary markdown output path",
    )
    parser.add_argument(
        "--model",
        default=str(DEFAULT_MODEL),
        help="Path to pose_landmarker_lite.task",
    )
    parser.add_argument(
        "--no-overlay",
        action="store_true",
        help="Skip annotated video creation",
    )
    args = parser.parse_args()

    output_csv = Path(args.output)
    overlay_video = Path(args.overlay_output) if args.overlay_output else default_overlay_path(output_csv)
    summary_output = Path(args.summary_output) if args.summary_output else default_summary_path(output_csv)

    saved_csv, saved_overlay, saved_summary = process_video(
        Path(args.video),
        output_csv,
        Path(args.model),
        overlay_video,
        summary_output,
        draw_overlay=not args.no_overlay,
    )
    print(f"Saved enhanced pose metrics to: {saved_csv}")
    if not args.no_overlay:
        print(f"Saved annotated overlay video to: {saved_overlay}")
    print(f"Saved biomechanical summary to: {saved_summary}")


if __name__ == "__main__":
    main()
