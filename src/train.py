import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import pandas as pd
import numpy as np
import mlflow
import mlflow.sklearn
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, ConfusionMatrixDisplay

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.lineage import track_step


DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "student-mat.csv")
TRACKING_URI = "http://localhost:5000"
EXPERIMENT_NAME = "student-performance"
MODEL_NAME = "StudentPerformanceModel"

CATEGORICAL_COLS = [
    "school", "sex", "address", "famsize", "Pstatus",
    "Mjob", "Fjob", "reason", "guardian",
    "schoolsup", "famsup", "paid", "activities",
    "nursery", "higher", "internet", "romantic",
]


def load_and_prepare_data(path: str) -> tuple[pd.DataFrame, pd.Series]:
    df = pd.read_csv(path, sep=";")

    df["target"] = (df["G3"] >= 10).astype(int)
    df = df.drop(columns=["G3"])

    label_encoders = {}
    for col in CATEGORICAL_COLS:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col])
        label_encoders[col] = le

    X = df.drop(columns=["target"])
    y = df["target"]
    return X, y


def train():
    mlflow.set_tracking_uri(TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)

    with track_step("data_ingestion"):
        X, y = load_and_prepare_data(DATA_PATH)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

    with track_step("data_validation"):
        assert not X_train.isnull().any().any(), "Training data contains nulls"
        assert len(X_train) > 0, "Training set is empty"
        print(f"Validation OK: {len(X_train)} train, {len(X_test)} test rows")

    params = {"n_estimators": 100, "max_depth": 5}

    with track_step("model_training"):
        with mlflow.start_run() as run:
            clf = RandomForestClassifier(
                n_estimators=params["n_estimators"],
                max_depth=params["max_depth"],
                random_state=42,
            )
            clf.fit(X_train, y_train)

            y_pred = clf.predict(X_test)
            acc = accuracy_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred)

            mlflow.log_params(params)
            mlflow.log_metric("accuracy", acc)
            mlflow.log_metric("f1_score", f1)

            cm = confusion_matrix(y_test, y_pred)
            disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=["Fail", "Pass"])
            disp.plot(cmap="Blues")
            plt.title("Confusion Matrix")

            cm_path = "confusion_matrix.png"
            plt.savefig(cm_path)
            mlflow.log_artifact(cm_path)
            os.remove(cm_path)
            plt.close()

            mlflow.sklearn.log_model(
                clf,
                artifact_path="model",
                registered_model_name=MODEL_NAME,
            )

            print(f"Run ID  : {run.info.run_id}")
            print(f"Accuracy: {acc:.4f}")
            print(f"F1 Score: {f1:.4f}")


if __name__ == "__main__":
    train()
