# Project Dependency Graph

## Main Linear Pipeline

```text
sprint1/input_videos/special_olympics_running.webm
    -> sprint1/pose_pipeline.py
    -> sprint1/outputs/special_olympics_running_enhanced.csv
    -> sprint2/fatigue_pipeline.py
    +  sprint2/input_data/synthetic_athlete_telemetry_100.csv
    -> sprint2/outputs/combined_fatigue_features.csv
    -> sprint2/ann_fatigue_model.py
    -> sprint2/models/ann_fatigue_model.keras
    -> sprint2/outputs/ann_fatigue_model_report.md
    -> sprint2/xgboost_fatigue_model.py
    -> sprint2/models/xgboost_fatigue_model.json
    -> sprint2/outputs/xgboost_fatigue_report.md
    -> sprint2/outputs/xgboost_feature_importance.png
    -> sprint2/lstm_fatigue_model.py
    -> sprint2/models/lstm_fatigue_model.keras
    -> sprint2/outputs/lstm_classification_report.md
    -> sprint2/outputs/lstm_vs_xgboost_vs_ann_report.md
```

## Sprint 3 Current Branch

```text
sprint3/generate_genomic_dataset.py
    -> sprint3/input_data/athlete_genomic_profiles.csv
    -> sprint3/outputs/genomic_dataset_summary.md
    -> sprint3/phenotype_clustering.py
    -> sprint3/models/kmeans_recovery_model.pkl
    -> sprint3/outputs/clustered_athletes.csv
    -> sprint3/outputs/elbow_curve.png
    -> sprint3/outputs/cluster_visualization.png
    -> sprint3/outputs/cluster_analysis_report.md
    -> sprint3/workload_optimizer.py
    -> sprint3/outputs/workload_recommendations.csv
    -> sprint3/outputs/workload_recommendation_report.md
```

## Missing Link

```text
sprint2/outputs/combined_fatigue_features.csv
    -X-> sprint3/workload_optimizer.py
```

Sprint 3 currently does not consume Sprint 2 fatigue score, risk level, or recommendation data.

## Inputs

| File | Role |
| --- | --- |
| `sprint1/input_videos/special_olympics_running.webm` | Sprint 1 video input |
| `sprint1/models/pose_landmarker_lite.task` | MediaPipe pose model |
| `sprint2/input_data/synthetic_athlete_telemetry_100.csv` | Main Sprint 2 telemetry input |
| `sprint2/input_data/athlete_hr_predict_telemetry.csv` | Optional Garmin-derived reference telemetry |
| `sprint3/input_data/athlete_genomic_profiles.csv` | Sprint 3 genomic/phenotype input |

## CSV Outputs

| File | Produced By | Used By |
| --- | --- | --- |
| `sprint1/outputs/special_olympics_running_enhanced.csv` | Sprint 1 | Sprint 2 |
| `sprint2/outputs/combined_fatigue_features.csv` | Sprint 2 | Sprint 2 models |
| `sprint2/outputs/athlete_hr_predict_fatigue_features.csv` | Sprint 2 optional branch | Not used later |
| `sprint3/outputs/clustered_athletes.csv` | Sprint 3 clustering | Sprint 3 workload optimizer |
| `sprint3/outputs/workload_recommendations.csv` | Sprint 3 workload optimizer | Final endpoint |

## Models

| Model | File | Produced By |
| --- | --- | --- |
| MediaPipe pose model | `sprint1/models/pose_landmarker_lite.task` | Downloaded asset |
| ANN fatigue model | `sprint2/models/ann_fatigue_model.keras` | `sprint2/ann_fatigue_model.py` |
| XGBoost fatigue model | `sprint2/models/xgboost_fatigue_model.json` | `sprint2/xgboost_fatigue_model.py` |
| LSTM fatigue model | `sprint2/models/lstm_fatigue_model.keras` | `sprint2/lstm_fatigue_model.py` |
| K-Means recovery model | `sprint3/models/kmeans_recovery_model.pkl` | `sprint3/phenotype_clustering.py` |

## Reports And Visuals

| File | Purpose |
| --- | --- |
| `sprint1/outputs/special_olympics_running_enhanced_summary.md` | Sprint 1 biomechanical summary |
| `sprint2/outputs/fatigue_summary.md` | Sprint 2 fatigue summary |
| `sprint2/outputs/xgboost_feature_importance.png` | XGBoost feature importance |
| `sprint2/outputs/lstm_training_history.png` | LSTM training plot |
| `sprint2/outputs/lstm_confusion_matrix.png` | LSTM confusion matrix |
| `sprint3/outputs/genomic_dataset_summary.md` | Genomic dataset summary |
| `sprint3/outputs/elbow_curve.png` | K-Means cluster count evaluation |
| `sprint3/outputs/cluster_visualization.png` | K-Means PCA visualization |
| `sprint3/outputs/workload_recommendation_report.md` | Workload recommendation explanation |
