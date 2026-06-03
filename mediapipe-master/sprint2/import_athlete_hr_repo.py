import argparse
import csv
from pathlib import Path
from statistics import mean


def to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def read_rows(path):
    with Path(path).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_rows(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "session_id",
        "athlete_id",
        "date",
        "resting_heart_rate",
        "sleep_efficiency",
        "spo2",
        "gps_distance_km",
        "sprint_count",
        "match_load",
        "source_file",
        "avg_heart_rate",
        "max_heart_rate",
        "avg_speed_mps",
        "max_speed_mps",
        "avg_cadence",
        "duration_sec",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def date_from_timestamp(value):
    return (value or "").split(" ")[0]


def summarize_run(path, index):
    rows = read_rows(path)
    heart_rates = [to_float(row.get("heart_rate")) for row in rows]
    speeds = [to_float(row.get("enhanced_speed")) for row in rows]
    cadences = [to_float(row.get("cadence")) for row in rows]
    distances = [to_float(row.get("distance")) for row in rows]

    duration_sec = len(rows)
    max_distance_m = max(distances) if distances else 0.0
    avg_hr = mean(heart_rates) if heart_rates else 0.0
    max_hr = max(heart_rates) if heart_rates else 0.0
    avg_speed = mean(speeds) if speeds else 0.0
    max_speed = max(speeds) if speeds else 0.0
    avg_cadence = mean(cadences) if cadences else 0.0
    sprint_count = sum(1 for speed in speeds if speed >= 4.5)

    # These fields are unavailable in the reference repo, so they are neutral placeholders.
    sleep_efficiency = 85
    spo2 = 98

    match_load = min(
        100.0,
        (max_distance_m / 1000.0) * 8.0 + sprint_count * 1.2 + max(avg_hr - 100.0, 0.0) * 0.35,
    )

    return {
        "session_id": f"garmin_run_{index:03d}",
        "athlete_id": "athlete_hr_predict_reference",
        "date": date_from_timestamp(rows[0].get("timestamp") if rows else ""),
        "resting_heart_rate": round(max(min(heart_rates), 45.0), 1) if heart_rates else 60,
        "sleep_efficiency": sleep_efficiency,
        "spo2": spo2,
        "gps_distance_km": round(max_distance_m / 1000.0, 3),
        "sprint_count": sprint_count,
        "match_load": round(match_load, 2),
        "source_file": path.name,
        "avg_heart_rate": round(avg_hr, 2),
        "max_heart_rate": round(max_hr, 2),
        "avg_speed_mps": round(avg_speed, 3),
        "max_speed_mps": round(max_speed, 3),
        "avg_cadence": round(avg_cadence, 2),
        "duration_sec": duration_sec,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Convert athlete_hr_predict Garmin CSV files to Sprint 2 telemetry rows"
    )
    parser.add_argument(
        "--repo",
        default=r"C:\Users\sahasra7547\Downloads\mediapipe-master\athlete_hr_predict-master",
        help="Path to athlete_hr_predict-master",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=8,
        help="Number of run files to summarize",
    )
    parser.add_argument(
        "--output",
        default="sprint2/input_data/athlete_hr_predict_telemetry.csv",
        help="Output Sprint 2 telemetry CSV",
    )
    args = parser.parse_args()

    repo = Path(args.repo)
    files = sorted((repo / "fit_file_csv").glob("*.fit.csv"))[: args.limit]
    if not files:
        raise FileNotFoundError(f"No .fit.csv files found under {repo / 'fit_file_csv'}")

    summaries = [summarize_run(path, index + 1) for index, path in enumerate(files)]
    write_rows(args.output, summaries)
    print(f"Saved converted athlete_hr_predict telemetry to: {args.output}")


if __name__ == "__main__":
    main()
