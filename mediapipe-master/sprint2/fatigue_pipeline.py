import argparse
import csv
from pathlib import Path
from statistics import mean, pstdev


MOVEMENT_METRICS = [
    "right_knee_angle",
    "left_knee_angle",
    "knee_angle_difference",
    "hip_alignment_abs_angle",
    "right_ankle_deviation_angle",
    "left_ankle_deviation_angle",
]

TELEMETRY_FIELDS = [
    "resting_heart_rate",
    "sleep_efficiency",
    "spo2",
    "gps_distance_km",
    "sprint_count",
    "match_load",
]


def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fieldnames):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def metric_values(rows, key):
    values = []
    for row in rows:
        if row.get("pose_detected") != "1":
            continue
        value = to_float(row.get(key))
        if value is not None:
            values.append(value)
    return values


def summarize_movement(rows):
    summary = {}
    for metric in MOVEMENT_METRICS:
        values = metric_values(rows, metric)
        if not values:
            summary[f"avg_{metric}"] = 0.0
            summary[f"max_{metric}"] = 0.0
            summary[f"std_{metric}"] = 0.0
            continue
        summary[f"avg_{metric}"] = round(mean(values), 4)
        summary[f"max_{metric}"] = round(max(values), 4)
        summary[f"std_{metric}"] = round(pstdev(values), 4)

    summary["pose_detection_coverage"] = round(
        sum(1 for row in rows if row.get("pose_detected") == "1") / max(len(rows), 1), 4
    )
    return summary


def clamp(value, low=0.0, high=100.0):
    return max(low, min(high, value))


def fatigue_score(row, movement):
    resting_hr = float(row["resting_heart_rate"])
    sleep = float(row["sleep_efficiency"])
    spo2 = float(row["spo2"])
    distance = float(row["gps_distance_km"])
    sprint_count = float(row["sprint_count"])
    match_load = float(row["match_load"])

    knee_asymmetry = movement["avg_knee_angle_difference"]
    hip_alignment = movement["avg_hip_alignment_abs_angle"]
    ankle_deviation = (
        movement["avg_right_ankle_deviation_angle"]
        + movement["avg_left_ankle_deviation_angle"]
    ) / 2.0

    physiological_load = (
        max(resting_hr - 55.0, 0.0) * 1.25
        + max(85.0 - sleep, 0.0) * 1.4
        + max(97.0 - spo2, 0.0) * 5.0
    )
    external_load = distance * 2.4 + sprint_count * 0.65 + match_load * 0.35
    biomechanical_load = knee_asymmetry * 0.35 + hip_alignment * 0.45 + ankle_deviation * 0.25

    return round(clamp(physiological_load + external_load + biomechanical_load), 2)


def risk_level(score):
    if score >= 75:
        return "High"
    if score >= 50:
        return "Moderate"
    return "Low"


def recommendation(level):
    if level == "High":
        return "Reduce sprint volume, prioritize recovery, and review asymmetry markers."
    if level == "Moderate":
        return "Maintain controlled workload and monitor sleep, heart rate, and ankle deviation."
    return "Proceed with normal training while continuing baseline monitoring."


def build_feature_rows(telemetry_rows, movement):
    rows = []
    for telemetry in telemetry_rows:
        score = fatigue_score(telemetry, movement)
        level = risk_level(score)
        row = dict(telemetry)
        row.update(movement)
        row["fatigue_score"] = score
        row["risk_level"] = level
        row["recommendation"] = recommendation(level)
        rows.append(row)
    return rows


def write_summary(path, rows, movement_csv, telemetry_csv, output_csv):
    high = sum(1 for row in rows if row["risk_level"] == "High")
    moderate = sum(1 for row in rows if row["risk_level"] == "Moderate")
    low = sum(1 for row in rows if row["risk_level"] == "Low")
    scores = [float(row["fatigue_score"]) for row in rows]
    riskiest = max(rows, key=lambda row: float(row["fatigue_score"]))
    riskiest_label = riskiest.get("date") or riskiest.get("session_id", "unknown session")
    riskiest_date = riskiest.get("date", "Not provided")

    lines = [
        "# Sprint 2 Fatigue Fusion Summary",
        "",
        f"- Sprint 1 movement CSV: `{movement_csv}`",
        f"- Telemetry CSV: `{telemetry_csv}`",
        f"- Combined feature output: `{output_csv}`",
        f"- Sessions analyzed: {len(rows)}",
        f"- Average fatigue score: {mean(scores):.2f}",
        f"- Highest fatigue score: {riskiest['fatigue_score']} on {riskiest_label}",
        f"- Risk distribution: {low} Low, {moderate} Moderate, {high} High",
        "",
        "## Movement Features Reused From Sprint 1",
        "",
        f"- Average right knee angle: {rows[0]['avg_right_knee_angle']} deg",
        f"- Average left knee angle: {rows[0]['avg_left_knee_angle']} deg",
        f"- Average knee asymmetry: {rows[0]['avg_knee_angle_difference']} deg",
        f"- Average hip alignment angle: {rows[0]['avg_hip_alignment_abs_angle']} deg",
        (
            "- Average ankle deviation: "
            f"{((float(rows[0]['avg_right_ankle_deviation_angle']) + float(rows[0]['avg_left_ankle_deviation_angle'])) / 2):.2f} deg"
        ),
        f"- Pose detection coverage: {float(rows[0]['pose_detection_coverage']) * 100:.1f}%",
        "",
        "## Riskiest Session",
        "",
        f"- Session: {riskiest['session_id']}",
        f"- Date: {riskiest_date}",
        f"- Fatigue score: {riskiest['fatigue_score']}",
        f"- Risk level: {riskiest['risk_level']}",
        f"- Recommendation: {riskiest['recommendation']}",
        "",
        "## Interpretation",
        "",
        (
            "This is a Sprint 2 feature-fusion prototype. It combines movement mechanics "
            "from Sprint 1 with wearable-style telemetry and workload variables. The risk "
            "score is rule-based for explainability; it can later be replaced by XGBoost, "
            "LSTM, or another trained model once real labeled athlete data exists."
        ),
    ]

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Sprint 2 fatigue feature fusion pipeline")
    parser.add_argument(
        "--movement-csv",
        default="sprint1/outputs/special_olympics_running_enhanced.csv",
        help="Sprint 1 enhanced movement CSV",
    )
    parser.add_argument(
        "--telemetry-csv",
        default="sprint2/input_data/sample_telemetry.csv",
        help="Wearable/workload telemetry CSV",
    )
    parser.add_argument(
        "--output",
        default="sprint2/outputs/combined_fatigue_features.csv",
        help="Combined Sprint 2 feature dataset",
    )
    parser.add_argument(
        "--summary-output",
        default="sprint2/outputs/fatigue_summary.md",
        help="Sprint 2 summary report",
    )
    args = parser.parse_args()

    movement_rows = read_csv(args.movement_csv)
    telemetry_rows = read_csv(args.telemetry_csv)
    movement_summary = summarize_movement(movement_rows)
    feature_rows = build_feature_rows(telemetry_rows, movement_summary)

    fieldnames = list(feature_rows[0].keys())
    write_csv(args.output, feature_rows, fieldnames)
    write_summary(
        args.summary_output,
        feature_rows,
        args.movement_csv,
        args.telemetry_csv,
        args.output,
    )

    print(f"Saved Sprint 2 combined feature dataset to: {args.output}")
    print(f"Saved Sprint 2 fatigue summary to: {args.summary_output}")


if __name__ == "__main__":
    main()
