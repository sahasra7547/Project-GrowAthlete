import argparse
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path("sprint2") / ".matplotlib"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

try:
    from xgboost import XGBClassifier
except ImportError as exc:
    raise SystemExit(
        "Missing dependency: xgboost. Install it with:\n"
        "  python -m pip install xgboost\n"
        "Then rerun:\n"
        "  python sprint2\\xgboost_fatigue_model.py"
    ) from exc


FEATURE_COLUMNS = [
    "resting_heart_rate",
    "sleep_efficiency",
    "spo2",
    "gps_distance_km",
    "sprint_count",
    "match_load",
    "avg_heart_rate",
    "max_heart_rate",
    "avg_speed_mps",
    "max_speed_mps",
    "avg_cadence",
    "duration_sec",
    "avg_right_knee_angle",
    "avg_left_knee_angle",
    "avg_knee_angle_difference",
    "avg_hip_alignment_abs_angle",
    "avg_right_ankle_deviation_angle",
    "avg_left_ankle_deviation_angle",
    "pose_detection_coverage",
]


def load_dataset(path):
    df = pd.read_csv(path)
    missing = [column for column in FEATURE_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required feature columns: {missing}")
    if "fatigue_risk" in df.columns:
        target_column = "fatigue_risk"
    elif "risk_level" in df.columns:
        target_column = "risk_level"
    else:
        raise ValueError("Dataset must include fatigue_risk or risk_level as the target.")
    return df, target_column


def train_model(df, target_column):
    x = df[FEATURE_COLUMNS].fillna(0).astype(float)
    encoder = LabelEncoder()
    y = encoder.fit_transform(df[target_column].astype(str))

    stratify = y if min(pd.Series(y).value_counts()) >= 2 else None
    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.25,
        random_state=42,
        stratify=stratify,
    )

    model = XGBClassifier(
        n_estimators=120,
        max_depth=3,
        learning_rate=0.08,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="multi:softprob",
        eval_metric="mlogloss",
        random_state=42,
    )
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    return model, encoder, x_test, y_test, predictions


def metric_summary(y_true, predictions, labels):
    accuracy = accuracy_score(y_true, predictions)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true,
        predictions,
        labels=list(range(len(labels))),
        average="weighted",
        zero_division=0,
    )
    matrix = confusion_matrix(y_true, predictions, labels=list(range(len(labels))))
    return accuracy, precision, recall, f1, matrix


def feature_importance(model):
    importances = model.feature_importances_
    pairs = sorted(
        zip(FEATURE_COLUMNS, importances),
        key=lambda item: item[1],
        reverse=True,
    )
    return pairs


def save_feature_chart(pairs, path):
    top_pairs = pairs[:12]
    labels = [name for name, _ in reversed(top_pairs)]
    values = [value for _, value in reversed(top_pairs)]

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(10, 6))
    plt.barh(labels, values, color="#2563eb")
    plt.xlabel("XGBoost feature importance")
    plt.title("Sprint 2 Fatigue Classifier Feature Importance")
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


def format_matrix(matrix, labels):
    header = "| Actual \\ Predicted | " + " | ".join(labels) + " |"
    divider = "| --- | " + " | ".join(["---"] * len(labels)) + " |"
    rows = [header, divider]
    for label, row in zip(labels, matrix):
        rows.append("| " + label + " | " + " | ".join(str(int(v)) for v in row) + " |")
    return "\n".join(rows)


def write_report(path, accuracy, precision, recall, f1, matrix, labels, pairs, model_path, chart_path):
    lines = [
        "# Sprint 2 XGBoost Fatigue Classification Report",
        "",
        f"- Model file: `{model_path}`",
        f"- Feature importance chart: `{chart_path}`",
        f"- Accuracy: {accuracy:.4f}",
        f"- Precision: {precision:.4f}",
        f"- Recall: {recall:.4f}",
        f"- F1 score: {f1:.4f}",
        "",
        "## Confusion Matrix",
        "",
        format_matrix(matrix, labels),
        "",
        "## Feature Importance Ranking",
        "",
    ]
    for rank, (name, importance) in enumerate(pairs, start=1):
        lines.append(f"{rank}. {name}: {importance:.6f}")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            (
                "This XGBoost model is a Sprint 2 baseline for fatigue-risk classification. "
                "It combines wearable/workload telemetry with Sprint 1 biomechanical features."
            ),
        ]
    )

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Train Sprint 2 XGBoost fatigue classifier")
    parser.add_argument(
        "--features-csv",
        default="sprint2/outputs/combined_fatigue_features.csv",
        help="Combined Sprint 2 feature CSV",
    )
    parser.add_argument(
        "--model-output",
        default="sprint2/models/xgboost_fatigue_model.json",
        help="XGBoost model output path",
    )
    parser.add_argument(
        "--report-output",
        default="sprint2/outputs/xgboost_fatigue_report.md",
        help="Markdown report output path",
    )
    parser.add_argument(
        "--chart-output",
        default="sprint2/outputs/xgboost_feature_importance.png",
        help="Feature importance chart output path",
    )
    args = parser.parse_args()

    df, target_column = load_dataset(args.features_csv)
    model, encoder, _, y_test, predictions = train_model(df, target_column)
    labels = list(encoder.classes_)
    accuracy, precision, recall, f1, matrix = metric_summary(y_test, predictions, labels)
    pairs = feature_importance(model)

    model_path = Path(args.model_output)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model.save_model(model_path)

    save_feature_chart(pairs, args.chart_output)
    write_report(
        args.report_output,
        accuracy,
        precision,
        recall,
        f1,
        matrix,
        labels,
        pairs,
        model_path,
        args.chart_output,
    )

    print(f"Saved XGBoost model to: {model_path}")
    print(f"Saved XGBoost report to: {args.report_output}")
    print(f"Saved feature importance chart to: {args.chart_output}")


if __name__ == "__main__":
    main()
