import argparse
import csv
from collections import Counter
from pathlib import Path
from statistics import mean


def to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def clamp(value, low, high):
    return max(low, min(high, value))


def genomic_bias(row):
    actn3 = row.get("actn3_genotype")
    ace = row.get("ace_genotype")
    sprint_bias = 0.0
    endurance_bias = 0.0

    if actn3 == "RR":
        sprint_bias += 0.03
    elif actn3 == "XX":
        endurance_bias += 0.03

    if ace == "DD":
        sprint_bias += 0.02
    elif ace == "II":
        endurance_bias += 0.02

    return sprint_bias, endurance_bias


def base_multiplier(phenotype):
    if "High Recovery" in phenotype:
        return 1.20
    if "Recovery Limited" in phenotype:
        return 0.80
    if "Balanced" in phenotype:
        return 1.00
    if "Endurance" in phenotype:
        return 1.03
    return 0.98


def fatigue_adjustment(row):
    risk_level = row.get("risk_level", "Low")
    fatigue_score = to_float(row.get("fatigue_score"))

    if risk_level == "High" or fatigue_score >= 75:
        return -0.18
    if risk_level == "Moderate" or fatigue_score >= 50:
        return -0.08
    if fatigue_score < 40:
        return 0.03
    return 0.0


def recovery_pressure(row):
    recovery_time = to_float(row.get("recovery_time_hours"))
    resting_hr = to_float(row.get("resting_hr"))
    sleep = to_float(row.get("sleep_efficiency"))
    body_fat = to_float(row.get("body_fat_percent"))

    pressure = 0.0
    pressure += max(recovery_time - 30, 0) * 0.006
    pressure += max(resting_hr - 60, 0) * 0.007
    pressure += max(82 - sleep, 0) * 0.008
    pressure += max(body_fat - 18, 0) * 0.006
    return pressure


def recovery_priority(row):
    pressure = recovery_pressure(row)
    if row.get("risk_level") == "High" or "Recovery Limited" in row.get("phenotype_group", "") or pressure >= 0.16:
        return "High"
    if row.get("risk_level") == "Moderate" or pressure >= 0.07:
        return "Moderate"
    return "Low"


def risk_flag(row, multiplier):
    training_load = to_float(row.get("training_load"))
    recovery_time = to_float(row.get("recovery_time_hours"))
    sleep = to_float(row.get("sleep_efficiency"))
    resting_hr = to_float(row.get("resting_hr"))

    fatigue_score = to_float(row.get("fatigue_score"))
    risk_level = row.get("risk_level", "Low")

    if risk_level == "High" or fatigue_score >= 80:
        return "High"
    if training_load >= 85 and (recovery_time >= 34 or sleep < 78 or resting_hr > 64):
        return "High"
    if risk_level == "Moderate" or multiplier < 0.9 or recovery_time >= 32 or sleep < 82:
        return "Moderate"
    return "Low"


def multiplier_bounds(phenotype, risk_level):
    if risk_level == "High":
        return 0.65, 0.90
    if risk_level == "Moderate":
        return 0.75, 1.00
    if "High Recovery" in phenotype:
        return 1.15, 1.25
    if "Recovery Limited" in phenotype:
        return 0.70, 0.90
    if "Balanced" in phenotype:
        return 0.95, 1.05
    if "Endurance" in phenotype:
        return 0.95, 1.08
    return 0.90, 1.05


def recommendation_for(row):
    phenotype = row.get("phenotype_group", "Balanced Athlete")
    training_load = to_float(row.get("training_load"))
    sprint_bias, endurance_bias = genomic_bias(row)
    pressure = recovery_pressure(row)

    multiplier = base_multiplier(phenotype)
    multiplier += sprint_bias * 0.6
    multiplier += endurance_bias * 0.4
    multiplier += fatigue_adjustment(row)
    multiplier -= pressure

    low, high = multiplier_bounds(phenotype, row.get("risk_level", "Low"))
    multiplier = clamp(multiplier, low, high)

    recommended_load = clamp(training_load * multiplier, 10, 115)
    adjustment_percent = (multiplier - 1.0) * 100

    output = dict(row)
    output["workload_multiplier"] = round(multiplier, 3)
    output["recommended_training_load"] = round(recommended_load, 1)
    output["recovery_priority"] = recovery_priority(row)
    output["workload_adjustment_percent"] = round(adjustment_percent, 1)
    output["athlete_risk_flag"] = risk_flag(row, multiplier)
    output["fatigue_aware_logic"] = (
        f"{row.get('risk_level', 'Low')} fatigue + {phenotype} phenotype"
    )
    return output


def markdown_distribution(counter):
    lines = ["| Category | Count |", "| --- | ---: |"]
    for key, value in sorted(counter.items()):
        lines.append(f"| {key} | {value} |")
    return "\n".join(lines)


def write_report(path, rows, input_path, output_path):
    phenotype_counts = Counter(row["phenotype_group"] for row in rows)
    priority_counts = Counter(row["recovery_priority"] for row in rows)
    risk_counts = Counter(row["athlete_risk_flag"] for row in rows)
    multipliers = [to_float(row["workload_multiplier"]) for row in rows]
    recommended = [to_float(row["recommended_training_load"]) for row in rows]
    original = [to_float(row["training_load"]) for row in rows]

    lines = [
        "# Sprint 3 Workload Recommendation Report",
        "",
        f"- Input clustered athletes: `{input_path}`",
        f"- Output recommendations: `{output_path}`",
        f"- Athletes processed: {len(rows)}",
        f"- Average current training load: {mean(original):.2f}",
        f"- Average recommended training load: {mean(recommended):.2f}",
        f"- Average workload multiplier: {mean(multipliers):.3f}",
        "",
        "## Recommendation Logic",
        "",
        "- High Recovery / Power athletes receive a workload multiplier in the 1.15-1.25 range.",
        "- Balanced athletes receive a workload multiplier in the 0.95-1.05 range.",
        "- Recovery Limited athletes receive a workload multiplier in the 0.70-0.90 range.",
        "- Sprint 2 High fatigue reduces the multiplier strongly, Moderate fatigue reduces it slightly, and Low fatigue can permit a small increase.",
        "- Final recommendations depend on both Sprint 2 fatigue state and Sprint 3 phenotype cluster.",
        "- ACTN3 RR and ACE DD add a small power-oriented workload bias.",
        "- ACTN3 XX and ACE II add a small endurance-oriented workload bias.",
        "- Recovery pressure from long recovery time, higher resting HR, lower sleep efficiency, and higher body fat reduces workload.",
        "- Risk flags increase when high workload overlaps with weak recovery markers.",
        "",
        "## Phenotype Distribution",
        "",
        markdown_distribution(phenotype_counts),
        "",
        "## Recovery Priority Distribution",
        "",
        markdown_distribution(priority_counts),
        "",
        "## Athlete Risk Flag Distribution",
        "",
        markdown_distribution(risk_counts),
        "",
        "## Practical Coaching Interpretation",
        "",
        (
            "The recommendation engine converts phenotype clusters into actionable training-load changes. "
            "Athletes with strong recovery profiles may receive modest workload increases, while recovery-limited "
            "athletes receive reduced load and higher recovery priority."
        ),
        "",
        "## Genomic Interpretation Warning",
        "",
        (
            "ACTN3 and ACE genotypes are treated only as probabilistic tendency signals. "
            "They must not be used as deterministic athletic limits or fixed predictions of performance. "
            "Training history, recovery behavior, coaching context, psychology, nutrition, and injury status remain essential."
        ),
    ]

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Sprint 3 adaptive workload recommendation engine")
    parser.add_argument("--input", default="sprint3/outputs/clustered_athletes.csv")
    parser.add_argument("--output", default="sprint3/outputs/integrated_workload_recommendations.csv")
    parser.add_argument("--report-output", default="sprint3/outputs/workload_recommendation_report.md")
    args = parser.parse_args()

    rows = read_csv(args.input)
    recommendations = [recommendation_for(row) for row in rows]
    write_csv(args.output, recommendations)
    write_report(args.report_output, recommendations, args.input, args.output)

    print(f"Saved workload recommendations to: {args.output}")
    print(f"Saved workload recommendation report to: {args.report_output}")


if __name__ == "__main__":
    main()
