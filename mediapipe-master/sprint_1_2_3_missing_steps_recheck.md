# Sprint 1-3 PDF Procedure Recheck

Source PDF: `C:\Users\sahasra7547\Downloads\Sahasra - Internship Research & Project Execution Framework.pdf`

Recheck date: 2026-06-02

Scope: Requirement/procedure coverage only. This does not evaluate code quality.

## Current Pipeline State

- Sprint 1 uses one athlete video and produces biomechanical pose metrics.
- Sprint 2 uses Sprint 1 biomechanics plus 150 synthetic telemetry sessions for the same athlete.
- Sprint 3 consumes Sprint 2 fatigue outputs and produces recovery/workload recommendations for the same athlete.
- Dashboard is now framed correctly as a single-athlete longitudinal dashboard.

## Sprint 1: Computer Vision Pipeline Setup

### PDF Procedure

1. Load multi-angle athlete videos into a frame-by-frame processing cycle.
2. Track a 33-point body coordinate map.
3. Focus on knee flexion, ankle deviation, and hip alignment.
4. Calculate the 3D hip-knee-ankle angle using spatial trigonometry.

### Covered

- Frame-by-frame video processing is implemented in `sprint1/pose_pipeline.py`.
- Main Sprint 1 output exists: `sprint1/outputs/special_olympics_running_enhanced.csv`.
- Output contains 180 frame rows and 148 columns.
- 33 MediaPipe landmarks are saved with x, y, z, and visibility values.
- Knee flexion, ankle deviation, hip alignment, and foot rotation metrics are generated.
- The joint-angle function uses x, y, and z coordinates.
- Annotated overlay video and summary report are generated.

### Partially Covered / Missing

- Multi-angle processing is not implemented. Current Sprint 1 uses one video angle.
- The PDF mentions sprinting, cutting, and jumping. Current demonstrated video is running/sprinting only.
- Soft-tissue degradation detection is not implemented. Current Sprint 1 produces biomechanical indicators, not clinical strain prediction.

### Sprint 1 Recheck Result

Sprint 1 is strong for a single-athlete prototype, but not a full multi-angle/multi-action system.

## Sprint 2: Multi-Modal Bio-Telemetry Integration

### PDF Procedure

1. Build a telemetry table from smartwatch-style passive metrics: resting heart rate, sleep efficiency, and SpO2.
2. Combine spatial angle profiles with GPS distance, sprint counts, and match load.
3. Train predictive models using XGBoost and LSTM.
4. Classify current data states into tier-based risk outputs.
5. Produce a health dashboard with rolling fatigue score and workload modifications.

### Covered

- Telemetry dataset is generated: `sprint2/input_data/synthetic_athlete_telemetry_fresh.csv`.
- Sprint 2 combined feature matrix exists: `sprint2/outputs/combined_fatigue_features.csv`.
- Sprint 1 biomechanics are merged into Sprint 2 features.
- Telemetry includes resting heart rate, sleep efficiency, SpO2, GPS distance, sprint count, match load, heart rate, speed, cadence, and duration.
- XGBoost model is trained: `sprint2/models/xgboost_fatigue_model.json`.
- LSTM model is trained: `sprint2/models/lstm_fatigue_model.keras`.
- Risk outputs are produced as Low, Moderate, and High.
- Dashboard exists: `dashboard/athlete_fatigue_dashboard.html`.
- Dashboard shows fatigue score, model results, and workload recommendations.

### Partially Covered / Missing

- Wearable sensor data is synthetic, not live smartwatch/API data.
- The PDF says longitudinal bioinformatics matrices; Sprint 2 itself does not use real bioinformatics matrices. Genomic-style data begins in Sprint 3.
- The injury forecasting model is currently a fatigue/risk classifier, not a medically validated injury predictor.
- The dashboard is static HTML, not a real-time streaming dashboard.

### Sprint 2 Recheck Result

Sprint 2 covers the intended ML and dashboard workflow well for a prototype. The missing pieces are real wearable ingestion, real longitudinal data, and validated injury labels.

## Sprint 3: Polygenic Expression Profiling Framework

### PDF Procedure

1. Create tabular representations of open literature genetic indicators such as ACTN3 and ACE.
2. Use K-Means clustering to group multi-source phenotypes such as height, body fat, and recovery velocity.
3. Recommend dynamic workload scaling vectors based on recovery tiers.
4. Avoid deterministic genetic limits.

### Covered

- Genomic-style athlete profile dataset exists: `sprint3/input_data/athlete_genomic_profiles.csv`.
- ACTN3 and ACE genotype columns are implemented.
- Height, weight, body fat, recovery time, resting HR, sleep efficiency, training load, sprint score, and endurance score are included.
- Sprint 2 fatigue data is integrated through `sprint3/outputs/integrated_athlete_profiles.csv`.
- Current integrated files now correctly represent one athlete, `athlete_001`, across 150 sessions.
- K-Means clustering is implemented in `sprint3/phenotype_clustering.py`.
- Clustered output exists: `sprint3/outputs/clustered_athletes.csv`.
- Workload recommendation output exists: `sprint3/outputs/integrated_workload_recommendations.csv`.
- Genomic reports include a warning that genetic markers are probabilistic tendencies, not fixed limits.

### Partially Covered / Missing

- The genomic data is synthetic/literature-inspired, not downloaded from a real open-source genomic dataset.
- ACTN3 and ACE are represented as genotype categories, not full polygenic sequences.
- Since the project is now correctly one-athlete based, genotype does not vary across sessions. Sprint 3 clustering mainly separates session/recovery states, not different athletes.
- Personal training ceilings are approximated through workload recommendations, not a validated ceiling model.

### Sprint 3 Recheck Result

Sprint 3 is connected and functional as a one-athlete longitudinal recovery/workload simulation. The missing pieces are real genomic data, full polygenic scoring, and validated training-ceiling modeling.

## Final Missing/Partial Items

The following are the only meaningful remaining gaps against the PDF:

1. True multi-angle video processing.
2. Cutting and jumping action examples.
3. Live wearable/API telemetry ingestion.
4. Real longitudinal athlete data.
5. Real open-source genomic data or stronger literature-sourced genotype table.
6. Full polygenic scoring beyond ACTN3 and ACE.
7. Clinically validated injury/strain outcome labels.
8. Real-time dashboard streaming instead of static HTML.
9. Validated personal training ceiling model.

## Readiness

For an internship/research prototype, Sprint 1, Sprint 2, and Sprint 3 are sufficiently complete and connected.

For real-world deployment or final scientific validation, the missing items above should be listed clearly as future work.

Decision: **READY TO CONTINUE TO SPRINT 4 AS A PROTOTYPE**.
