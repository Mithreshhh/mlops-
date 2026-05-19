import os
import json
import pandas as pd
from evidently import Report
from evidently.presets import DataDriftPreset

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "student-mat.csv")
REPORT_HTML_PATH = os.path.join(os.path.dirname(__file__), "drift_report.html")
REPORT_JSON_PATH = os.path.join(os.path.dirname(__file__), "drift_report.json")


def generate_drift_report():
    df = pd.read_csv(DATA_PATH, sep=";")
    df = df.drop(columns=["G3"])

    split = int(len(df) * 0.7)
    reference = df.iloc[:split]
    current = df.iloc[split:]

    report = Report(metrics=[DataDriftPreset()])
    result = report.run(reference_data=reference, current_data=current)
    
    # Save HTML report
    result.save_html(REPORT_HTML_PATH)
    
    # Save JSON report (for continuous training script)
    result.save_json(REPORT_JSON_PATH)

    print(f"Reference rows: {len(reference)}")
    print(f"Current rows  : {len(current)}")
    print(f"HTML report saved to: {os.path.abspath(REPORT_HTML_PATH)}")
    print(f"JSON report saved to: {os.path.abspath(REPORT_JSON_PATH)}")


if __name__ == "__main__":
    generate_drift_report()
