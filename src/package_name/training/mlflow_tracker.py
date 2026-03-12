"""
mlflow_tracker.py — Lightweight wrapper for MLflow experiment tracking.

Drop this file into any training repo.  Import and use as:

    from mlflow_tracker import TrackedRun

    with TrackedRun("transformer-v1", run_name="lr-sweep-003") as run:
        run.log_params({"lr": 1e-4, "batch_size": 32, "n_layers": 6})
        for epoch in range(100):
            # ... training ...
            run.log_metrics({"train_loss": t_loss, "val_loss": v_loss}, step=epoch)
        run.log_artifact("checkpoints/best_model.pt")

Configuration is via environment variables so credentials never touch code:

    MLFLOW_TRACKING_URI    — e.g. https://mlflow.yourdomain.com
    MLFLOW_TRACKING_USERNAME
    MLFLOW_TRACKING_PASSWORD

Set these in your shell profile, .env, or Colab secrets.
"""

from __future__ import annotations

import os
import platform
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import mlflow
from mlflow.entities import RunStatus

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_DEFAULT_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")


def _detect_environment() -> str:
    """Best-effort detection of the runtime environment."""
    if "COLAB_GPU" in os.environ or "COLAB_RELEASE_TAG" in os.environ:
        return "colab"
    if "KAGGLE_KERNEL_RUN_TYPE" in os.environ:
        return "kaggle"
    if Path("/proc/driver/nvidia/version").exists():
        return f"local-gpu-{platform.node()}"
    return f"local-{platform.node()}"


def _git_sha() -> str | None:
    """Return short git SHA of the current repo, or None."""
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"],
                stderr=subprocess.DEVNULL,
            )
            .decode()
            .strip()
        )
    except Exception:
        return None


# ---------------------------------------------------------------------------
# TrackedRun context manager
# ---------------------------------------------------------------------------


@dataclass
class TrackedRun:
    """Context manager wrapping an MLflow run with automatic tagging.

    Parameters
    ----------
    experiment : str
        MLflow experiment name.  Maps naturally to a project / repo,
        e.g. "vanilla-transformer", "vae-mnist".
    run_name : str | None
        Human-readable run label (shows in the UI).
    tags : dict
        Additional tags merged with auto-detected ones.
    tracking_uri : str | None
        Override the tracking URI (otherwise uses env var / default).
    """

    experiment: str
    run_name: str | None = None
    tags: dict[str, str] = field(default_factory=dict)
    tracking_uri: str | None = None

    # internal
    _run: Any = field(default=None, init=False, repr=False)

    def __enter__(self) -> "TrackedRun":
        uri = self.tracking_uri or _DEFAULT_TRACKING_URI
        mlflow.set_tracking_uri(uri)
        mlflow.set_experiment(self.experiment)

        auto_tags = {
            "env": _detect_environment(),
            "python": platform.python_version(),
        }
        sha = _git_sha()
        if sha:
            auto_tags["git_sha"] = sha

        merged_tags = {**auto_tags, **self.tags}
        self._run = mlflow.start_run(run_name=self.run_name, tags=merged_tags)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            mlflow.set_tag("error", str(exc_val)[:250])
            mlflow.end_run(status=RunStatus.to_string(RunStatus.FAILED))
        else:
            mlflow.end_run()
        return False  # don't suppress exceptions

    # ---- convenience delegates -------------------------------------------

    @staticmethod
    def log_params(params: dict[str, Any]) -> None:
        mlflow.log_params(params)

    @staticmethod
    def log_metrics(metrics: dict[str, float], step: int | None = None) -> None:
        mlflow.log_metrics(metrics, step=step)

    @staticmethod
    def log_metric(key: str, value: float, step: int | None = None) -> None:
        mlflow.log_metric(key, value, step=step)

    @staticmethod
    def log_artifact(path: str, artifact_path: str | None = None) -> None:
        mlflow.log_artifact(path, artifact_path)

    @staticmethod
    def log_artifacts(dir_path: str, artifact_path: str | None = None) -> None:
        mlflow.log_artifacts(dir_path, artifact_path)

    @staticmethod
    def set_tag(key: str, value: str) -> None:
        mlflow.set_tag(key, value)

    @property
    def run_id(self) -> str:
        return self._run.info.run_id


# ---------------------------------------------------------------------------
# Standalone usage helpers
# ---------------------------------------------------------------------------


def quick_log(
    experiment: str,
    params: dict,
    metrics: dict,
    run_name: str | None = None,
) -> str:
    """One-shot: log a single set of params + metrics and return the run ID.

    Useful for hyperparameter sweeps where you compute final metrics outside
    the training loop.
    """
    with TrackedRun(experiment, run_name=run_name) as run:
        run.log_params(params)
        run.log_metrics(metrics)
    return run.run_id


if __name__ == "__main__":
    import logging as _logging

    _logging.basicConfig(level=_logging.INFO, format="%(levelname)s: %(message)s")
    _log = _logging.getLogger(__name__)

    # Smoke test — verifies connectivity to the tracking server.
    _log.info("Tracking URI : %s", _DEFAULT_TRACKING_URI)
    _log.info("Environment  : %s", _detect_environment())
    _log.info("Git SHA      : %s", _git_sha() or "(not in a git repo)")

    with TrackedRun("_smoke-test", run_name="connectivity-check") as run:
        run.log_params({"test_param": "hello"})
        run.log_metrics({"test_metric": 1.0})
        _log.info("Run logged successfully.  ID: %s", run.run_id)
