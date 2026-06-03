import argparse
from pathlib import Path

import pandas as pd


RISK_ORDER = {"Low": 0, "Moderate": 1, "High": 2}


def load_csv(path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Required input not found: {path}")
    return pd.read_csv(path)


def normalize_sprint2_columns(df):
    normalized = df.copy()
    if "fatigue_prediction" not in normalized.columns:
        normalized["fatigue_prediction"] = normalized.get("risk_level", "Unknown")
    if "training_load" not in normalized.columns:
        normalized["training_load"] = normalized.get("match_load", 0)
    return normalized


def build_bridge(athletes, fatigue_rows, athlete_id):
    if athlete_id not in set(athletes["athlete_id"]):
        raise ValueError(f"Selected athlete_id `{athlete_id}` was not found in genomic profiles.")
    sessions = fatigue_rows["session_id"].tolist()
    return pd.DataFrame(
        {
            "athlete_id": [athlete_id for _ in sessions],
            "session_id": sessions,
        }
    )


def write_report(path, sprint2_path, sprint3_path, bridge_path, sprint2_bridged_path, output_path, integrated):
    risk_counts = integrated["risk_level"].value_counts().to_dict()
    lines = [
        "# Sprint 2 to Sprint 3 Integration Report",
        "",
        "## Files Merged",
        "",
        f"- Sprint 2 fatigue features: `{sprint2_path}`",
        f"- Sprint 3 genomic profiles: `{sprint3_path}`",
        f"- Athlete/session bridge: `{bridge_path}`",
        f"- Bridged Sprint 2 fatigue dataset: `{sprint2_bridged_path}`",
        f"- Integrated output: `{output_path}`",
        "",
        "## Bridge Logic",
        "",
        (
            "Each Sprint 2 `session_id` is assigned to the same Sprint 3 `athlete_id`. "
            "This represents a single-athlete longitudinal prototype: one video-tracked athlete with many synthetic training sessions."
        ),
        "",
        "## Sprint 2 Features Added To Sprint 3",
        "",
        "- `session_id`",
        "- `fatigue_score`",
        "- `risk_level`",
        "- `fatigue_prediction`",
        "- `sprint2_recommendation`",
        "- `sprint2_training_load`",
        "- `training_load` updated from Sprint 2 workload when available",
        "",
        "## Integrated Dataset Summary",
        "",
        f"- Integrated rows: {len(integrated)}",
        f"- Unique athletes represented: {integrated['athlete_id'].nunique()}",
        f"- Unique sessions represented: {integrated['session_id'].nunique()}",
        f"- Fatigue risk distribution: {risk_counts}",
        "",
        "## Next Pipeline Step",
        "",
        (
            "Use this integrated file as the Sprint 3 clustering input so recovery phenotype groups are informed by "
            "both genomic-inspired traits and Sprint 2 fatigue state."
        ),
    ]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Integrate Sprint 2 fatigue outputs with Sprint 3 athlete profiles")
    parser.add_argument("--sprint2", default="sprint2/outputs/combined_fatigue_features.csv")
    parser.add_argument("--genomic", default="sprint3/input_data/athlete_genomic_profiles.csv")
    parser.add_argument("--athlete-id", default="athlete_001")
    parser.add_argument("--bridge-output", default="sprint3/outputs/athlete_session_bridge.csv")
    parser.add_argument("--sprint2-bridged-output", default="sprint2/outputs/combined_fatigue_features_with_athletes.csv")
    parser.add_argument("--output", default="sprint3/outputs/integrated_athlete_profiles.csv")
    parser.add_argument("--report-output", default="sprint3/outputs/sprint2_sprint3_integration_report.md")
    args = parser.parse_args()

    fatigue = normalize_sprint2_columns(load_csv(args.sprint2))
    athletes = load_csv(args.genomic)

    required_fatigue = ["session_id", "fatigue_score", "risk_level", "fatigue_prediction", "recommendation", "training_load"]
    missing = [column for column in required_fatigue if column not in fatigue.columns]
    if missing:
        raise ValueError(f"Sprint 2 dataset is missing required columns: {missing}")

    bridge = build_bridge(athletes, fatigue, args.athlete_id)
    Path(args.bridge_output).parent.mkdir(parents=True, exist_ok=True)
    bridge.to_csv(args.bridge_output, index=False)

    sprint2_bridged = bridge.merge(fatigue, on="session_id", how="left")
    Path(args.sprint2_bridged_output).parent.mkdir(parents=True, exist_ok=True)
    sprint2_bridged.to_csv(args.sprint2_bridged_output, index=False)

    sprint2_subset = fatigue[
        ["session_id", "fatigue_score", "risk_level", "fatigue_prediction", "recommendation", "training_load"]
    ].copy()
    sprint2_subset = sprint2_subset.rename(
        columns={
            "recommendation": "sprint2_recommendation",
            "training_load": "sprint2_training_load",
        }
    )

    integrated = bridge.merge(athletes, on="athlete_id", how="left").merge(sprint2_subset, on="session_id", how="left")
    integrated["risk_level_numeric"] = integrated["risk_level"].map(RISK_ORDER).fillna(0).astype(int)
    integrated["training_load"] = integrated["sprint2_training_load"].fillna(integrated["training_load"])

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    integrated.to_csv(args.output, index=False)
    write_report(
        args.report_output,
        args.sprint2,
        args.genomic,
        args.bridge_output,
        args.sprint2_bridged_output,
        args.output,
        integrated,
    )

    print(f"Saved athlete/session bridge to: {args.bridge_output}")
    print(f"Saved bridged Sprint 2 fatigue dataset to: {args.sprint2_bridged_output}")
    print(f"Saved integrated athlete profiles to: {args.output}")
    print(f"Saved integration report to: {args.report_output}")


if __name__ == "__main__":
    main()
