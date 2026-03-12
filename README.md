# Python Package Template

## Purpose

This repository is a **clean, reusable template** for building Python
packages with:

-   Modern `src/` layout
-   A `training/` area for ML-specific utilities
-   A lightweight MLflow tracker for experiment logging
-   Reproducible testing via **tox**
-   Automated CI via **GitHub Actions**
-   Consistent formatting and static analysis
-   Easy local installation (`pip install -e .`)

It is intended for developers or teams maintaining **multiple internal
Python packages** who want consistent quality gates and minimal setup
friction. In this version, the template is tuned for **personal ML
projects** that need a small amount of experiment infrastructure without
pulling in a larger framework.

------------------------------------------------------------------------

## What This Template Includes

### Packaging

-   `pyproject.toml` using **setuptools**
-   Versioning via **setuptools_scm**
-   Dependencies loaded from `requirements.txt`
-   Editable installs supported

### ML Training Utilities

-   `src/package_name/training/` for training-related helpers
-   `mlflow_tracker.py` with a `TrackedRun` context manager
-   Runtime configuration through environment variables
-   Automatic tags for environment, Python version, and git SHA when
    available

### Testing & Quality (tox)

Preconfigured environments:

-   `py312` --- run unit tests with coverage
-   `lint` --- ruff linting
-   `type` --- mypy static typing
-   `docs` --- interrogate doc coverage
-   `format_check` --- ruff formatting + lint verification
-   `format` --- auto-format convenience

### Continuous Integration

GitHub Actions workflow (`ci-quality.yml`) provides:

-   Formatting checks
-   Linting
-   Type checking
-   Unit tests
-   Coverage artifacts
-   JUnit test reporting

The workflow is intentionally simple and suitable for private or
internal packages.

------------------------------------------------------------------------

## Repository Structure

    .
    ├── .github/workflows/ci-quality.yml
    ├── pyproject.toml
    ├── requirements.txt
    ├── src/package_name/
    │   └── training/mlflow_tracker.py
    ├── tests/
    ├── tox.ini
    └── README.md

------------------------------------------------------------------------

## How to Use This Template

### 1. Create a New Repository

Use this repository as a template (GitHub "Use this template") or copy
it.

### 2. Rename the Package

Replace occurrences of:

-   `package_name` → your import name
-   `package-name` → your distribution name

Locations to update:

-   `pyproject.toml`
-   `tox.ini`
-   `src/package_name/`
-   workflow env paths (if present)

### 3. Add Dependencies

Edit:

    requirements.txt

⚠️ Requirements file should contain **only standard requirement
specifiers**\
(no `-r`, no `--extra-index-url`, no editable installs).

If you do not want MLflow in a given project, remove it from
`requirements.txt` and delete `src/package_name/training/mlflow_tracker.py`.

### 4. Install Locally

``` bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
```

### 5. Run Quality Checks Locally

``` bash
tox
tox -e lint
tox -e type
tox -e format_check
```

### 6. Enable GitHub Actions

Push to GitHub --- CI runs automatically on:

-   push
-   pull request
-   manual trigger

## MLflow Tracker

### Purpose

The tracker in
`src/package_name/training/mlflow_tracker.py`
provides a thin wrapper around MLflow so your training scripts can log
experiments with very little boilerplate. It is intended for personal ML
projects where you want:

-   A consistent way to start and end runs
-   Environment-driven configuration instead of hardcoded credentials
-   Useful default tags without repeating setup code in every project

### Configuration

The tracker reads MLflow connection details from environment variables:

-   `MLFLOW_TRACKING_URI`
-   `MLFLOW_TRACKING_USERNAME`
-   `MLFLOW_TRACKING_PASSWORD`

Example:

``` bash
export MLFLOW_TRACKING_URI="https://mlflow.yourdomain.com"
export MLFLOW_TRACKING_USERNAME="your-user"
export MLFLOW_TRACKING_PASSWORD="your-password"
```

If `MLFLOW_TRACKING_URI` is not set, the tracker falls back to
`http://localhost:5000`.

### Usage

Basic example:

``` python
from package_name.training.mlflow_tracker import TrackedRun

with TrackedRun("my-experiment", run_name="baseline") as run:
    run.log_params({"lr": 1e-4, "batch_size": 32})
    run.log_metrics({"train_loss": 0.42}, step=1)
    run.log_artifact("artifacts/model.pt")
```

For one-shot logging, use `quick_log`:

``` python
from package_name.training.mlflow_tracker import quick_log

run_id = quick_log(
    experiment="my-experiment",
    params={"lr": 1e-4},
    metrics={"val_accuracy": 0.91},
    run_name="final-metrics",
)
```

### Default Behavior

Each run automatically attaches a few useful tags:

-   `env` for the detected runtime environment
-   `python` for the Python version
-   `git_sha` when the current repository is a git checkout

You can add extra tags by passing `tags={...}` to `TrackedRun`.

------------------------------------------------------------------------

## Recommended Developer Workflow

Typical loop:

1.  Write code
2.  Run `tox -e format`
3.  Run `tox`
4.  Commit & push
5.  CI verifies everything

------------------------------------------------------------------------

## Customization Ideas

Depending on your needs, you may want to add:

-   `pre-commit` hooks
-   Notebook testing or linting
-   Coverage upload (Codecov)
-   Multi‑Python test matrix
-   Wheel/sdist build job
-   Private PyPI publishing workflow

------------------------------------------------------------------------

## Design Philosophy

This template is intentionally:

-   Minimal but production‑ready
-   Fast in CI
-   Friendly for internal packages
-   Easy to reason about
-   Easy to extend

It avoids heavy frameworks (Poetry, Hatch, etc.) unless explicitly
needed.

------------------------------------------------------------------------

## License

MIT License © 2026 Jan Mikelson
