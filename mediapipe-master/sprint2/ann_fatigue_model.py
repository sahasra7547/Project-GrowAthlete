import argparse
import os
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler


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


def available_features(df):
    return [column for column in FEATURE_COLUMNS if column in df.columns]


def build_model(input_dim, class_count):
    model = tf.keras.Sequential(
        [
            tf.keras.layers.Input(shape=(input_dim,)),
            tf.keras.layers.Dense(16, activation="relu"),
            tf.keras.layers.Dropout(0.1),
            tf.keras.layers.Dense(8, activation="relu"),
            tf.keras.layers.Dense(class_count, activation="softmax"),
        ]
    )
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.01),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


def write_report(path, accuracy, labels, report, features, model_path):
    lines = [
        "# Sprint 2 ANN Fatigue Model Report",
        "",
        f"- Model output: `{model_path}`",
        f"- Accuracy on holdout rows: {accuracy:.3f}",
        f"- Classes: {', '.join(labels)}",
        f"- Feature count: {len(features)}",
        "",
        "## Features",
        "",
    ]
    lines.extend([f"- {feature}" for feature in features])
    lines.extend(["", "## Classification Report", "", "```text", report, "```", ""])
    lines.append(
        "Note: this ANN is a Sprint 2 prototype. The dataset is small, so the rule-based score remains the main explainable baseline until more labeled sessions are collected."
    )

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Train a small Sprint 2 ANN risk classifier")
    parser.add_argument(
        "--features-csv",
        default="sprint2/outputs/athlete_hr_predict_fatigue_features.csv",
        help="Sprint 2 combined feature CSV",
    )
    parser.add_argument(
        "--model-output",
        default="sprint2/models/ann_fatigue_model.keras",
        help="Saved Keras model path",
    )
    parser.add_argument(
        "--report-output",
        default="sprint2/outputs/ann_fatigue_model_report.md",
        help="ANN report path",
    )
    args = parser.parse_args()

    df = pd.read_csv(args.features_csv)
    features = available_features(df)
    if len(features) < 3:
        raise ValueError("Not enough numeric features found for ANN training.")

    x = df[features].fillna(0).astype(float).to_numpy()
    encoder = LabelEncoder()
    y = encoder.fit_transform(df["risk_level"].astype(str))

    scaler = StandardScaler()
    x = scaler.fit_transform(x)

    stratify = y if len(set(y)) > 1 and min(np.bincount(y)) >= 2 else None
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.25, random_state=42, stratify=stratify
    )

    model = build_model(x_train.shape[1], len(encoder.classes_))
    model.fit(x_train, y_train, epochs=80, batch_size=4, verbose=0)

    probabilities = model.predict(x_test, verbose=0)
    predictions = probabilities.argmax(axis=1)
    accuracy = accuracy_score(y_test, predictions)
    report = classification_report(
        y_test,
        predictions,
        labels=list(range(len(encoder.classes_))),
        target_names=list(encoder.classes_),
        zero_division=0,
    )

    model_path = Path(args.model_output)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(model_path)

    write_report(
        args.report_output,
        accuracy,
        list(encoder.classes_),
        report,
        features,
        model_path,
    )

    print(f"Saved Sprint 2 ANN model to: {model_path}")
    print(f"Saved Sprint 2 ANN report to: {args.report_output}")


if __name__ == "__main__":
    main()
