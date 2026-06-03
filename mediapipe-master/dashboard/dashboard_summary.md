# Athlete Dashboard Summary

- Dashboard: `dashboard\athlete_fatigue_dashboard.html`
- XGBoost held-out prediction CSV: `dashboard\outputs\xgboost_test_predictions.csv`

## Test Data Used

- XGBoost uses `sprint2/outputs/combined_fatigue_features_with_athletes.csv`.
- The script splits that dataset into 75% training rows and 25% testing rows.
- Test split setting: `test_size=0.25`, `random_state=42`, stratified by fatigue class when possible.
- XGBoost test rows: 38
- XGBoost correct predictions: 30
- XGBoost wrong predictions: 8

## Model Accuracy Used In Dashboard

- XGBoost: 0.7895 - primary dashboard decision model
- LSTM: 0.7667 - sequence prototype; below XGBoost on this refreshed run
- ANN: 0.9470

## Model Selection Note

The refreshed dataset produced a non-perfect LSTM result, so the dashboard can report it as a comparison metric. XGBoost remains the primary dashboard model because it performs slightly better here and provides feature importance.

## Dashboard Use

The dashboard is athlete/session-focused. It shows fatigue score, risk tier, recommended workload, phenotype group, recovery priority, and whether the selected session was correctly predicted in the XGBoost held-out test set.