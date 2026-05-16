"""Prepare student-mat.csv for Feast by adding student_id and event_timestamp."""
import os
import pandas as pd
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
CSV_PATH = os.path.join(DATA_DIR, "student-mat.csv")
PARQUET_PATH = os.path.join(DATA_DIR, "student_features.parquet")


def prepare():
    df = pd.read_csv(CSV_PATH, sep=";")
    df["student_id"] = range(1, len(df) + 1)
    df["event_timestamp"] = pd.Timestamp(datetime.now())
    df.to_parquet(PARQUET_PATH, index=False)
    print(f"Wrote {len(df)} rows to {os.path.abspath(PARQUET_PATH)}")


if __name__ == "__main__":
    prepare()
