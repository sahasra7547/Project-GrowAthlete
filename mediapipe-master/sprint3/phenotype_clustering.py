import argparse
import os
import pickle
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path("sprint3") / ".matplotlib"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


FEATURES = [
    "actn3_power_score",
    "actn3_endurance_score",
    "ace_power_score",
    "ace_endurance_score",
    "body_fat_percent",
    "recovery_time_hours",
    "sleep_efficiency",
    "fatigue_score",
    "risk_level_numeric",
    "training_load",
]

REPORT_FEATURES = [
    "body_fat_percent",
    "recovery_time_hours",
    "resting_hr",
    "sleep_efficiency",
    "sprint_performance_score",
    "endurance_score",
    "fatigue_score",
    "risk_level_numeric",
    "training_load",
]

LABEL_CANDIDATES = [
    "High Recovery / Power",
    "Balanced Athlete",
    "Endurance Dominant",
    "Recovery Limited",
    "Power Recovery Limited",
    "Aerobic Recovery Efficient",
]


def load_data(path):
    df = pd.read_csv(path)
    df = add_encoded_features(df)
    missing = [feature for feature in FEATURES if feature not in df.columns]
    if missing:
        raise ValueError(f"Missing required clustering features: {missing}")
    return df


def add_encoded_features(df):
    encoded = df.copy()
    encoded["actn3_power_score"] = encoded["actn3_genotype"].map({"RR": 1.0, "RX": 0.5, "XX": 0.0}).fillna(0.5)
    encoded["actn3_endurance_score"] = encoded["actn3_genotype"].map({"RR": 0.0, "RX": 0.5, "XX": 1.0}).fillna(0.5)
    encoded["ace_power_score"] = encoded["ace_genotype"].map({"DD": 1.0, "ID": 0.5, "II": 0.0}).fillna(0.5)
    encoded["ace_endurance_score"] = encoded["ace_genotype"].map({"DD": 0.0, "ID": 0.5, "II": 1.0}).fillna(0.5)
    if "risk_level_numeric" not in encoded.columns and "risk_level" in encoded.columns:
        encoded["risk_level_numeric"] = encoded["risk_level"].map({"Low": 0, "Moderate": 1, "High": 2}).fillna(0)
    if "fatigue_score" not in encoded.columns:
        encoded["fatigue_score"] = 0.0
    return encoded


def normalize_features(df):
    scaler = StandardScaler()
    matrix = scaler.fit_transform(df[FEATURES].fillna(df[FEATURES].median()))
    return scaler, matrix


def evaluate_cluster_counts(matrix, min_k=2, max_k=8):
    records = []
    for k in range(min_k, max_k + 1):
        model = KMeans(n_clusters=k, random_state=42, n_init=20)
        labels = model.fit_predict(matrix)
        records.append(
            {
                "k": k,
                "inertia": model.inertia_,
                "silhouette": silhouette_score(matrix, labels),
            }
        )
    return records


def choose_best_k(records):
    return max(records, key=lambda item: item["silhouette"])["k"]


def train_kmeans(matrix, k):
    model = KMeans(n_clusters=k, random_state=42, n_init=30)
    labels = model.fit_predict(matrix)
    return model, labels


def cluster_profiles(df):
    available = [feature for feature in REPORT_FEATURES if feature in df.columns]
    grouped = df.groupby("cluster_id")[available].mean()
    return grouped


def label_clusters(df):
    profiles = cluster_profiles(df)
    labels = {}
    used = set()

    for cluster_id, row in profiles.iterrows():
        recovery_strength = row["sleep_efficiency"] - row["recovery_time_hours"] * 0.6 - row["resting_hr"] * 0.25
        power_strength = row["sprint_performance_score"] - row["endurance_score"]
        endurance_strength = row["endurance_score"] - row["sprint_performance_score"]
        recovery_limited = row["recovery_time_hours"] + row["resting_hr"] * 0.35 + row["body_fat_percent"] * 0.5
        fatigue_pressure = row.get("fatigue_score", 0) + row.get("risk_level_numeric", 0) * 12

        if fatigue_pressure >= profiles.apply(
            lambda r: r.get("fatigue_score", 0) + r.get("risk_level_numeric", 0) * 12,
            axis=1,
        ).quantile(0.75) or recovery_limited >= profiles.apply(
            lambda r: r["recovery_time_hours"] + r["resting_hr"] * 0.35 + r["body_fat_percent"] * 0.5,
            axis=1,
        ).quantile(0.75):
            label = "Recovery Limited"
        elif power_strength > 5 and recovery_strength > profiles.apply(
            lambda r: r["sleep_efficiency"] - r["recovery_time_hours"] * 0.6 - r["resting_hr"] * 0.25,
            axis=1,
        ).median():
            label = "High Recovery / Power"
        elif endurance_strength > 4:
            label = "Endurance Dominant"
        else:
            label = "Balanced Athlete"

        if label in used:
            for candidate in LABEL_CANDIDATES:
                if candidate not in used:
                    label = candidate
                    break
        used.add(label)
        labels[cluster_id] = label

    return labels


def save_model(path, model, scaler, cluster_labels, features):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        pickle.dump(
            {
                "model": model,
                "scaler": scaler,
                "cluster_labels": cluster_labels,
                "features": features,
            },
            f,
        )


def save_elbow_curve(records, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    ks = [item["k"] for item in records]
    inertias = [item["inertia"] for item in records]
    silhouettes = [item["silhouette"] for item in records]

    fig, ax1 = plt.subplots(figsize=(9, 5))
    ax1.plot(ks, inertias, marker="o", color="#2563eb", label="Inertia")
    ax1.set_xlabel("Cluster count (k)")
    ax1.set_ylabel("Inertia", color="#2563eb")
    ax1.tick_params(axis="y", labelcolor="#2563eb")

    ax2 = ax1.twinx()
    ax2.plot(ks, silhouettes, marker="s", color="#dc2626", label="Silhouette")
    ax2.set_ylabel("Silhouette score", color="#dc2626")
    ax2.tick_params(axis="y", labelcolor="#dc2626")

    plt.title("Sprint 3 K-Means Cluster Count Evaluation")
    fig.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


def save_cluster_visualization(matrix, labels, named_labels, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pca = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(matrix)

    plt.figure(figsize=(9, 6))
    for cluster_id in sorted(set(labels)):
        mask = labels == cluster_id
        plt.scatter(
            coords[mask, 0],
            coords[mask, 1],
            s=38,
            alpha=0.78,
            label=named_labels[cluster_id],
        )
    plt.xlabel("PCA component 1")
    plt.ylabel("PCA component 2")
    plt.title("Sprint 3 Athlete Phenotype Clusters")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


def write_csv(path, df):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def markdown_table(df):
    features = list(df.columns)
    lines = ["| Cluster | " + " | ".join(features) + " |", "| --- | " + " | ".join(["---:"] * len(features)) + " |"]
    for cluster_id, row in df.iterrows():
        lines.append(
            "| "
            + str(cluster_id)
            + " | "
            + " | ".join(f"{row[feature]:.2f}" for feature in features)
            + " |"
        )
    return "\n".join(lines)


def write_report(path, df, evaluation_records, best_k, cluster_labels):
    cluster_means = cluster_profiles(df)
    cluster_sizes = df.groupby(["cluster_id", "phenotype_group"]).size().reset_index(name="count")

    lines = [
        "# Sprint 3 Phenotype Clustering Report",
        "",
        f"- Input athletes: {len(df)}",
        f"- Selected cluster count: {best_k}",
        "- Method: StandardScaler normalization + K-Means clustering",
        "- Selection criteria: elbow curve and highest silhouette score",
        "- Sprint 2 fatigue features included: fatigue score, risk level, and training load",
        "- Genomic-inspired features included: ACTN3 and ACE encoded power/endurance tendency scores",
        "",
        "## Cluster Count Evaluation",
        "",
        "| k | Inertia | Silhouette Score |",
        "| ---: | ---: | ---: |",
    ]
    for item in evaluation_records:
        lines.append(f"| {item['k']} | {item['inertia']:.2f} | {item['silhouette']:.4f} |")

    lines.extend(["", "## Cluster Sizes", "", "| Cluster ID | Phenotype Group | Count |", "| ---: | --- | ---: |"])
    for _, row in cluster_sizes.iterrows():
        lines.append(f"| {row['cluster_id']} | {row['phenotype_group']} | {row['count']} |")

    lines.extend(
        [
            "",
            "## Feature Distributions By Cluster",
            "",
            markdown_table(cluster_means),
            "",
            "## Biomechanical Implications",
            "",
        ]
    )

    for cluster_id, label in sorted(cluster_labels.items()):
        row = cluster_means.loc[cluster_id]
        if label == "High Recovery / Power":
            implication = (
                "This group combines strong sprint output with relatively efficient recovery markers. "
                "They may tolerate high-intensity sprint blocks, but workload should still be monitored after repeated maximal efforts."
            )
        elif label == "Endurance Dominant":
            implication = (
                "This group trends toward stronger endurance capacity than sprint output. "
                "Training emphasis can include aerobic volume and gradual speed exposure."
            )
        elif label == "Recovery Limited":
            implication = (
                "This group shows slower recovery or weaker recovery markers. "
                "They may need lower session density, recovery monitoring, and cautious progression."
            )
        else:
            implication = (
                "This group has mixed performance and recovery traits. "
                "They are suitable for balanced programming with individual workload adjustments."
            )
        lines.extend(
            [
                f"### Cluster {cluster_id}: {label}",
                "",
                (
                    f"Mean body fat {row['body_fat_percent']:.1f}%, recovery time "
                    f"{row['recovery_time_hours']:.1f}h, resting HR {row['resting_hr']:.1f} bpm, "
                    f"sprint score {row['sprint_performance_score']:.1f}, endurance score {row['endurance_score']:.1f}, "
                    f"fatigue score {row.get('fatigue_score', 0):.1f}, training load {row.get('training_load', 0):.1f}."
                ),
                "",
                implication,
                "",
            ]
        )

    lines.extend(
        [
            "## Research Caution",
            "",
            (
                "These clusters are exploratory phenotype groups. They should not be treated as fixed genetic ceilings. "
                "Training environment, recovery behavior, coaching quality, psychology, nutrition, and injury history remain critical."
            ),
        ]
    )

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Sprint 3 athlete phenotype clustering")
    parser.add_argument("--input", default="sprint3/outputs/integrated_athlete_profiles.csv")
    parser.add_argument("--model-output", default="sprint3/models/kmeans_recovery_model.pkl")
    parser.add_argument("--csv-output", default="sprint3/outputs/clustered_athletes.csv")
    parser.add_argument("--elbow-output", default="sprint3/outputs/elbow_curve.png")
    parser.add_argument("--cluster-plot-output", default="sprint3/outputs/cluster_visualization.png")
    parser.add_argument("--report-output", default="sprint3/outputs/cluster_analysis_report.md")
    parser.add_argument("--min-k", type=int, default=2)
    parser.add_argument("--max-k", type=int, default=6)
    args = parser.parse_args()

    df = load_data(args.input)
    scaler, matrix = normalize_features(df)
    evaluation_records = evaluate_cluster_counts(matrix, args.min_k, args.max_k)
    best_k = choose_best_k(evaluation_records)
    model, labels = train_kmeans(matrix, best_k)

    clustered = df.copy()
    clustered["cluster_id"] = labels
    cluster_labels = label_clusters(clustered)
    clustered["phenotype_group"] = clustered["cluster_id"].map(cluster_labels)

    save_model(args.model_output, model, scaler, cluster_labels, FEATURES)
    write_csv(args.csv_output, clustered)
    save_elbow_curve(evaluation_records, args.elbow_output)
    save_cluster_visualization(matrix, labels, cluster_labels, args.cluster_plot_output)
    write_report(args.report_output, clustered, evaluation_records, best_k, cluster_labels)

    print(f"Saved K-Means model to: {args.model_output}")
    print(f"Saved clustered athletes to: {args.csv_output}")
    print(f"Saved elbow curve to: {args.elbow_output}")
    print(f"Saved cluster visualization to: {args.cluster_plot_output}")
    print(f"Saved cluster report to: {args.report_output}")


if __name__ == "__main__":
    main()
