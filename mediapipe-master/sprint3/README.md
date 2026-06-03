# Sprint 3 Genomic Dataset Pipeline

Generate a synthetic sports-genetics and phenotype dataset:

```powershell
python sprint3\generate_genomic_dataset.py
```

Outputs:

```text
sprint3/input_data/athlete_genomic_profiles.csv
sprint3/outputs/genomic_dataset_summary.md
```

The synthetic trends are intentionally noisy and non-deterministic. Genotypes influence tendencies, but they do not define fixed athlete outcomes.

## Phenotype Clustering

Cluster athletes into recovery-performance phenotype groups:

```powershell
python sprint3\phenotype_clustering.py
```

Outputs:

```text
sprint3/models/kmeans_recovery_model.pkl
sprint3/outputs/clustered_athletes.csv
sprint3/outputs/elbow_curve.png
sprint3/outputs/cluster_visualization.png
sprint3/outputs/cluster_analysis_report.md
```

## Workload Optimization

Generate adaptive workload recommendations from clustered athletes:

```powershell
python sprint3\workload_optimizer.py
```

Outputs:

```text
sprint3/outputs/workload_recommendations.csv
sprint3/outputs/workload_recommendation_report.md
```
