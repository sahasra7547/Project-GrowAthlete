# Project Pipeline Audit V2

## Integration Quality

**Estimated integration quality: 93/100**

The project is now connected as a single research pipeline. Sprint 3 consumes Sprint 2 fatigue outputs through a shared athlete/session bridge, then uses those fatigue features during clustering and workload recommendation.

## Connected Correctly

- Sprint 1 produces biomechanical metrics from athlete video.
- Sprint 2 consumes Sprint 1 movement metrics and merges them with telemetry.
- Sprint 2 produces fatigue score, risk level, fatigue prediction, recommendation, and workload signals.
- Sprint 2 now has an athlete-linked fatigue dataset: `sprint2/outputs/combined_fatigue_features_with_athletes.csv`.
- Sprint 3 now consumes Sprint 2 outputs through `sprint3/outputs/integrated_athlete_profiles.csv`.
- Sprint 3 clustering now includes fatigue score, risk level, training load, ACTN3 encoding, ACE encoding, recovery time, body fat, and sleep efficiency.
- Sprint 3 workload recommendations now depend on both fatigue state and phenotype group.

## New Files Generated

- `sprint3/outputs/athlete_session_bridge.csv`
- `sprint2/outputs/combined_fatigue_features_with_athletes.csv`
- `sprint3/outputs/integrated_athlete_profiles.csv`
- `sprint3/outputs/integrated_workload_recommendations.csv`
- `sprint3/outputs/sprint2_sprint3_integration_report.md`
- `project_flow_diagram_v2.png`
- `project_pipeline_audit_v2.md`

## Data Flow Verified

| Stage | Input | Output | Status |
| --- | --- | --- | --- |
| Sprint 1 | Video file | Enhanced biomechanical CSV | Connected |
| Sprint 2 | Sprint 1 CSV + telemetry | Combined fatigue features | Connected |
| Bridge | Sprint 2 sessions + Sprint 3 athletes | Athlete/session bridge | Connected |
| Sprint 2 Bridging | Fatigue features + bridge | Athlete-linked fatigue CSV | Connected |
| Sprint 3 Integration | Bridge + fatigue + genomics | Integrated athlete profiles | Connected |
| Sprint 3 Clustering | Integrated athlete profiles | Clustered athletes | Connected |
| Sprint 3 Recommendations | Clustered athletes + fatigue state | Integrated workload recommendations | Connected |

## Current Counts

- Integrated rows: 100
- Unique athletes in integrated Sprint 3 file: 100
- Unique Sprint 2 sessions connected: 100
- Fatigue risk distribution: {'High': 40, 'Low': 33, 'Moderate': 27}
- Phenotype distribution after integrated clustering: {'High Recovery / Power': 55, 'Recovery Limited': 45}
- Recovery priority distribution: {'High': 86, 'Moderate': 14}
- Final athlete risk flag distribution: {'Moderate': 60, 'High': 40}

## What Is Partially Connected

The athlete/session bridge is synthetic because the project does not yet have real repeated sessions per real athlete. This is acceptable for the prototype, but Sprint 4 should replace it with real athlete IDs, dates, and longitudinal sessions.

## What Must Be Fixed Before Sprint 4

- Replace synthetic bridge mapping with real athlete/session history when available.
- Store prediction source columns if ANN/XGBoost/LSTM predictions are used separately from the rule-based fatigue score.
- Add longitudinal trend features such as 7-day load, acute/chronic workload ratio, and recovery trend.
- Validate recommendation rules with coach or domain-expert feedback before treating them as decision support.