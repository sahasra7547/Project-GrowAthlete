import csv
import random
from collections import Counter
from pathlib import Path
from statistics import mean, pstdev


RANDOM_SEED = 42
ATHLETE_COUNT = 300

ACTN3_OPTIONS = ["RR", "RX", "XX"]
ACE_OPTIONS = ["II", "ID", "DD"]

ACTN3_WEIGHTS = [0.32, 0.48, 0.20]
ACE_WEIGHTS = [0.25, 0.50, 0.25]

FIELDS = [
    "athlete_id",
    "actn3_genotype",
    "ace_genotype",
    "height_cm",
    "weight_kg",
    "body_fat_percent",
    "recovery_time_hours",
    "resting_hr",
    "sleep_efficiency",
    "training_load",
    "sprint_performance_score",
    "endurance_score",
]


def clamp(value, low, high):
    return max(low, min(high, value))


def choice(options, weights):
    return random.choices(options, weights=weights, k=1)[0]


def genotype_effects(actn3, ace):
    sprint = 0
    endurance = 0

    if actn3 == "RR":
        sprint += 8
        endurance -= 2
    elif actn3 == "RX":
        sprint += 3
        endurance += 2
    else:
        sprint -= 2
        endurance += 8

    if ace == "II":
        endurance += 7
        sprint -= 1
    elif ace == "ID":
        sprint += 2
        endurance += 2
    else:
        sprint += 6
        endurance -= 2

    return sprint, endurance


def generate_athlete(index):
    actn3 = choice(ACTN3_OPTIONS, ACTN3_WEIGHTS)
    ace = choice(ACE_OPTIONS, ACE_WEIGHTS)
    sprint_effect, endurance_effect = genotype_effects(actn3, ace)

    height = clamp(random.gauss(176, 9), 150, 205)
    body_fat = clamp(random.gauss(14, 5), 5, 30)
    lean_mass_factor = (100 - body_fat) / 100
    weight = clamp((height - 100) * random.uniform(0.88, 1.12) * (1.04 - body_fat / 250), 48, 115)

    sleep_efficiency = clamp(random.gauss(84, 7), 60, 98)
    resting_hr = clamp(random.gauss(55, 7) - endurance_effect * 0.15 + body_fat * 0.12, 42, 78)
    training_load = clamp(random.gauss(62, 18), 15, 100)

    recovery_time = (
        18
        + training_load * 0.32
        + body_fat * 0.38
        - sleep_efficiency * 0.16
        + random.gauss(0, 5)
    )
    recovery_time = clamp(recovery_time, 8, 72)

    sprint_score = (
        61
        + sprint_effect
        + lean_mass_factor * 12
        - body_fat * 0.55
        - recovery_time * 0.09
        + random.gauss(0, 8)
    )
    endurance_score = (
        60
        + endurance_effect
        + sleep_efficiency * 0.18
        - resting_hr * 0.22
        - body_fat * 0.28
        - recovery_time * 0.06
        + random.gauss(0, 8)
    )

    return {
        "athlete_id": f"athlete_{index:03d}",
        "actn3_genotype": actn3,
        "ace_genotype": ace,
        "height_cm": round(height, 1),
        "weight_kg": round(weight, 1),
        "body_fat_percent": round(body_fat, 1),
        "recovery_time_hours": round(recovery_time, 1),
        "resting_hr": round(resting_hr),
        "sleep_efficiency": round(sleep_efficiency),
        "training_load": round(training_load),
        "sprint_performance_score": round(clamp(sprint_score, 20, 100), 1),
        "endurance_score": round(clamp(endurance_score, 20, 100), 1),
    }


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def numeric_stats(rows, field):
    values = [float(row[field]) for row in rows]
    return {
        "mean": mean(values),
        "std": pstdev(values),
        "min": min(values),
        "max": max(values),
    }


def grouped_mean(rows, group_field, value_field):
    groups = {}
    for row in rows:
        groups.setdefault(row[group_field], []).append(float(row[value_field]))
    return {key: mean(values) for key, values in groups.items()}


def distribution_table(counter, total):
    lines = ["| Genotype | Count | Percent |", "| --- | ---: | ---: |"]
    for genotype, count in sorted(counter.items()):
        lines.append(f"| {genotype} | {count} | {count / total * 100:.1f}% |")
    return "\n".join(lines)


def stats_table(rows):
    fields = [
        "height_cm",
        "weight_kg",
        "body_fat_percent",
        "recovery_time_hours",
        "resting_hr",
        "sleep_efficiency",
        "training_load",
        "sprint_performance_score",
        "endurance_score",
    ]
    lines = ["| Field | Mean | Std | Min | Max |", "| --- | ---: | ---: | ---: | ---: |"]
    for field in fields:
        stats = numeric_stats(rows, field)
        lines.append(
            f"| {field} | {stats['mean']:.2f} | {stats['std']:.2f} | "
            f"{stats['min']:.2f} | {stats['max']:.2f} |"
        )
    return "\n".join(lines)


def grouped_table(rows, group_field):
    sprint_means = grouped_mean(rows, group_field, "sprint_performance_score")
    endurance_means = grouped_mean(rows, group_field, "endurance_score")
    lines = [
        f"| {group_field} | Avg Sprint Score | Avg Endurance Score |",
        "| --- | ---: | ---: |",
    ]
    for genotype in sorted(sprint_means):
        lines.append(
            f"| {genotype} | {sprint_means[genotype]:.2f} | {endurance_means[genotype]:.2f} |"
        )
    return "\n".join(lines)


def write_summary(path, rows, csv_path):
    total = len(rows)
    actn3_counts = Counter(row["actn3_genotype"] for row in rows)
    ace_counts = Counter(row["ace_genotype"] for row in rows)

    lines = [
        "# Sprint 3 Genomic Dataset Summary",
        "",
        f"- Dataset: `{csv_path}`",
        f"- Synthetic athletes: {total}",
        "- Purpose: simulate sports-genetics and phenotype features for Sprint 3 clustering and workload analysis.",
        "",
        "## ACTN3 Genotype Distribution",
        "",
        distribution_table(actn3_counts, total),
        "",
        "## ACE Genotype Distribution",
        "",
        distribution_table(ace_counts, total),
        "",
        "## Descriptive Statistics",
        "",
        stats_table(rows),
        "",
        "## Literature-Inspired Trend Check",
        "",
        "### ACTN3 Group Means",
        "",
        grouped_table(rows, "actn3_genotype"),
        "",
        "### ACE Group Means",
        "",
        grouped_table(rows, "ace_genotype"),
        "",
        "## Notes",
        "",
        (
            "The dataset uses noisy, non-deterministic trends: ACTN3 RR is biased toward sprint/power, "
            "ACTN3 XX toward endurance, ACE II toward endurance, and ACE DD toward power. "
            "Individual outcomes still vary due to phenotype, recovery, training load, and random noise."
        ),
    ]

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    random.seed(RANDOM_SEED)
    rows = [generate_athlete(i + 1) for i in range(ATHLETE_COUNT)]

    csv_path = Path("sprint3/input_data/athlete_genomic_profiles.csv")
    summary_path = Path("sprint3/outputs/genomic_dataset_summary.md")

    write_csv(csv_path, rows)
    write_summary(summary_path, rows, csv_path)

    print(f"Saved Sprint 3 genomic dataset to: {csv_path}")
    print(f"Saved Sprint 3 dataset summary to: {summary_path}")


if __name__ == "__main__":
    main()
