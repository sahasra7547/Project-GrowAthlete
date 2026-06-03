# Sprint 2 Minimal Pipeline

Sprint 2 combines Sprint 1 movement mechanics with wearable-style telemetry and workload data.

## Inputs

```text
sprint1/outputs/special_olympics_running_enhanced.csv
sprint2/input_data/sample_telemetry.csv
```

## Run

```powershell
python sprint2\fatigue_pipeline.py
```

## Use The Downloaded athlete_hr_predict Repo

Convert its Garmin-style running CSV files into Sprint 2 telemetry:

```powershell
python sprint2\import_athlete_hr_repo.py
```

Then run Sprint 2 using those converted telemetry rows:

```powershell
python sprint2\fatigue_pipeline.py --telemetry-csv sprint2\input_data\athlete_hr_predict_telemetry.csv --output sprint2\outputs\athlete_hr_predict_fatigue_features.csv --summary-output sprint2\outputs\athlete_hr_predict_fatigue_summary.md
```

## Optional ANN Prototype

After creating `athlete_hr_predict_fatigue_features.csv`, train a small neural-network classifier:

```powershell
python sprint2\ann_fatigue_model.py
```

Outputs:

```text
sprint2/models/ann_fatigue_model.keras
sprint2/outputs/ann_fatigue_model_report.md
```

## XGBoost Baseline

Train the Sprint 2 XGBoost fatigue classifier:

```powershell
python sprint2\xgboost_fatigue_model.py
```

Outputs:

```text
sprint2/models/xgboost_fatigue_model.json
sprint2/outputs/xgboost_fatigue_report.md
sprint2/outputs/xgboost_feature_importance.png
```

## LSTM Sequence Model

Train the final Sprint 2 time-series model with sliding windows:

```powershell
python sprint2\lstm_fatigue_model.py --sequence-length 5
```

Outputs:

```text
sprint2/models/lstm_fatigue_model.keras
sprint2/outputs/lstm_training_history.png
sprint2/outputs/lstm_confusion_matrix.png
sprint2/outputs/lstm_classification_report.md
sprint2/outputs/lstm_vs_xgboost_vs_ann_report.md
```

## Outputs

```text
sprint2/outputs/combined_fatigue_features.csv
sprint2/outputs/fatigue_summary.md
```

This is intentionally rule-based first. It gives an explainable fatigue score before adding heavier machine learning models.
