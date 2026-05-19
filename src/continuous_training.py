"""Continuous Training Script.

Checks for data drift and triggers retraining if drift is detected.
Uses MLflow to manage model versions and stage transitions.
"""

import os
import sys
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import mlflow
from mlflow.tracking import MlflowClient

DRIFT_REPORT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "monitoring", "drift_report.json"
)
DRIFT_THRESHOLD = 0.3
TRACKING_URI = "http://127.0.0.1:5000"
MODEL_NAME = "StudentPerformanceModel"


def load_drift_report() -> dict:
    """Load and parse the Evidently drift report JSON."""
    if not os.path.exists(DRIFT_REPORT_PATH):
        raise FileNotFoundError(
            f"Drift report not found at {DRIFT_REPORT_PATH}. "
            "Run 'python monitoring/drift_report.py' first."
        )
    
    with open(DRIFT_REPORT_PATH, "r", encoding="utf-8") as f:
        report = json.load(f)
    
    return report


def get_drift_score(report: dict) -> float:
    """Extract the share of drifted columns from the report."""
    try:
        metrics = report.get("metrics", [])
        
        # Look for DriftedColumnsCount metric
        for metric in metrics:
            metric_name = metric.get("metric_name", "")
            if "DriftedColumnsCount" in metric_name:
                value = metric.get("value", {})
                if isinstance(value, dict) and "share" in value:
                    return value["share"]
        
        # Alternative: look for share_of_drifted_columns in result
        for metric in metrics:
            result = metric.get("result", {})
            if "share_of_drifted_columns" in result:
                return result["share_of_drifted_columns"]
        
        # Another alternative structure
        if "share_of_drifted_columns" in report:
            return report["share_of_drifted_columns"]
        
        raise KeyError("Could not find drift share in report")
    except Exception as e:
        raise ValueError(f"Error parsing drift report: {e}")


def check_drift(drift_score: float) -> bool:
    """Check if drift exceeds threshold."""
    return drift_score > DRIFT_THRESHOLD


def run_training():
    """Import and run the training function."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from src.train import train
    train()


def transition_model_to_production(client: MlflowClient) -> tuple[int, int | None]:
    """
    Transition the latest model version to Production.
    Archive the previous Production version.
    
    Returns: (new_version, old_version or None)
    """
    # Get all versions of the model
    versions = client.search_model_versions(f"name='{MODEL_NAME}'")
    
    if not versions:
        raise ValueError(f"No versions found for model '{MODEL_NAME}'")
    
    # Find the latest version (highest version number)
    latest_version = max(versions, key=lambda v: int(v.version))
    new_version_num = int(latest_version.version)
    
    # Find current Production version (if any)
    old_production_version = None
    for v in versions:
        if v.current_stage == "Production":
            old_production_version = int(v.version)
            break
    
    # Archive the old Production version
    if old_production_version and old_production_version != new_version_num:
        client.transition_model_version_stage(
            name=MODEL_NAME,
            version=str(old_production_version),
            stage="Archived",
            archive_existing_versions=False,
        )
        print(f"Archived model version {old_production_version}")
    
    # Transition latest to Production
    client.transition_model_version_stage(
        name=MODEL_NAME,
        version=str(new_version_num),
        stage="Production",
        archive_existing_versions=False,
    )
    print(f"Transitioned model version {new_version_num} to Production")
    
    return new_version_num, old_production_version


def main():
    """Main continuous training pipeline."""
    print("=" * 60)
    print("CONTINUOUS TRAINING PIPELINE")
    print("=" * 60)
    
    retraining_happened = False
    new_version = None
    drift_score = None
    
    try:
        # Step 1: Load and check drift report
        print("\n[Step 1] Loading drift report...")
        report = load_drift_report()
        drift_score = get_drift_score(report)
        print(f"Drift score (share_of_drifted_columns): {drift_score:.2%}")
        print(f"Drift threshold: {DRIFT_THRESHOLD:.0%}")
        
        if not check_drift(drift_score):
            print("\n✓ No significant drift detected, skipping retraining.")
            print("=" * 60)
            print("\nSUMMARY")
            print("-" * 60)
            print(f"  Drift Score:        {drift_score:.2%}")
            print(f"  Retraining:         No (below threshold)")
            print(f"  New Model Version:  N/A")
            print("=" * 60)
            return False
        
        print(f"\n⚠ Drift detected ({drift_score:.2%} > {DRIFT_THRESHOLD:.0%}), starting retraining...")
        
        # Step 2: Run training
        print("\n[Step 2] Running training pipeline...")
        mlflow.set_tracking_uri(TRACKING_URI)
        run_training()
        retraining_happened = True
        print("Training completed successfully.")
        
        # Step 3: Transition model to Production
        print("\n[Step 3] Transitioning model to Production...")
        client = MlflowClient(tracking_uri=TRACKING_URI)
        new_version, old_version = transition_model_to_production(client)
        
        # Step 4: Print summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("-" * 60)
        print(f"  Drift Score:            {drift_score:.2%}")
        print(f"  Retraining:             Yes")
        print(f"  New Production Version: {new_version}")
        if old_version:
            print(f"  Archived Version:       {old_version}")
        print("=" * 60)
        
        return True
        
    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}")
        print("Please run 'python monitoring/drift_report.py' first to generate the drift report.")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n✗ Error during continuous training: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    result = main()
    # Exit with code 0 if retraining happened (for CI to know)
    # Exit with code 2 if no retraining needed (not an error, just skip)
    sys.exit(0 if result else 2)
