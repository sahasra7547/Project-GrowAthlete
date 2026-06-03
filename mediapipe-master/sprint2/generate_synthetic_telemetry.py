import argparse
import random
from pathlib import Path

import pandas as pd


def clamp(value, low, high):
    return max(low, min(high, value))


def fatigue_label(score):
    if score >= 72:
        return "High"
    if score >= 48:
        return "Moderate"
    return "Low"


def make_session(session_number, rng):
    session_type = session_number % 3
    if session_type == 0:
        base_load = rng.uniform(18, 42)
        distance = rng.uniform(2.0, 6.8)
        sprint_count = rng.randint(0, 12)
        sleep = rng.uniform(86, 98)
        resting_hr = rng.randint(45, 57)
    elif session_type == 1:
        base_load = rng.uniform(43, 68)
        distance = rng.uniform(5.5, 10.5)
        sprint_count = rng.randint(8, 28)
        sleep = rng.uniform(75, 90)
        resting_hr = rng.randint(53, 64)
    else:
        base_load = rng.uniform(69, 98)
        distance = rng.uniform(8.0, 15.0)
        sprint_count = rng.randint(22, 50)
        sleep = rng.uniform(60, 82)
        resting_hr = rng.randint(60, 75)

    spo2 = rng.randint(93, 100)
    avg_hr = clamp(88 + base_load * 0.78 + rng.gauss(0, 8), 100, 180)
    max_hr = clamp(avg_hr + rng.uniform(24, 58), 140, 210)
    avg_speed = clamp(2.0 + distance / 3.2 + rng.gauss(0, 0.6), 2, 8)
    max_speed = clamp(avg_speed + rng.uniform(2.2, 5.0), 4, 12)
    cadence = clamp(145 + avg_speed * 7.2 + rng.gauss(0, 8), 140, 200)
    duration = clamp(int((distance * 1000) / max(avg_speed, 0.1) + rng.gauss(0, 260)), 600, 7200)

    fatigue_score = (
        max(resting_hr - 52, 0) * 1.35
        + max(88 - sleep, 0) * 1.15
        + max(97 - spo2, 0) * 4.0
        + distance * 2.0
        + sprint_count * 0.55
        + base_load * 0.45
        + max(avg_hr - 130, 0) * 0.34
        + rng.gauss(0, 6.5)
    )

    return {
        "session_id": f"session_{session_number:03d}",
        "resting_heart_rate": int(round(resting_hr)),
        "sleep_efficiency": int(round(sleep)),
        "spo2": int(round(spo2)),
        "gps_distance_km": round(distance, 2),
        "sprint_count": int(sprint_count),
        "match_load": int(round(base_load)),
        "avg_heart_rate": int(round(avg_hr)),
        "max_heart_rate": int(round(max_hr)),
        "avg_speed_mps": round(avg_speed, 2),
        "max_speed_mps": round(max_speed, 2),
        "avg_cadence": int(round(cadence)),
        "duration_sec": int(duration),
        "fatigue_risk": fatigue_label(fatigue_score),
    }


def rebalance_classes(rows, rng):
    grouped = {"Low": [], "Moderate": [], "High": []}
    for row in rows:
        grouped[row["fatigue_risk"]].append(row)

    # Keep the dataset close to balanced while preserving physiological logic.
    target_per_class = len(rows) // 3
    for label, group in grouped.items():
        while len(group) < target_per_class:
            source_label = max(grouped, key=lambda key: len(grouped[key]))
            moved = grouped[source_label].pop(rng.randrange(len(grouped[source_label])))
            if label == "Low":
                moved.update(
                    {
                        "resting_heart_rate": rng.randint(45, 55),
                        "sleep_efficiency": rng.randint(88, 98),
                        "gps_distance_km": round(rng.uniform(2, 6), 2),
                        "sprint_count": rng.randint(0, 10),
                        "match_load": rng.randint(12, 38),
                        "avg_heart_rate": rng.randint(100, 128),
                        "max_heart_rate": rng.randint(142, 172),
                        "fatigue_risk": "Low",
                    }
                )
            elif label == "Moderate":
                moved.update(
                    {
                        "resting_heart_rate": rng.randint(54, 64),
                        "sleep_efficiency": rng.randint(76, 89),
                        "gps_distance_km": round(rng.uniform(5, 10), 2),
                        "sprint_count": rng.randint(8, 28),
                        "match_load": rng.randint(42, 68),
                        "avg_heart_rate": rng.randint(124, 154),
                        "max_heart_rate": rng.randint(166, 194),
                        "fatigue_risk": "Moderate",
                    }
                )
            else:
                moved.update(
                    {
                        "resting_heart_rate": rng.randint(62, 75),
                        "sleep_efficiency": rng.randint(60, 80),
                        "gps_distance_km": round(rng.uniform(8, 15), 2),
                        "sprint_count": rng.randint(24, 50),
                        "match_load": rng.randint(70, 100),
                        "avg_heart_rate": rng.randint(148, 180),
                        "max_heart_rate": rng.randint(184, 210),
                        "fatigue_risk": "High",
                    }
                )
            group.append(moved)

    balanced = grouped["Low"] + grouped["Moderate"] + grouped["High"]
    rng.shuffle(balanced)
    for index, row in enumerate(balanced, start=1):
        row["session_id"] = f"session_{index:03d}"
    return balanced


def main():
    parser = argparse.ArgumentParser(description="Generate fresh Sprint 2 synthetic telemetry")
    parser.add_argument("--rows", type=int, default=150)
    parser.add_argument("--seed", type=int, default=20260602)
    parser.add_argument("--output", default="sprint2/input_data/synthetic_athlete_telemetry_fresh.csv")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    rows = [make_session(index, rng) for index in range(1, args.rows + 1)]
    rows = rebalance_classes(rows, rng)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(output, index=False)

    counts = pd.DataFrame(rows)["fatigue_risk"].value_counts().to_dict()
    print(f"Saved fresh synthetic telemetry to: {output}")
    print(f"Rows: {len(rows)}")
    print(f"Class distribution: {counts}")


if __name__ == "__main__":
    main()
