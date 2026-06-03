import argparse
import json
import re
from pathlib import Path

import pandas as pd
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier


FEATURE_COLUMNS = [
    "resting_heart_rate",
    "sleep_efficiency",
    "spo2",
    "gps_distance_km",
    "sprint_count",
    "match_load",
    "avg_heart_rate",
    "max_heart_rate",
    "avg_speed_mps",
    "max_speed_mps",
    "avg_cadence",
    "duration_sec",
    "avg_right_knee_angle",
    "avg_left_knee_angle",
    "avg_knee_angle_difference",
    "avg_hip_alignment_abs_angle",
    "avg_right_ankle_deviation_angle",
    "avg_left_ankle_deviation_angle",
    "pose_detection_coverage",
]


def read_csv(path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Missing required input: {path}")
    return pd.read_csv(path)


def train_xgboost_and_export_predictions(features_csv, output_csv):
    df = read_csv(features_csv).copy()
    target = "fatigue_risk" if "fatigue_risk" in df.columns else "risk_level"
    missing = [column for column in FEATURE_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Missing XGBoost feature columns: {missing}")

    x = df[FEATURE_COLUMNS].fillna(0).astype(float)
    encoder = LabelEncoder()
    y = encoder.fit_transform(df[target].astype(str))

    stratify = y if min(pd.Series(y).value_counts()) >= 2 else None
    x_train, x_test, y_train, y_test, index_train, index_test = train_test_split(
        x,
        y,
        df.index,
        test_size=0.25,
        random_state=42,
        stratify=stratify,
    )

    model = XGBClassifier(
        n_estimators=120,
        max_depth=3,
        learning_rate=0.08,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="multi:softprob",
        eval_metric="mlogloss",
        random_state=42,
    )
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    probabilities = model.predict_proba(x_test)
    labels = list(encoder.classes_)

    test_rows = df.loc[index_test].copy()
    test_rows["actual_risk"] = encoder.inverse_transform(y_test)
    test_rows["xgboost_prediction"] = encoder.inverse_transform(predictions)
    test_rows["xgboost_correct"] = test_rows["actual_risk"] == test_rows["xgboost_prediction"]
    test_rows["xgboost_confidence"] = probabilities.max(axis=1).round(4)
    for class_index, label in enumerate(labels):
        test_rows[f"probability_{label.lower()}"] = probabilities[:, class_index].round(4)

    keep_columns = [
        "athlete_id",
        "session_id",
        "actual_risk",
        "xgboost_prediction",
        "xgboost_correct",
        "xgboost_confidence",
        "fatigue_score",
        "recommendation",
    ] + [column for column in test_rows.columns if column.startswith("probability_")]

    output_csv = Path(output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    test_rows[keep_columns].to_csv(output_csv, index=False)

    return {
        "accuracy": float(accuracy_score(y_test, predictions)),
        "test_rows": int(len(test_rows)),
        "correct_rows": int(test_rows["xgboost_correct"].sum()),
        "wrong_rows": int((~test_rows["xgboost_correct"]).sum()),
    }


def parse_metric_report(path):
    text = Path(path).read_text(encoding="utf-8") if Path(path).exists() else ""
    metric = {}
    for key in ["Accuracy", "Precision", "Recall", "F1 score", "F1 Score"]:
        match = re.search(rf"{re.escape(key)}:\s*([0-9.]+)", text)
        if match:
            normalized = key.lower().replace(" ", "_")
            metric[normalized] = float(match.group(1))
    holdout_match = re.search(r"Accuracy on holdout rows:\s*([0-9.]+)", text)
    if holdout_match:
        metric["accuracy"] = float(holdout_match.group(1))
    return metric


def parse_xgboost_importance(path):
    text = Path(path).read_text(encoding="utf-8") if Path(path).exists() else ""
    pairs = []
    for line in text.splitlines():
        match = re.match(r"\d+\.\s+([A-Za-z0-9_]+):\s+([0-9.]+)", line.strip())
        if match:
            pairs.append({"feature": match.group(1), "importance": float(match.group(2))})
    return pairs[:10]


def clean_records(df):
    cleaned = df.where(pd.notnull(df), "")
    return cleaned.to_dict(orient="records")


def risk_badge_class(value):
    return {
        "High": "risk-high",
        "Moderate": "risk-moderate",
        "Low": "risk-low",
    }.get(value, "risk-neutral")


def build_dashboard_html(dataset, predictions, model_metrics, feature_importance, xgb_eval):
    lstm_accuracy = model_metrics.get("lstm", {}).get("accuracy")
    if lstm_accuracy is not None and lstm_accuracy < 0.99:
        lstm_display = f"{lstm_accuracy * 100:.2f}%"
        lstm_use = "Sequence prototype: useful comparison, below XGBoost on this refreshed run"
        lstm_note = (
            "The refreshed synthetic dataset no longer produces a perfect LSTM score. "
            "XGBoost remains the dashboard decision model because it is slightly stronger in this run and easier to explain."
        )
    else:
        lstm_display = "Not ranked"
        lstm_use = "Prototype only: synthetic sequence score is not treated as validated"
        lstm_note = (
            "If LSTM reaches a perfect score on a small synthetic sequence holdout, it is shown as a prototype result only. "
            "XGBoost remains the dashboard decision model because it has inspectable held-out rows and explainable feature importance."
        )
    payload = {
        "dataset": dataset,
        "predictions": predictions,
        "modelMetrics": model_metrics,
        "featureImportance": feature_importance,
        "xgbEval": xgb_eval,
        "display": {
            "lstmAccuracy": lstm_display,
            "lstmUse": lstm_use,
            "lstmNote": lstm_note,
        },
    }
    payload_json = json.dumps(payload)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Single Athlete Fatigue Dashboard</title>
  <style>
    :root {{
      --bg: #f6f7f9;
      --panel: #ffffff;
      --line: #d8dee8;
      --text: #172033;
      --muted: #667085;
      --green: #0f766e;
      --blue: #1d4ed8;
      --amber: #b45309;
      --red: #b91c1c;
      --violet: #6d28d9;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background:
        linear-gradient(180deg, #eef4f8 0, #f6f7f9 260px, #f6f7f9 100%);
      color: var(--text);
      font-family: Arial, Helvetica, sans-serif;
      letter-spacing: 0;
    }}
    header {{
      border-bottom: 1px solid var(--line);
      background: #ffffff;
      padding: 18px 28px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 18px;
      position: sticky;
      top: 0;
      z-index: 10;
      box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
    }}
    .brand-mark {{
      width: 40px;
      height: 40px;
      border-radius: 10px;
      background: #0f766e;
      display: grid;
      place-items: center;
      color: #ffffff;
      font-weight: 800;
      flex: 0 0 auto;
    }}
    .header-title {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    h1 {{
      margin: 0;
      font-size: 24px;
      font-weight: 700;
    }}
    .subtle {{ color: var(--muted); font-size: 13px; }}
    .note {{
      background: #fff7ed;
      border: 1px solid #fed7aa;
      color: #7c2d12;
      border-radius: 8px;
      padding: 12px 14px;
      font-size: 13px;
      line-height: 1.45;
      margin-bottom: 18px;
    }}
    main {{ padding: 22px 28px 36px; max-width: 1500px; margin: 0 auto; }}
    .toolbar {{
      display: grid;
      grid-template-columns: repeat(3, minmax(180px, 1fr));
      gap: 14px;
      margin-bottom: 18px;
    }}
    .overview {{
      display: grid;
      grid-template-columns: repeat(4, minmax(150px, 1fr));
      gap: 14px;
      margin-bottom: 18px;
    }}
    .overview-card {{
      background: rgba(255, 255, 255, 0.92);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      min-height: 96px;
      box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
      position: relative;
      overflow: hidden;
    }}
    .overview-card::before {{
      content: "";
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 4px;
      background: #0f766e;
    }}
    .overview-card.amber::before {{ background: var(--amber); }}
    .overview-card.red::before {{ background: var(--red); }}
    .overview-card.blue::before {{ background: var(--blue); }}
    .overview-card .big {{
      font-size: 28px;
      font-weight: 800;
      margin-top: 9px;
    }}
    .overview-card .hint {{
      color: var(--muted);
      font-size: 12px;
      margin-top: 4px;
    }}
    label {{ display: block; font-size: 12px; color: var(--muted); margin-bottom: 6px; }}
    select {{
      width: 100%;
      min-height: 42px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #ffffff;
      color: var(--text);
      padding: 8px 10px;
      font-size: 14px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: 1.2fr 1fr;
      gap: 18px;
      align-items: start;
    }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
      min-width: 0;
      box-shadow: 0 12px 28px rgba(15, 23, 42, 0.05);
    }}
    .panel h2 {{
      margin: 0 0 14px;
      font-size: 18px;
    }}
    .kpis {{
      display: grid;
      grid-template-columns: repeat(4, minmax(120px, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }}
    .kpi {{
      background: #f9fafb;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 13px;
      min-height: 86px;
      border-top: 3px solid #64748b;
    }}
    .kpi:nth-child(1) {{ border-top-color: var(--violet); }}
    .kpi:nth-child(2) {{ border-top-color: var(--red); }}
    .kpi:nth-child(3) {{ border-top-color: var(--green); }}
    .kpi:nth-child(4) {{ border-top-color: var(--amber); }}
    .kpi .value {{ font-size: 24px; font-weight: 700; margin-top: 8px; }}
    .badge {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 28px;
      border-radius: 999px;
      padding: 4px 10px;
      font-weight: 700;
      font-size: 13px;
    }}
    .risk-high {{ color: #7f1d1d; background: #fee2e2; }}
    .risk-moderate {{ color: #78350f; background: #fef3c7; }}
    .risk-low {{ color: #064e3b; background: #d1fae5; }}
    .risk-neutral {{ color: #344054; background: #e5e7eb; }}
    .ok {{ color: #065f46; font-weight: 700; }}
    .bad {{ color: #991b1b; font-weight: 700; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th, td {{ border-bottom: 1px solid var(--line); padding: 10px 8px; text-align: left; vertical-align: top; }}
    th {{ color: var(--muted); font-weight: 700; }}
    .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 18px; margin-top: 18px; }}
    .bar-row {{ display: grid; grid-template-columns: 190px 1fr 70px; gap: 10px; align-items: center; margin: 9px 0; }}
    .bar-track {{ background: #e5e7eb; height: 12px; border-radius: 999px; overflow: hidden; }}
    .bar-fill {{ height: 100%; background: var(--blue); }}
    .snapshot-row {{ margin: 14px 0; }}
    .snapshot-head {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      font-size: 13px;
      margin-bottom: 7px;
    }}
    .snapshot-track {{
      width: 100%;
      height: 12px;
      background: #e5e7eb;
      border-radius: 999px;
      overflow: hidden;
    }}
    .snapshot-fill {{
      height: 100%;
      border-radius: 999px;
      background: var(--blue);
      width: 0;
    }}
    .snapshot-fill.good {{ background: var(--green); }}
    .snapshot-fill.warn {{ background: var(--amber); }}
    .snapshot-fill.danger {{ background: var(--red); }}
    .split-meter {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      margin-top: 12px;
    }}
    .mini-stat {{
      background: #f8fafc;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
    }}
    .mini-stat strong {{
      display: block;
      font-size: 20px;
      margin-top: 6px;
    }}
    .recommendation {{
      border-left: 4px solid var(--blue);
      background: #eff6ff;
      padding: 13px 14px;
      border-radius: 6px;
      line-height: 1.45;
    }}
    .stack {{ display: grid; gap: 18px; }}
    .small-table-wrapper {{ max-height: 380px; overflow: auto; border: 1px solid var(--line); border-radius: 8px; }}
    @media (max-width: 980px) {{
      .grid, .two-col, .toolbar, .overview, .split-meter {{ grid-template-columns: 1fr; }}
      .kpis {{ grid-template-columns: repeat(2, minmax(120px, 1fr)); }}
      header {{ align-items: flex-start; flex-direction: column; }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="header-title">
      <div class="brand-mark">AF</div>
      <div>
        <h1>Single Athlete Fatigue Dashboard</h1>
        <div class="subtle">One video-tracked athlete + longitudinal telemetry sessions + workload recommendations</div>
      </div>
    </div>
    <div class="subtle">Dashboard decision model: <strong id="bestModel">XGBoost</strong></div>
  </header>

  <main>
    <div class="note">
      {lstm_note}
    </div>

    <section class="overview">
      <div class="overview-card blue">
        <div class="subtle">Total Sessions</div>
        <div class="big" id="totalSessions">-</div>
        <div class="hint">training sessions for athlete_001</div>
      </div>
      <div class="overview-card red">
        <div class="subtle">High Risk Sessions</div>
        <div class="big" id="highRiskCount">-</div>
        <div class="hint">needs close monitoring</div>
      </div>
      <div class="overview-card">
        <div class="subtle">XGBoost Correct</div>
        <div class="big" id="xgbCorrectCount">-</div>
        <div class="hint">held-out test rows</div>
      </div>
      <div class="overview-card amber">
        <div class="subtle">XGBoost Wrong</div>
        <div class="big" id="xgbWrongCount">-</div>
        <div class="hint">review cases</div>
      </div>
    </section>

    <section class="toolbar">
      <div>
        <label for="athleteSelect">Athlete (fixed)</label>
        <select id="athleteSelect"></select>
      </div>
      <div>
        <label for="sessionSelect">Session</label>
        <select id="sessionSelect"></select>
      </div>
      <div>
        <label for="riskFilter">Risk filter</label>
        <select id="riskFilter">
          <option value="All">All risk levels</option>
          <option value="High">High</option>
          <option value="Moderate">Moderate</option>
          <option value="Low">Low</option>
        </select>
      </div>
    </section>

    <section class="kpis">
      <div class="kpi"><div class="subtle">Fatigue Score</div><div class="value" id="fatigueScore">-</div></div>
      <div class="kpi"><div class="subtle">Risk Level</div><div class="value"><span id="riskLevel" class="badge">-</span></div></div>
      <div class="kpi"><div class="subtle">Recommended Load</div><div class="value" id="recommendedLoad">-</div></div>
      <div class="kpi"><div class="subtle">Workload Change</div><div class="value" id="workloadChange">-</div></div>
    </section>

    <section class="grid">
      <div class="stack">
        <div class="panel">
          <h2>Selected Athlete Session</h2>
          <div class="two-col">
            <table>
              <tbody id="athleteTable"></tbody>
            </table>
            <table>
              <tbody id="performanceTable"></tbody>
            </table>
          </div>
        </div>
        <div class="panel">
          <h2>Performance Snapshot</h2>
          <div id="performanceBars"></div>
        </div>
        <div class="panel">
          <h2>Coach Recommendation</h2>
          <div class="recommendation" id="recommendation">-</div>
        </div>
        <div class="panel">
          <h2>XGBoost Test Result For Selected Session</h2>
          <table>
            <tbody id="xgbSessionTable"></tbody>
          </table>
        </div>
      </div>

      <div class="stack">
        <div class="panel">
          <h2>Model Comparison</h2>
          <table>
            <thead><tr><th>Model</th><th>Reported Accuracy</th><th>Use In Dashboard</th></tr></thead>
            <tbody id="modelTable"></tbody>
          </table>
          <div class="split-meter">
            <div class="mini-stat">
              <span class="subtle">XGBoost Test Accuracy</span>
              <strong id="xgbAccuracy">-</strong>
            </div>
            <div class="mini-stat">
              <span class="subtle">Reviewed Test Rows</span>
              <strong id="xgbRows">-</strong>
            </div>
          </div>
        </div>
        <div class="panel">
          <h2>XGBoost Feature Importance</h2>
          <div id="importanceBars"></div>
        </div>
      </div>
    </section>

    <section class="panel" style="margin-top: 18px;">
      <h2>XGBoost Held-Out Test Rows</h2>
      <div class="small-table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Athlete</th><th>Session</th><th>Actual</th><th>Predicted</th><th>Correct</th><th>Confidence</th>
            </tr>
          </thead>
          <tbody id="testRows"></tbody>
        </table>
      </div>
    </section>
  </main>

  <script>
    const payload = {payload_json};
    const data = payload.dataset;
    const predictions = payload.predictions;
    const predictionBySession = new Map(predictions.map(row => [row.session_id, row]));

    const athleteSelect = document.getElementById('athleteSelect');
    const sessionSelect = document.getElementById('sessionSelect');
    const riskFilter = document.getElementById('riskFilter');

    function unique(values) {{ return [...new Set(values)].sort(); }}
    function riskClass(value) {{
      if (value === 'High') return 'risk-high';
      if (value === 'Moderate') return 'risk-moderate';
      if (value === 'Low') return 'risk-low';
      return 'risk-neutral';
    }}
    function fmt(value, suffix = '') {{
      if (value === undefined || value === null || value === '') return '-';
      const number = Number(value);
      if (!Number.isNaN(number)) return `${{Math.round(number * 100) / 100}}${{suffix}}`;
      return `${{value}}${{suffix}}`;
    }}
    function bounded(value, maxValue = 100) {{
      const number = Number(value);
      if (Number.isNaN(number)) return 0;
      return Math.max(0, Math.min(100, (number / maxValue) * 100));
    }}
    function snapshot(label, value, maxValue, suffix, intent = 'neutral') {{
      const width = bounded(value, maxValue);
      const cls = intent === 'good' ? 'good' : intent === 'warn' ? 'warn' : intent === 'danger' ? 'danger' : '';
      return `<div class="snapshot-row">
        <div class="snapshot-head"><span>${{label}}</span><strong>${{fmt(value, suffix)}}</strong></div>
        <div class="snapshot-track"><div class="snapshot-fill ${{cls}}" style="width:${{width}}%"></div></div>
      </div>`;
    }}
    function setOptions(select, values) {{
      select.innerHTML = values.map(value => `<option value="${{value}}">${{value}}</option>`).join('');
    }}
    function filteredData() {{
      const risk = riskFilter.value;
      return data.filter(row => risk === 'All' || row.risk_level === risk);
    }}
    function refreshAthletes() {{
      const rows = filteredData();
      const athletes = unique(rows.map(row => row.athlete_id));
      setOptions(athleteSelect, athletes);
      refreshSessions();
    }}
    function refreshSessions() {{
      const athlete = athleteSelect.value;
      const rows = filteredData().filter(row => row.athlete_id === athlete);
      setOptions(sessionSelect, rows.map(row => row.session_id));
      renderSelected();
    }}
    function rowHtml(label, value) {{ return `<tr><th>${{label}}</th><td>${{value}}</td></tr>`; }}
    function renderSelected() {{
      const row = data.find(item => item.athlete_id === athleteSelect.value && item.session_id === sessionSelect.value) || filteredData()[0] || data[0];
      if (!row) return;

      document.getElementById('fatigueScore').textContent = fmt(row.fatigue_score);
      const risk = document.getElementById('riskLevel');
      risk.textContent = row.risk_level || '-';
      risk.className = `badge ${{riskClass(row.risk_level)}}`;
      document.getElementById('recommendedLoad').textContent = fmt(row.recommended_training_load);
      document.getElementById('workloadChange').textContent = fmt(row.workload_adjustment_percent, '%');
      document.getElementById('recommendation').textContent = row.sprint2_recommendation || row.recommendation || '-';
      const fatigueIntent = Number(row.fatigue_score) >= 75 ? 'danger' : Number(row.fatigue_score) >= 50 ? 'warn' : 'good';
      const sleepIntent = Number(row.sleep_efficiency) >= 85 ? 'good' : Number(row.sleep_efficiency) >= 75 ? 'warn' : 'danger';
      const loadIntent = Number(row.training_load) >= 75 ? 'danger' : Number(row.training_load) >= 50 ? 'warn' : 'good';
      document.getElementById('performanceBars').innerHTML = [
        snapshot('Fatigue score', row.fatigue_score, 100, '', fatigueIntent),
        snapshot('Sleep efficiency', row.sleep_efficiency, 100, '%', sleepIntent),
        snapshot('Training load', row.training_load, 115, '', loadIntent),
        snapshot('Recommended load', row.recommended_training_load, 115, '', 'good'),
      ].join('');

      document.getElementById('athleteTable').innerHTML = [
        rowHtml('Athlete ID', row.athlete_id),
        rowHtml('Session ID', row.session_id),
        rowHtml('Phenotype Group', row.phenotype_group),
        rowHtml('Recovery Priority', row.recovery_priority),
        rowHtml('Athlete Risk Flag', `<span class="badge ${{riskClass(row.athlete_risk_flag)}}">${{row.athlete_risk_flag}}</span>`),
      ].join('');

      document.getElementById('performanceTable').innerHTML = [
        rowHtml('Sleep Efficiency', fmt(row.sleep_efficiency, '%')),
        rowHtml('Resting HR', fmt(row.resting_hr || row.resting_heart_rate, ' bpm')),
        rowHtml('Training Load', fmt(row.training_load)),
        rowHtml('Sprint Score', fmt(row.sprint_performance_score)),
        rowHtml('Endurance Score', fmt(row.endurance_score)),
        rowHtml('ACTN3 / ACE', `${{row.actn3_genotype || '-'}} / ${{row.ace_genotype || '-'}}`),
      ].join('');

      const pred = predictionBySession.get(row.session_id);
      if (pred) {{
        const correct = String(pred.xgboost_correct).toLowerCase() === 'true';
        document.getElementById('xgbSessionTable').innerHTML = [
          rowHtml('Actual Risk', pred.actual_risk),
          rowHtml('XGBoost Prediction', pred.xgboost_prediction),
          rowHtml('Correct?', `<span class="${{correct ? 'ok' : 'bad'}}">${{correct ? 'True' : 'False'}}</span>`),
          rowHtml('Confidence', fmt(Number(pred.xgboost_confidence) * 100, '%')),
        ].join('');
      }} else {{
        document.getElementById('xgbSessionTable').innerHTML = rowHtml('Status', 'This session was used outside the XGBoost held-out test set.');
      }}
    }}
    function renderModelTable() {{
      const rows = [
        ['XGBoost', fmt(Number(payload.modelMetrics.xgboost?.accuracy) * 100, '%'), 'Primary dashboard model: held-out test + feature importance'],
        ['LSTM', payload.display.lstmAccuracy, payload.display.lstmUse],
        ['ANN', fmt(Number(payload.modelMetrics.ann?.accuracy) * 100, '%'), 'Prototype neural baseline'],
      ];
      document.getElementById('modelTable').innerHTML = rows.map(([model, acc, use]) =>
        `<tr><td>${{model}}</td><td>${{acc}}</td><td>${{use}}</td></tr>`
      ).join('');
      document.getElementById('xgbAccuracy').textContent = fmt(Number(payload.modelMetrics.xgboost?.accuracy) * 100, '%');
      document.getElementById('xgbRows').textContent = payload.xgbEval.test_rows;
    }}
    function renderImportance() {{
      const max = Math.max(...payload.featureImportance.map(item => item.importance), 0.001);
      document.getElementById('importanceBars').innerHTML = payload.featureImportance.map(item => {{
        const width = Math.max(2, (item.importance / max) * 100);
        return `<div class="bar-row"><div>${{item.feature}}</div><div class="bar-track"><div class="bar-fill" style="width:${{width}}%"></div></div><div>${{item.importance.toFixed(3)}}</div></div>`;
      }}).join('');
    }}
    function renderTestRows() {{
      document.getElementById('testRows').innerHTML = predictions.map(row => {{
        const correct = String(row.xgboost_correct).toLowerCase() === 'true';
        return `<tr>
          <td>${{row.athlete_id}}</td>
          <td>${{row.session_id}}</td>
          <td>${{row.actual_risk}}</td>
          <td>${{row.xgboost_prediction}}</td>
          <td><span class="${{correct ? 'ok' : 'bad'}}">${{correct ? 'True' : 'False'}}</span></td>
          <td>${{fmt(Number(row.xgboost_confidence) * 100, '%')}}</td>
        </tr>`;
      }}).join('');
    }}
    function renderOverview() {{
      const high = data.filter(row => row.risk_level === 'High').length;
      document.getElementById('totalSessions').textContent = data.length;
      document.getElementById('highRiskCount').textContent = high;
      document.getElementById('xgbCorrectCount').textContent = payload.xgbEval.correct_rows;
      document.getElementById('xgbWrongCount').textContent = payload.xgbEval.wrong_rows;
    }}

    riskFilter.addEventListener('change', refreshAthletes);
    athleteSelect.addEventListener('change', refreshSessions);
    sessionSelect.addEventListener('change', renderSelected);

    refreshAthletes();
    renderOverview();
    renderModelTable();
    renderImportance();
    renderTestRows();
  </script>
</body>
</html>"""


def write_summary(path, html_path, predictions_path, xgb_eval, model_metrics):
    lstm_accuracy = model_metrics["lstm"].get("accuracy")
    if lstm_accuracy is not None and lstm_accuracy < 0.99:
        lstm_line = f"- LSTM: {lstm_accuracy:.4f} - sequence prototype; below XGBoost on this refreshed run"
        lstm_note = (
            "The refreshed dataset produced a non-perfect LSTM result, so the dashboard can report it as a comparison metric. "
            "XGBoost remains the primary dashboard model because it performs slightly better here and provides feature importance."
        )
    else:
        lstm_line = "- LSTM: Not ranked - prototype only; perfect synthetic sequence scores are not treated as validated"
        lstm_note = (
            "If the LSTM report shows a perfect score on this small synthetic dataset, that is not strong evidence of real-world superiority. "
            "For the dashboard, XGBoost remains the main model because its held-out predictions are inspectable and its feature importance explains the risk decision."
        )
    lines = [
        "# Athlete Dashboard Summary",
        "",
        f"- Dashboard: `{html_path}`",
        f"- XGBoost held-out prediction CSV: `{predictions_path}`",
        "",
        "## Test Data Used",
        "",
        "- XGBoost uses `sprint2/outputs/combined_fatigue_features_with_athletes.csv`.",
        "- The script splits that dataset into 75% training rows and 25% testing rows.",
        "- Test split setting: `test_size=0.25`, `random_state=42`, stratified by fatigue class when possible.",
        f"- XGBoost test rows: {xgb_eval['test_rows']}",
        f"- XGBoost correct predictions: {xgb_eval['correct_rows']}",
        f"- XGBoost wrong predictions: {xgb_eval['wrong_rows']}",
        "",
        "## Model Accuracy Used In Dashboard",
        "",
        f"- XGBoost: {model_metrics['xgboost'].get('accuracy', 0):.4f} - primary dashboard decision model",
        lstm_line,
        f"- ANN: {model_metrics['ann'].get('accuracy', 0):.4f}",
        "",
        "## Model Selection Note",
        "",
        lstm_note,
        "",
        "## Dashboard Use",
        "",
        "The dashboard is athlete/session-focused. It shows fatigue score, risk tier, recommended workload, phenotype group, recovery priority, and whether the selected session was correctly predicted in the XGBoost held-out test set.",
    ]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Generate athlete fatigue dashboard")
    parser.add_argument("--features-csv", default="sprint2/outputs/combined_fatigue_features_with_athletes.csv")
    parser.add_argument("--recommendations-csv", default="sprint3/outputs/integrated_workload_recommendations.csv")
    parser.add_argument("--predictions-output", default="dashboard/outputs/xgboost_test_predictions.csv")
    parser.add_argument("--html-output", default="dashboard/athlete_fatigue_dashboard.html")
    parser.add_argument("--summary-output", default="dashboard/dashboard_summary.md")
    args = parser.parse_args()

    xgb_eval = train_xgboost_and_export_predictions(args.features_csv, args.predictions_output)
    recommendations = read_csv(args.recommendations_csv)
    predictions = read_csv(args.predictions_output)

    model_metrics = {
        "xgboost": parse_metric_report("sprint2/outputs/xgboost_fatigue_report.md"),
        "ann": parse_metric_report("sprint2/outputs/ann_fatigue_model_report.md"),
        "lstm": parse_metric_report("sprint2/outputs/lstm_classification_report.md"),
    }
    model_metrics["xgboost"]["accuracy"] = xgb_eval["accuracy"]

    feature_importance = parse_xgboost_importance("sprint2/outputs/xgboost_fatigue_report.md")
    html = build_dashboard_html(
        clean_records(recommendations),
        clean_records(predictions),
        model_metrics,
        feature_importance,
        xgb_eval,
    )

    html_path = Path(args.html_output)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(html, encoding="utf-8")
    write_summary(args.summary_output, args.html_output, args.predictions_output, xgb_eval, model_metrics)

    print(f"Saved dashboard to: {args.html_output}")
    print(f"Saved XGBoost test predictions to: {args.predictions_output}")
    print(f"Saved dashboard summary to: {args.summary_output}")


if __name__ == "__main__":
    main()
