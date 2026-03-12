import importlib
import sys
from types import ModuleType, SimpleNamespace


def _install_fake_mlflow() -> SimpleNamespace:
    calls = SimpleNamespace(
        tracking_uri=None,
        experiment=None,
        started_runs=[],
        end_statuses=[],
        tags=[],
    )

    mlflow_module = ModuleType("mlflow")
    entities_module = ModuleType("mlflow.entities")

    class FakeRunStatus:
        FAILED = "FAILED"

        @staticmethod
        def to_string(status: str) -> str:
            return status

    def set_tracking_uri(uri: str) -> None:
        calls.tracking_uri = uri

    def set_experiment(experiment: str) -> None:
        calls.experiment = experiment

    def start_run(run_name: str | None = None, tags: dict[str, str] | None = None):
        calls.started_runs.append({"run_name": run_name, "tags": tags or {}})
        return SimpleNamespace(info=SimpleNamespace(run_id="fake-run-id"))

    def end_run(status: str | None = None) -> None:
        calls.end_statuses.append(status)

    def set_tag(key: str, value: str) -> None:
        calls.tags.append((key, value))

    mlflow_module.set_tracking_uri = set_tracking_uri
    mlflow_module.set_experiment = set_experiment
    mlflow_module.start_run = start_run
    mlflow_module.end_run = end_run
    mlflow_module.set_tag = set_tag
    mlflow_module.log_params = lambda params: None
    mlflow_module.log_metrics = lambda metrics, step=None: None
    mlflow_module.log_metric = lambda key, value, step=None: None
    mlflow_module.log_artifact = lambda path, artifact_path=None: None
    mlflow_module.log_artifacts = lambda dir_path, artifact_path=None: None
    entities_module.RunStatus = FakeRunStatus

    sys.modules["mlflow"] = mlflow_module
    sys.modules["mlflow.entities"] = entities_module
    return calls


def test_tracked_run_reads_tracking_uri_at_runtime(monkeypatch):
    monkeypatch.delenv("MLFLOW_TRACKING_URI", raising=False)
    calls = _install_fake_mlflow()
    sys.modules.pop("package_name.training.mlflow_tracker", None)

    tracker = importlib.import_module("package_name.training.mlflow_tracker")

    monkeypatch.setenv("MLFLOW_TRACKING_URI", "https://mlflow.example.test")

    with tracker.TrackedRun("demo-experiment", run_name="demo-run") as run:
        assert run.run_id == "fake-run-id"

    assert calls.tracking_uri == "https://mlflow.example.test"
    assert calls.experiment == "demo-experiment"
    assert calls.started_runs[0]["run_name"] == "demo-run"
    assert calls.end_statuses == [None]
