# Project Pipeline Audit

## Executive Summary

The project is organized into three clear sprint folders and each sprint runs successfully as an individual pipeline. Sprint 1 and Sprint 2 are properly connected: Sprint 2 reads the Sprint 1 biomechanical CSV and merges it with telemetry data. Sprint 3 is functionally complete as a genomic/phenotype/workload module, but it is not yet fully connected to Sprint 2 because it does not consume Sprint 2 fatigue outputs.

Estimated integration quality: **78%**

## Expected Flow Versus Actual Flow

| Pipeline Link | Expected | Actual Status |
| --- | --- | --- |
| Sprint 1 video -> Sprint 1 biomechanical CSV | Athlete video processed by MediaPipe into biomechanical metrics | Connected and complete |
| Sprint 1 CSV -> Sprint 2 feature matrix | Sprint 2 consumes movement metrics from Sprint 1 | Connected and complete |
| Sprint 2 telemetry -> Sprint 2 feature matrix | Sprint 2 merges telemetry with biomechanics | Connected and complete |
| Sprint 2 feature matrix -> Sprint 2 models | ANN, XGBoost, LSTM train from combined feature data | Connected and complete |
| Sprint 2 outputs -> Sprint 3 | Sprint 3 should consume fatigue/recovery outputs from Sprint 2 | **Disconnected / not implemented** |
| Sprint 3 genomic profiles -> clustering | Genomic-inspired profiles feed K-Means clustering | Connected and complete |
| Sprint 3 clusters -> workload recommendations | Clustered athletes feed workload optimizer | Connected and complete |

## Sprint 1 Audit

### Inputs

- `sprint1/input_videos/special_olympics_running.webm`
- `sprint1/models/pose_landmarker_lite.task`

### Code

- `sprint1/pose_pipeline.py`

### Outputs

- `sprint1/outputs/special_olympics_running_enhanced.csv`
- `sprint1/outputs/special_olympics_running_enhanced_overlay.mp4`
- `sprint1/outputs/special_olympics_running_enhanced_summary.md`

### Status

Sprint 1 is connected and complete. The enhanced CSV contains biomechanical features such as knee angles, hip alignment, ankle deviation, foot rotation, and all 33 pose landmarks.

## Sprint 2 Audit

### Inputs

- `sprint1/outputs/special_olympics_running_enhanced.csv`
- `sprint2/input_data/synthetic_athlete_telemetry_100.csv`
- Optional/reference telemetry: `sprint2/input_data/athlete_hr_predict_telemetry.csv`

### Code

- `sprint2/fatigue_pipeline.py`
- `sprint2/ann_fatigue_model.py`
- `sprint2/xgboost_fatigue_model.py`
- `sprint2/lstm_fatigue_model.py`
- `sprint2/import_athlete_hr_repo.py`

### Outputs

- `sprint2/outputs/combined_fatigue_features.csv`
- `sprint2/outputs/fatigue_summary.md`
- `sprint2/models/ann_fatigue_model.keras`
- `sprint2/models/xgboost_fatigue_model.json`
- `sprint2/models/lstm_fatigue_model.keras`
- `sprint2/outputs/ann_fatigue_model_report.md`
- `sprint2/outputs/xgboost_fatigue_report.md`
- `sprint2/outputs/xgboost_feature_importance.png`
- `sprint2/outputs/lstm_classification_report.md`
- `sprint2/outputs/lstm_training_history.png`
- `sprint2/outputs/lstm_confusion_matrix.png`
- `sprint2/outputs/lstm_vs_xgboost_vs_ann_report.md`

### Status

Sprint 2 correctly consumes Sprint 1 outputs. The key proof is `sprint2/fatigue_pipeline.py`, whose default `--movement-csv` is `sprint1/outputs/special_olympics_running_enhanced.csv`.

## Sprint 3 Audit

### Inputs

- `sprint3/input_data/athlete_genomic_profiles.csv`
- `sprint3/outputs/clustered_athletes.csv`

### Code

- `sprint3/generate_genomic_dataset.py`
- `sprint3/phenotype_clustering.py`
- `sprint3/workload_optimizer.py`

### Outputs

- `sprint3/input_data/athlete_genomic_profiles.csv`
- `sprint3/outputs/genomic_dataset_summary.md`
- `sprint3/models/kmeans_recovery_model.pkl`
- `sprint3/outputs/clustered_athletes.csv`
- `sprint3/outputs/elbow_curve.png`
- `sprint3/outputs/cluster_visualization.png`
- `sprint3/outputs/cluster_analysis_report.md`
- `sprint3/outputs/workload_recommendations.csv`
- `sprint3/outputs/workload_recommendation_report.md`

### Status

Sprint 3 works internally. However, it does **not** currently read `sprint2/outputs/combined_fatigue_features.csv`, `sprint2/outputs/fatigue_summary.md`, or any Sprint 2 model output. It uses its own synthetic genomic/phenotype dataset and then clusters that dataset.

## Broken Or Weak Connections

1. **Sprint 3 does not consume Sprint 2 outputs.**
   - Expected: Sprint 3 should use fatigue score, risk level, or recovery telemetry from Sprint 2.
   - Actual: Sprint 3 starts from `athlete_genomic_profiles.csv` only.

2. **Athlete identity is not shared across sprints.**
   - Sprint 2 uses session-level IDs such as `session_001`.
   - Sprint 3 uses athlete-level IDs such as `athlete_001`.
   - There is no bridge table linking Sprint 2 sessions to Sprint 3 athlete profiles.

3. **Sprint 3 workload recommendations do not include Sprint 2 fatigue score.**
   - Workload optimization uses phenotype, recovery time, resting HR, sleep, genotype, and training load.
   - It does not use Sprint 2 `fatigue_score` or `risk_level`.

## Disconnected Or Isolated Datasets

These files are valid but are not part of the main linear pipeline:

- `sprint1/outputs/running_form_enhanced.csv`
- `sprint1/outputs/running_form_pose_angles.csv`
- `sprint1/outputs/repo_test_video_enhanced.csv`
- `sprint2/input_data/sample_telemetry.csv`
- `sprint2/input_data/synthetic_athlete_telemetry_50.csv`
- `sprint2/input_data/athlete_hr_predict_telemetry.csv`
- `sprint2/outputs/athlete_hr_predict_fatigue_features.csv`
- `sprint2/outputs/athlete_hr_predict_fatigue_summary.md`

They are useful for testing/reference, but the main path currently uses:

`special_olympics_running_enhanced.csv` -> `synthetic_athlete_telemetry_100.csv` -> `combined_fatigue_features.csv`.

## Generated Files Not Used Later

The following outputs are terminal deliverables or visual/report artifacts and are not consumed by later scripts:

- Sprint 1 overlay videos and summary reports
- Sprint 2 model reports and charts
- Sprint 2 trained ANN/XGBoost/LSTM models
- Sprint 3 summary reports and charts
- `sprint3/outputs/workload_recommendations.csv` is currently the final endpoint

This is acceptable for reporting, but if Sprint 4 needs to build on Sprint 3, it should consume `workload_recommendations.csv`.

## What Is Connected Correctly

- Sprint 1 video to biomechanical CSV.
- Sprint 2 reads Sprint 1 biomechanical CSV.
- Sprint 2 merges biomechanics with telemetry.
- Sprint 2 generates fatigue scores, risk levels, recommendations, and model outputs.
- Sprint 3 genomic profiles feed phenotype clustering.
- Sprint 3 clustered athletes feed workload recommendations.

## What Is Partially Connected

- Sprint 3 uses concepts similar to Sprint 2: recovery, training load, sleep, resting HR.
- But it does not use Sprint 2 files directly.

## What Is Disconnected

- Sprint 2 to Sprint 3 file-level dependency.
- Session-to-athlete identity bridge.
- Sprint 2 fatigue/risk scores inside Sprint 3 workload recommendations.

## Must Fix Before Sprint 4

1. Create an athlete/session bridge:
   - Example file: `project_bridge/athlete_session_map.csv`
   - Columns: `athlete_id`, `session_id`, `date`

2. Add Sprint 2 fatigue summaries into Sprint 3:
   - Merge `sprint2/outputs/combined_fatigue_features.csv` with `sprint3/outputs/clustered_athletes.csv`.
   - Join by `athlete_id` or a bridge table.

3. Update `sprint3/workload_optimizer.py`:
   - Add optional `--fatigue-features` input.
   - Use `fatigue_score` and `risk_level` when computing workload multiplier and athlete risk flag.

4. Define one canonical pipeline command sequence:
   - Sprint 1 pose extraction.
   - Sprint 2 feature fusion and model training.
   - Sprint 3 genomic clustering.
   - Sprint 3 workload optimizer with Sprint 2 fatigue input.

## Integration Quality Estimate

Current score: **78 / 100**

Reasoning:

- Sprint 1 -> Sprint 2 integration is strong.
- Sprint 2 internal modeling is strong.
- Sprint 3 internal pipeline is strong.
- Sprint 2 -> Sprint 3 integration is missing, which is the main architectural gap before Sprint 4.
