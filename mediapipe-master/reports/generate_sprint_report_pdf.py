from pathlib import Path
import re

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "reports"
PDF_OUT = OUT_DIR / "sahasra_sprint1_3_detailed_project_report.pdf"
MD_OUT = OUT_DIR / "sahasra_sprint1_3_detailed_project_report.md"


def read_csv(path):
    return pd.read_csv(ROOT / path)


def read_text(path):
    full = ROOT / path
    return full.read_text(encoding="utf-8", errors="ignore") if full.exists() else ""


def metric_from_report(text, label):
    match = re.search(rf"{re.escape(label)}:\s*([0-9.]+)", text, flags=re.IGNORECASE)
    return match.group(1) if match else "N/A"


def make_styles():
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle(
            "ReportTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=29,
            textColor=colors.HexColor("#0B2545"),
            alignment=TA_CENTER,
            spaceAfter=12,
        ),
        "subtitle": ParagraphStyle(
            "ReportSubtitle",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#475467"),
            alignment=TA_CENTER,
            spaceAfter=12,
        ),
        "h1": ParagraphStyle(
            "Heading1Custom",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#1D4ED8"),
            spaceBefore=12,
            spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "Heading2Custom",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#0F766E"),
            spaceBefore=10,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "BodyCustom",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.5,
            textColor=colors.HexColor("#172033"),
            spaceAfter=7,
        ),
        "small": ParagraphStyle(
            "SmallCustom",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=10.5,
            textColor=colors.HexColor("#475467"),
            spaceAfter=4,
        ),
        "callout": ParagraphStyle(
            "Callout",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#7C2D12"),
            backColor=colors.HexColor("#FFF7ED"),
            borderColor=colors.HexColor("#FED7AA"),
            borderWidth=1,
            borderPadding=8,
            spaceBefore=8,
            spaceAfter=10,
        ),
    }
    return styles


def para(text, style):
    text = str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = text.replace("\n", "<br/>")
    return Paragraph(text, style)


def bullet(text, styles):
    return Paragraph("&#8226; " + text, styles["body"])


def table(data, widths=None, header=True):
    converted = []
    styles = make_styles()
    for row in data:
        converted.append([para(cell, styles["small"]) for cell in row])
    if widths is None:
        widths = [6.5 * inch / len(data[0])] * len(data[0])
    t = Table(converted, colWidths=widths, hAlign="LEFT", repeatRows=1 if header else 0)
    style = [
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D0D5DD")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]
    if header:
        style.extend(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF5")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0B2545")),
            ]
        )
    t.setStyle(TableStyle(style))
    return t


def add_image(story, rel_path, caption, styles, max_width=6.3 * inch):
    path = ROOT / rel_path
    if not path.exists():
        return
    img = Image(str(path))
    ratio = img.imageHeight / float(img.imageWidth)
    img.drawWidth = max_width
    img.drawHeight = max_width * ratio
    story.append(img)
    story.append(para(caption, styles["small"]))
    story.append(Spacer(1, 8))


def page_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#667085"))
    canvas.drawString(0.75 * inch, 0.45 * inch, "Sahasra Sports Biomechanics, Telemetry, and Genomic Simulation Report")
    canvas.drawRightString(7.75 * inch, 0.45 * inch, f"Page {doc.page}")
    canvas.restoreState()


def build_markdown(stats):
    lines = [
        "# Sahasra Sprint 1-3 Detailed Project Report",
        "",
        "## Executive Summary",
        "",
        "The project is now a single-athlete longitudinal prototype. Sprint 1 analyzes one athlete video. Sprint 2 combines that biomechanics profile with 150 synthetic training sessions for athlete_001. Sprint 3 consumes Sprint 2 fatigue outputs and produces recovery/workload recommendations.",
        "",
        f"- Sprint 1 frames: {stats['sprint1_rows']}",
        f"- Sprint 1 columns: {stats['sprint1_cols']}",
        f"- Sprint 2 sessions: {stats['sprint2_rows']}",
        f"- Unique athlete IDs after integration: {stats['unique_athletes']}",
        f"- XGBoost accuracy: {stats['xgb_accuracy']}",
        f"- LSTM accuracy: {stats['lstm_accuracy']}",
        f"- ANN accuracy: {stats['ann_accuracy']}",
        "",
        "## Readiness",
        "",
        "READY TO CONTINUE TO SPRINT 4 AS A PROTOTYPE.",
        "",
        "Remaining limitations: no true multi-angle video, no cutting/jumping examples, synthetic telemetry, synthetic genomic data, no clinically validated injury labels, and static dashboard rather than live streaming.",
    ]
    return "\n".join(lines)


def build_pdf():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    styles = make_styles()

    sprint1 = read_csv("sprint1/outputs/special_olympics_running_enhanced.csv")
    sprint2 = read_csv("sprint2/outputs/combined_fatigue_features.csv")
    sprint2_linked = read_csv("sprint2/outputs/combined_fatigue_features_with_athletes.csv")
    integrated = read_csv("sprint3/outputs/integrated_athlete_profiles.csv")
    recs = read_csv("sprint3/outputs/integrated_workload_recommendations.csv")

    xgb_report = read_text("sprint2/outputs/xgboost_fatigue_report.md")
    lstm_report = read_text("sprint2/outputs/lstm_classification_report.md")
    ann_report = read_text("sprint2/outputs/ann_fatigue_model_report.md")

    stats = {
        "sprint1_rows": len(sprint1),
        "sprint1_cols": len(sprint1.columns),
        "sprint2_rows": len(sprint2),
        "unique_athletes": sprint2_linked["athlete_id"].nunique(),
        "xgb_accuracy": metric_from_report(xgb_report, "Accuracy"),
        "xgb_precision": metric_from_report(xgb_report, "Precision"),
        "xgb_recall": metric_from_report(xgb_report, "Recall"),
        "xgb_f1": metric_from_report(xgb_report, "F1 score"),
        "lstm_accuracy": metric_from_report(lstm_report, "Accuracy"),
        "lstm_precision": metric_from_report(lstm_report, "Precision"),
        "lstm_recall": metric_from_report(lstm_report, "Recall"),
        "lstm_f1": metric_from_report(lstm_report, "F1 score"),
        "ann_accuracy": metric_from_report(ann_report, "Accuracy on holdout rows"),
    }

    risk_counts = sprint2["risk_level"].value_counts().to_dict()
    phenotype_counts = recs["phenotype_group"].value_counts().to_dict()
    priority_counts = recs["recovery_priority"].value_counts().to_dict()

    story = []
    story.append(Spacer(1, 0.25 * inch))
    story.append(para("Sahasra Sprint 1-3 Detailed Project Report", styles["title"]))
    story.append(
        para(
            "Sports Biomechanics, Fatigue Prediction, Genomic-Inspired Recovery Clustering, and Workload Recommendation Prototype",
            styles["subtitle"],
        )
    )
    story.append(Spacer(1, 0.15 * inch))
    story.append(
        table(
            [
                ["Project Mode", "Single-athlete longitudinal prototype"],
                ["Primary Athlete", "athlete_001"],
                ["Sprint 1 Input", "One athlete video"],
                ["Sprint 2 Sessions", f"{stats['sprint2_rows']} synthetic training sessions"],
                ["Primary Dashboard Model", "XGBoost"],
                ["Readiness", "Ready to continue to Sprint 4 as a prototype"],
            ],
            widths=[2.2 * inch, 4.3 * inch],
            header=False,
        )
    )
    story.append(Spacer(1, 12))
    story.append(
        para(
            "Important interpretation: the current system analyzes one video-tracked athlete. The 150 rows shown in Sprint 2 and the dashboard are synthetic longitudinal sessions for athlete_001, not 150 different real athletes.",
            styles["callout"],
        )
    )

    story.append(PageBreak())
    story.append(para("1. Executive Summary", styles["h1"]))
    story.append(
        para(
            "The Sprint 1-3 pipeline is now connected end to end. Sprint 1 extracts lower-body biomechanics from an athlete video. Sprint 2 combines those biomechanics with wearable-style telemetry and trains fatigue risk models. Sprint 3 consumes Sprint 2 fatigue state, integrates genomic-inspired profile features, clusters recovery-performance phenotype states, and generates fatigue-aware workload recommendations.",
            styles["body"],
        )
    )
    story.append(
        table(
            [
                ["Area", "Current Implementation", "Status"],
                ["Sprint 1", "MediaPipe pose extraction, 33 landmarks, knee/hip/ankle metrics, overlay video", "Implemented"],
                ["Sprint 2", "150-session telemetry fusion, XGBoost, LSTM, ANN, dashboard", "Implemented"],
                ["Sprint 3", "ACTN3/ACE profile, K-Means clustering, workload recommendations", "Implemented"],
                ["Integration", "Sprint 2 fatigue outputs feed Sprint 3 for athlete_001", "Connected"],
                ["Limitations", "Synthetic telemetry/genomics, no live sensor ingestion, no clinical injury labels", "Prototype caveat"],
            ],
            widths=[1.2 * inch, 4.0 * inch, 1.3 * inch],
        )
    )

    story.append(para("2. Expected Pipeline Flow", styles["h1"]))
    story.append(
        para(
            "Expected flow: Sprint 1 video biomechanics -> Sprint 2 telemetry fusion and fatigue prediction -> Sprint 3 genomic-inspired recovery clustering -> fatigue-aware workload recommendations.",
            styles["body"],
        )
    )
    add_image(story, "project_flow_diagram_v2.png", "Figure 1. Integrated project pipeline diagram.", styles)

    story.append(para("3. Sprint 1: Computer Vision and Biomechanics", styles["h1"]))
    story.append(
        para(
            "Sprint 1 processes one athlete video using MediaPipe pose tracking. It extracts a 33-point body coordinate map and computes lower-body biomechanics over time.",
            styles["body"],
        )
    )
    story.append(
        table(
            [
                ["Requirement", "Implemented Evidence"],
                ["Video ingestion", "sprint1/pose_pipeline.py processes video frame by frame"],
                ["33-point tracking", f"CSV has {stats['sprint1_cols']} columns including x/y/z/visibility for landmarks"],
                ["Knee flexion", "right_knee_angle, left_knee_angle, knee_angle_difference"],
                ["Ankle deviation", "right_ankle_deviation_angle, left_ankle_deviation_angle"],
                ["Hip alignment", "hip_alignment_angle, hip_alignment_abs_angle, hip_y_difference"],
                ["Outputs", "Enhanced CSV, annotated overlay MP4, biomechanical summary"],
            ],
            widths=[2.0 * inch, 4.5 * inch],
        )
    )
    story.append(para("Sprint 1 core question coverage", styles["h2"]))
    story.append(
        para(
            "The Sprint 1 core question asks whether real-time geometric movement mechanics can isolate soft-tissue degradation patterns before clinical strain symptoms emerge. The project covers the movement-mechanics part by producing frame-level geometric indicators. It does not yet prove clinical soft-tissue degradation because verified strain labels are not available.",
            styles["body"],
        )
    )

    story.append(para("4. Sprint 2: Telemetry Fusion and Fatigue Prediction", styles["h1"]))
    story.append(
        para(
            "Sprint 2 uses Sprint 1 biomechanics plus 150 synthetic wearable/workload sessions for athlete_001. The primary model for dashboard decision-making is XGBoost because it has an inspectable held-out split and feature importance.",
            styles["body"],
        )
    )
    story.append(
        table(
            [
                ["Input/Output", "Path or Description"],
                ["Telemetry input", "sprint2/input_data/synthetic_athlete_telemetry_fresh.csv"],
                ["Combined features", "sprint2/outputs/combined_fatigue_features.csv"],
                ["Athlete-linked features", "sprint2/outputs/combined_fatigue_features_with_athletes.csv"],
                ["XGBoost model", "sprint2/models/xgboost_fatigue_model.json"],
                ["Dashboard", "dashboard/athlete_fatigue_dashboard.html"],
            ],
            widths=[2.0 * inch, 4.5 * inch],
        )
    )
    story.append(
        table(
            [
                ["Model", "Accuracy", "Precision", "Recall", "F1", "Dashboard Use"],
                ["XGBoost", stats["xgb_accuracy"], stats["xgb_precision"], stats["xgb_recall"], stats["xgb_f1"], "Primary decision model"],
                ["LSTM", stats["lstm_accuracy"], stats["lstm_precision"], stats["lstm_recall"], stats["lstm_f1"], "Sequence comparison prototype"],
                ["ANN", stats["ann_accuracy"], "N/A", "N/A", "N/A", "Weak baseline"],
            ],
            widths=[1.2 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch, 1.9 * inch],
        )
    )
    story.append(para("Risk distribution", styles["h2"]))
    story.append(
        table(
            [["Risk Level", "Session Count"]]
            + [[key, str(value)] for key, value in sorted(risk_counts.items())],
            widths=[2.0 * inch, 1.5 * inch],
        )
    )
    add_image(story, "sprint2/outputs/xgboost_feature_importance.png", "Figure 2. XGBoost feature importance chart.", styles)
    story.append(para("Sprint 2 core question coverage", styles["h2"]))
    story.append(
        para(
            "The Sprint 2 core question asks whether passive physiological streams and active video tracking can extract hidden fatigue variables better than individual analytics silos. The implemented prototype directly addresses this by combining wearable-style telemetry with Sprint 1 video biomechanics and comparing XGBoost, LSTM, and ANN models. Because the data is synthetic, this is workflow evidence rather than real-world validation.",
            styles["body"],
        )
    )

    story.append(PageBreak())
    story.append(para("5. Sprint 3: Genomic-Inspired Profiling and Workload Optimization", styles["h1"]))
    story.append(
        para(
            "Sprint 3 simulates genomic-inspired athlete profiling using ACTN3 and ACE markers, recovery metrics, fatigue state, and training load. After the single-athlete correction, all 150 sessions belong to athlete_001.",
            styles["body"],
        )
    )
    story.append(
        table(
            [
                ["Component", "Implemented Evidence"],
                ["Genomic context", "ACTN3 and ACE genotype fields in sprint3/input_data/athlete_genomic_profiles.csv"],
                ["Sprint 2 integration", "sprint3/outputs/integrated_athlete_profiles.csv consumes fatigue_score and risk_level"],
                ["K-Means clustering", "sprint3/models/kmeans_recovery_model.pkl and clustered_athletes.csv"],
                ["Workload scaling", "workload_multiplier, workload_adjustment_percent, recommended_training_load"],
                ["Safety warning", "Reports state genomic markers are probabilistic and not deterministic limits"],
            ],
            widths=[1.8 * inch, 4.7 * inch],
        )
    )
    story.append(para("Phenotype and recovery outputs", styles["h2"]))
    story.append(
        table(
            [["Output Category", "Distribution"]]
            + [["Phenotype groups", str(phenotype_counts)], ["Recovery priority", str(priority_counts)]],
            widths=[2.0 * inch, 4.5 * inch],
        )
    )
    add_image(story, "sprint3/outputs/cluster_visualization.png", "Figure 3. Sprint 3 recovery-performance cluster visualization.", styles)
    story.append(para("Sprint 3 core question coverage", styles["h2"]))
    story.append(
        para(
            "The Sprint 3 core question asks whether open literature genomic markers can calibrate athlete workloads safely without deterministic genetic bias. The prototype covers this by using ACTN3 and ACE as probabilistic tendency features and by keeping workload decisions tied to fatigue and recovery state. It does not yet use real genomic datasets or validated training ceiling models.",
            styles["body"],
        )
    )

    story.append(para("6. Dashboard Output", styles["h1"]))
    story.append(
        para(
            "The dashboard is a static HTML interface for athlete_001. It shows session-level fatigue score, risk level, phenotype group, recovery priority, XGBoost prediction correctness, feature importance, and workload recommendation.",
            styles["body"],
        )
    )
    story.append(
        table(
            [
                ["Dashboard Item", "Current Output"],
                ["HTML file", "dashboard/athlete_fatigue_dashboard.html"],
                ["Test predictions", "dashboard/outputs/xgboost_test_predictions.csv"],
                ["XGBoost held-out rows", "38"],
                ["Correct / wrong", "30 correct, 8 wrong"],
                ["Dashboard framing", "Single Athlete Fatigue Dashboard"],
            ],
            widths=[2.0 * inch, 4.5 * inch],
        )
    )

    story.append(para("7. Missing or Prototype-Level Items", styles["h1"]))
    for item in [
        "True multi-angle video processing is not implemented.",
        "Cutting and jumping action examples are not demonstrated.",
        "Telemetry is synthetic, not live smartwatch/API data.",
        "Genomic data is synthetic/literature-inspired, not a real open-source genomic dataset.",
        "ACTN3 and ACE are categorical markers, not full polygenic sequence analysis.",
        "No clinically validated injury or strain outcome labels are available.",
        "Dashboard is static HTML, not real-time streaming.",
        "Personal training ceilings are approximated by workload scaling, not clinically validated ceiling prediction.",
    ]:
        story.append(bullet(item, styles))

    story.append(para("8. Final Readiness Decision", styles["h1"]))
    story.append(
        para(
            "READY TO CONTINUE TO SPRINT 4 AS A PROTOTYPE. The implemented pipeline satisfies the main Sprint 1-3 engineering workflow and addresses the core research questions at prototype level. The remaining gaps should be presented as future work and validation requirements.",
            styles["callout"],
        )
    )

    doc = SimpleDocTemplate(
        str(PDF_OUT),
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
        title="Sahasra Sprint 1-3 Detailed Project Report",
        author="Codex",
    )
    doc.build(story, onFirstPage=page_footer, onLaterPages=page_footer)
    MD_OUT.write_text(build_markdown(stats), encoding="utf-8")
    print(PDF_OUT)
    print(MD_OUT)


if __name__ == "__main__":
    build_pdf()
