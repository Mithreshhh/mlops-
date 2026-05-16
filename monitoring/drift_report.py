import os
import pandas as pd
from evidently import Report
from evidently.presets import DataDriftPreset

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "student-mat.csv")
REPORT_PATH = os.path.join(os.path.dirname(__file__), "drift_report.html")


def generate_drift_report():
    df = pd.read_csv(DATA_PATH, sep=";")
    df = df.drop(columns=["G3"])

    split = int(len(df) * 0.7)
    reference = df.iloc[:split]
    current = df.iloc[split:]

    report = Report(metrics=[DataDriftPreset()])
    result = report.run(reference_data=reference, current_data=current)
    result.save_html(REPORT_PATH)

    print(f"Reference rows: {len(reference)}")
    print(f"Current rows  : {len(current)}")
    print(f"Drift report saved to: {os.path.abspath(REPORT_PATH)}")


if __name__ == "__main__":
    generate_drift_report()
