"""OpenLineage event emitter for the student training pipeline.

Emits START and COMPLETE events to a Marquez server. All calls are
wrapped in try/except so the pipeline continues even if Marquez is down.
"""

import uuid
from datetime import datetime, timezone

from openlineage.client import OpenLineageClient
from openlineage.client.run import Job, Run, RunEvent, RunState
from openlineage.client.transport.http import HttpConfig, HttpTransport

MARQUEZ_URL = "http://localhost:5001"
NAMESPACE = "mlops_student"
PRODUCER = "https://github.com/mlops-student"

STEPS = ["data_ingestion", "data_validation", "model_training"]

_client = None


def _get_client() -> OpenLineageClient:
    global _client
    if _client is None:
        config = HttpConfig(url=MARQUEZ_URL, timeout=2)
        config.retry = None
        transport = HttpTransport(config)
        _client = OpenLineageClient(transport=transport)
    return _client


def _emit(event: RunEvent) -> None:
    try:
        _get_client().emit(event)
    except Exception:
        pass


def _build_event(
    step_name: str,
    run_id: str,
    state: RunState,
) -> RunEvent:
    return RunEvent(
        eventType=state,
        eventTime=datetime.now(timezone.utc).isoformat(),
        run=Run(runId=run_id),
        job=Job(namespace=NAMESPACE, name=f"student_training_pipeline.{step_name}"),
        producer=PRODUCER,
    )


def emit_start(step_name: str, run_id: str) -> None:
    _emit(_build_event(step_name, run_id, RunState.START))


def emit_complete(step_name: str, run_id: str) -> None:
    _emit(_build_event(step_name, run_id, RunState.COMPLETE))


def emit_fail(step_name: str, run_id: str) -> None:
    _emit(_build_event(step_name, run_id, RunState.FAIL))


def track_step(step_name: str):
    """Context manager that emits START on entry and COMPLETE/FAIL on exit."""
    class _Tracker:
        def __init__(self):
            self.run_id = str(uuid.uuid4())

        def __enter__(self):
            emit_start(step_name, self.run_id)
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is None:
                emit_complete(step_name, self.run_id)
            else:
                emit_fail(step_name, self.run_id)
            return False

    return _Tracker()


def run_all_steps(func_map: dict) -> None:
    """Run a dict of {step_name: callable} with lineage tracking.

    Usage:
        run_all_steps({
            "data_ingestion": load_data,
            "data_validation": validate,
            "model_training": train,
        })
    """
    for step_name in STEPS:
        if step_name not in func_map:
            continue
        with track_step(step_name):
            func_map[step_name]()
