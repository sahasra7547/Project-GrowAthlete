import argparse
import os
import re
import random
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("MPLCONFIGDIR", str(Path("sprint2") / ".matplotlib"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
    roc_auc_score,
)
from sklearn.preprocessing import LabelEncoder, StandardScaler, label_binarize


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


def set_reproducible(seed):
    random.seed(seed)
    np.random.seed(seed)
    tf.random.set_seed(seed)


def target_column(df):
    if "fatigue_risk" in df.columns:
        return "fatigue_risk"
    if "risk_level" in df.columns:
        return "risk_level"
    raise ValueError("Expected `fatigue_risk` or `risk_level` target column.")


def load_feature_matrix(path):
    df = pd.read_csv(path)
    missing = [column for column in FEATURE_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required features: {missing}")

    target = target_column(df)
    if "session_id" in df.columns:
        df = df.sort_values("session_id").reset_index(drop=True)
    return df, target


def create_sequences(features, labels, sequence_length):
    x_sequences = []
    y_sequences = []
    for end_idx in range(sequence_length - 1, len(features)):
        start_idx = end_idx - sequence_length + 1
        x_sequences.append(features[start_idx : end_idx + 1])
        y_sequences.append(labels[end_idx])
    return np.array(x_sequences), np.array(y_sequences)


def split_sequences(x, y, train_ratio=0.65, val_ratio=0.15):
    total = len(x)
    train_end = max(1, int(total * train_ratio))
    val_end = max(train_end + 1, int(total * (train_ratio + val_ratio)))
    val_end = min(val_end, total - 1)

    return (
        x[:train_end],
        y[:train_end],
        x[train_end:val_end],
        y[train_end:val_end],
        x[val_end:],
        y[val_end:],
    )


def scale_sequences(x_train, x_val, x_test):
    scaler = StandardScaler()
    feature_count = x_train.shape[-1]
    scaler.fit(x_train.reshape(-1, feature_count))

    def transform(x):
        original_shape = x.shape
        return scaler.transform(x.reshape(-1, feature_count)).reshape(original_shape)

    return transform(x_train), transform(x_val), transform(x_test)


def build_lstm_model(sequence_length, feature_count, class_count):
    model = tf.keras.Sequential(
        [
            tf.keras.layers.Input(shape=(sequence_length, feature_count)),
            tf.keras.layers.LSTM(32, return_sequences=False),
            tf.keras.layers.Dropout(0.25),
            tf.keras.layers.Dense(24, activation="relu"),
            tf.keras.layers.Dropout(0.15),
            tf.keras.layers.Dense(class_count, activation="softmax"),
        ]
    )
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


def train_model(model, x_train, y_train, x_val, y_val, model_path, epochs, batch_size):
    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=12,
            restore_best_weights=True,
        ),
        tf.keras.callbacks.ModelCheckpoint(
            filepath=str(model_path),
            monitor="val_loss",
            save_best_only=True,
        ),
    ]

    return model.fit(
        x_train,
        y_train,
        validation_data=(x_val, y_val),
        epochs=epochs,
        batch_size=batch_size,
        callbacks=callbacks,
        verbose=0,
    )


def evaluate_model(model, x_test, y_test, labels):
    probabilities = model.predict(x_test, verbose=0)
    predictions = probabilities.argmax(axis=1)

    accuracy = accuracy_score(y_test, predictions)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test,
        predictions,
        labels=list(range(len(labels))),
        average="weighted",
        zero_division=0,
    )
    matrix = confusion_matrix(y_test, predictions, labels=list(range(len(labels))))

    roc_auc = None
    try:
        if len(labels) == 2:
            roc_auc = roc_auc_score(y_test, probabilities[:, 1])
        elif len(set(y_test)) == len(labels):
            y_binary = label_binarize(y_test, classes=list(range(len(labels))))
            roc_auc = roc_auc_score(y_binary, probabilities, average="weighted", multi_class="ovr")
    except ValueError:
        roc_auc = None

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "roc_auc": roc_auc,
        "matrix": matrix,
        "predictions": predictions,
        "probabilities": probabilities,
    }


def save_training_history(history, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(9, 5))
    plt.plot(history.history.get("loss", []), label="Train loss")
    plt.plot(history.history.get("val_loss", []), label="Validation loss")
    plt.plot(history.history.get("accuracy", []), label="Train accuracy")
    plt.plot(history.history.get("val_accuracy", []), label="Validation accuracy")
    plt.xlabel("Epoch")
    plt.ylabel("Metric value")
    plt.title("LSTM Fatigue Model Training History")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


def save_confusion_matrix(matrix, labels, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(6.5, 5.5))
    plt.imshow(matrix, cmap="Blues")
    plt.title("LSTM Confusion Matrix")
    plt.colorbar()
    ticks = np.arange(len(labels))
    plt.xticks(ticks, labels, rotation=35, ha="right")
    plt.yticks(ticks, labels)
    plt.xlabel("Predicted")
    plt.ylabel("Actual")

    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            plt.text(j, i, str(matrix[i, j]), ha="center", va="center", color="black")

    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


def matrix_markdown(matrix, labels):
    header = "| Actual \\ Predicted | " + " | ".join(labels) + " |"
    divider = "| --- | " + " | ".join(["---"] * len(labels)) + " |"
    rows = [header, divider]
    for label, row in zip(labels, matrix):
        rows.append("| " + label + " | " + " | ".join(str(int(value)) for value in row) + " |")
    return "\n".join(rows)


def fmt(value):
    return "N/A" if value is None else f"{value:.4f}"


def write_lstm_report(path, metrics, labels, sequence_length, sample_counts, model_path, history_path, matrix_path):
    lines = [
        "# Sprint 2 LSTM Fatigue Classification Report",
        "",
        f"- Model file: `{model_path}`",
        f"- Training history chart: `{history_path}`",
        f"- Confusion matrix chart: `{matrix_path}`",
        f"- Sequence length: {sequence_length}",
        f"- Train sequences: {sample_counts['train']}",
        f"- Validation sequences: {sample_counts['val']}",
        f"- Test sequences: {sample_counts['test']}",
        f"- Classes: {', '.join(labels)}",
        "",
        "## Metrics",
        "",
        f"- Accuracy: {metrics['accuracy']:.4f}",
        f"- Precision: {metrics['precision']:.4f}",
        f"- Recall: {metrics['recall']:.4f}",
        f"- F1 score: {metrics['f1']:.4f}",
        f"- ROC-AUC: {fmt(metrics['roc_auc'])}",
        "",
        "## Confusion Matrix",
        "",
        matrix_markdown(metrics["matrix"], labels),
        "",
        "## Interpretation",
        "",
        (
            "The LSTM receives a sliding window of consecutive training sessions and predicts "
            "the fatigue-risk class for the final session in each window. This tests whether "
            "recent sequential workload history adds value beyond single-row tabular features."
        ),
    ]

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def extract_metric(report_text, names):
    for name in names:
        pattern = rf"{re.escape(name)}(?: on holdout rows)?:\s*([0-9.]+)"
        match = re.search(pattern, report_text, flags=re.IGNORECASE)
        if match:
            return float(match.group(1))
    return None


def read_existing_model_metrics(path):
    path = Path(path)
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8", errors="ignore")
    return {
        "accuracy": extract_metric(text, ["Accuracy"]),
        "precision": extract_metric(text, ["Precision"]),
        "recall": extract_metric(text, ["Recall"]),
        "f1": extract_metric(text, ["F1 score"]),
    }


def best_model_name(rows):
    valid_rows = [row for row in rows if row["accuracy"] is not None]
    if not valid_rows:
        return "Not available"
    return max(valid_rows, key=lambda row: row["accuracy"])["model"]


def write_comparison_report(path, lstm_metrics, xgb_metrics, ann_metrics):
    rows = [
        {"model": "LSTM", **{k: lstm_metrics.get(k) for k in ["accuracy", "precision", "recall", "f1"]}},
        {"model": "XGBoost", **xgb_metrics},
        {"model": "ANN", **ann_metrics},
    ]
    best = best_model_name(rows)

    def row_line(row):
        return (
            f"| {row['model']} | {fmt(row.get('accuracy'))} | {fmt(row.get('precision'))} | "
            f"{fmt(row.get('recall'))} | {fmt(row.get('f1'))} |"
        )

    lines = [
        "# Sprint 2 Model Comparison: LSTM vs XGBoost vs ANN",
        "",
        "## Metric Comparison",
        "",
        "| Model | Accuracy | Precision | Recall | F1 Score |",
        "| --- | --- | --- | --- | --- |",
    ]
    lines.extend(row_line(row) for row in rows)
    lines.extend(
        [
            "",
            f"## Best Performing Model",
            "",
            f"Best model by available accuracy: **{best}**.",
            "",
            "## Strengths And Weaknesses",
            "",
            "### XGBoost",
            "",
            (
                "Strength: strong tabular baseline with clear feature importance. "
                "Weakness: treats each session mostly as an independent row, so it does not naturally learn temporal fatigue accumulation."
            ),
            "",
            "### ANN",
            "",
            (
                "Strength: flexible nonlinear classifier over the combined feature matrix. "
                "Weakness: less interpretable than XGBoost and needs more labeled rows for stable evaluation."
            ),
            "",
            "### LSTM",
            "",
            (
                "Strength: models recent session history with sliding windows, which matches the idea of fatigue accumulating over time. "
                "Weakness: the current dataset is still small and partly synthetic, so sequential gains should be interpreted carefully."
            ),
            "",
            "## Does Sequential Modeling Add Predictive Value?",
            "",
        ]
    )

    xgb_accuracy = xgb_metrics.get("accuracy")
    lstm_accuracy = lstm_metrics.get("accuracy")
    if xgb_accuracy is not None and lstm_accuracy is not None and lstm_accuracy > xgb_accuracy:
        lines.append(
            "In this run, the LSTM outperformed XGBoost, suggesting that recent sequential training history may add predictive signal."
        )
    elif xgb_accuracy is not None and lstm_accuracy is not None:
        lines.append(
            "In this run, XGBoost matched or outperformed the LSTM. That suggests the current labels are mostly explained by session-level telemetry features rather than long temporal dependencies."
        )
    else:
        lines.append(
            "Sequential value cannot be fully judged because one or more comparison metrics were unavailable."
        )

    lines.append(
        "For a stronger conclusion, collect real chronological athlete sessions with verified fatigue labels and retrain all models on the same split."
    )

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Train Sprint 2 LSTM fatigue classifier")
    parser.add_argument(
        "--features-csv",
        default="sprint2/outputs/combined_fatigue_features.csv",
        help="Combined Sprint 2 feature matrix",
    )
    parser.add_argument("--sequence-length", type=int, default=5)
    parser.add_argument("--epochs", type=int, default=120)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--model-output", default="sprint2/models/lstm_fatigue_model.keras")
    parser.add_argument("--history-output", default="sprint2/outputs/lstm_training_history.png")
    parser.add_argument("--matrix-output", default="sprint2/outputs/lstm_confusion_matrix.png")
    parser.add_argument("--report-output", default="sprint2/outputs/lstm_classification_report.md")
    parser.add_argument(
        "--comparison-output",
        default="sprint2/outputs/lstm_vs_xgboost_vs_ann_report.md",
    )
    args = parser.parse_args()

    set_reproducible(args.seed)
    df, target = load_feature_matrix(args.features_csv)
    if len(df) < args.sequence_length + 5:
        raise ValueError("Not enough rows to create useful LSTM sequences.")

    encoder = LabelEncoder()
    labels_encoded = encoder.fit_transform(df[target].astype(str))
    labels = list(encoder.classes_)

    feature_frame = df[FEATURE_COLUMNS].apply(pd.to_numeric, errors="coerce").fillna(0.0)
    x_sequences, y_sequences = create_sequences(
        feature_frame.to_numpy(dtype=np.float32),
        labels_encoded,
        args.sequence_length,
    )

    x_train, y_train, x_val, y_val, x_test, y_test = split_sequences(x_sequences, y_sequences)
    x_train, x_val, x_test = scale_sequences(x_train, x_val, x_test)

    model = build_lstm_model(args.sequence_length, len(FEATURE_COLUMNS), len(labels))
    history = train_model(
        model,
        x_train,
        y_train,
        x_val,
        y_val,
        args.model_output,
        args.epochs,
        args.batch_size,
    )

    best_model = tf.keras.models.load_model(args.model_output)
    metrics = evaluate_model(best_model, x_test, y_test, labels)

    save_training_history(history, args.history_output)
    save_confusion_matrix(metrics["matrix"], labels, args.matrix_output)
    write_lstm_report(
        args.report_output,
        metrics,
        labels,
        args.sequence_length,
        {"train": len(x_train), "val": len(x_val), "test": len(x_test)},
        args.model_output,
        args.history_output,
        args.matrix_output,
    )

    xgb_metrics = read_existing_model_metrics("sprint2/outputs/xgboost_fatigue_report.md")
    ann_metrics = read_existing_model_metrics("sprint2/outputs/ann_fatigue_model_report.md")
    write_comparison_report(args.comparison_output, metrics, xgb_metrics, ann_metrics)

    print(f"Saved LSTM model to: {args.model_output}")
    print(f"Saved training history to: {args.history_output}")
    print(f"Saved confusion matrix to: {args.matrix_output}")
    print(f"Saved LSTM report to: {args.report_output}")
    print(f"Saved model comparison report to: {args.comparison_output}")


if __name__ == "__main__":
    main()
