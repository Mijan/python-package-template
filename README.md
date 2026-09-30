# Python Package Template

## Purpose

This repository is a **clean, reusable template** for building Python
packages with:

-   Modern `src/` layout
-   A lightweight training profiler with W&B integration
-   Dependency management and locking via **uv**
-   Reproducible testing via **tox** (backed by `tox-uv` and `uv.lock`)
-   Automated CI via **GitHub Actions**
-   Consistent formatting and static analysis
-   One-command local setup (`uv sync`)

It is intended for developers or teams maintaining **multiple internal
Python packages** who want consistent quality gates and minimal setup
friction. In this version, the template is tuned for **personal ML
projects** that need lightweight experiment tracking without pulling in
a larger framework.

------------------------------------------------------------------------

## What This Template Includes

### Packaging

-   `pyproject.toml` using **setuptools** as the build backend
-   Versioning via **setuptools_scm**
-   Runtime dependencies declared in `[project.dependencies]`
-   Tooling dependencies declared as PEP 735 `[dependency-groups]`
    (`test`, `lint`, `type`, `docs`, and an umbrella `dev` group)
-   Exact versions pinned in a committed `uv.lock`

### ML Training Utilities

-   `src/package_name/profiler.py` — per-phase wall-clock profiler with
    optional CUDA synchronization
-   CSV logging of per-batch and per-epoch timing breakdowns
-   W&B (Weights & Biases) logger for experiment metrics and phase
    timings

### Testing & Quality (tox + uv)

Every tox environment uses the `uv-venv-lock-runner`, so it is created by
uv and installed from `uv.lock`. Local runs and CI resolve to identical
dependency versions. Preconfigured environments:

-   `py312` --- run unit tests with coverage
-   `lint` --- ruff linting
-   `type` --- mypy static typing
-   `docs` --- interrogate doc coverage
-   `format_check` --- ruff formatting + lint verification
-   `format` --- auto-format convenience

### Continuous Integration

GitHub Actions workflow (`ci-quality.yaml`) installs uv with
`astral-sh/setup-uv`, runs `uv sync --locked`, and provides:

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
    ├── .github/workflows/ci-quality.yaml
    ├── .python-version
    ├── pyproject.toml
    ├── uv.lock
    ├── src/package_name/
    │   ├── profiler.py
    │   └── package_code_file.py
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

Add runtime dependencies with uv, which updates both `pyproject.toml`
and `uv.lock`:

``` bash
uv add requests
uv add --group test hypothesis   # tooling goes into a dependency group
```

Commit `uv.lock` alongside `pyproject.toml`. CI runs with `UV_LOCKED=1`
and fails if the lock file is out of date, so run `uv lock` after any
manual edit to `pyproject.toml`.

If you do not want the profiler in a given project, run
`uv remove torch numpy wandb` and delete `src/package_name/profiler.py`.

### 4. Install Locally

[Install uv](https://docs.astral.sh/uv/getting-started/installation/),
then:

``` bash
uv sync
```

This creates `.venv`, installs the package in editable mode, and installs
the `dev` dependency group (tox, pytest, ruff, mypy, interrogate). The
Python version comes from `.python-version`; uv downloads it if needed.

Run anything inside the environment with `uv run`; no activation needed:

``` bash
uv run python -c "import package_name"
uv run pytest
```

### 5. Run Quality Checks Locally

``` bash
uv run tox
uv run tox -e lint
uv run tox -e type
uv run tox -e format_check
```

### 6. Enable GitHub Actions

Push to GitHub --- CI runs automatically on:

-   push
-   pull request
-   manual trigger

------------------------------------------------------------------------

## Training Profiler

### Purpose

`src/package_name/profiler.py` provides three composable classes for
profiling training loops and logging results:

| Class | Role |
|---|---|
| `PhaseTimer` | Times named phases within each batch; optionally syncs CUDA |
| `ProfileLogger` | Writes per-batch and per-epoch CSV logs to disk |
| `WandbLogger` | Logs epoch metrics and phase timings to Weights & Biases |

### W&B Configuration

Log in to W&B before running your script:

``` bash
wandb login
```

Or set the API key via environment variable:

``` bash
export WANDB_API_KEY="your-key-here"
```

### Usage Example

``` python
import torch
from package_name.profiler import PhaseTimer, ProfileLogger, WandbLogger

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = ...
optimizer = ...
dataloader = ...

timer = PhaseTimer(device=device)
csv_logger = ProfileLogger(log_dir="logs/profiler")
wb = WandbLogger(
    config={"lr": 1e-4, "batch_size": 32},
    project="my-project",
    run_name="baseline",
)

for epoch in range(num_epochs):
    timer.batch_records.clear()
    timer.records.clear()

    for batch_idx, batch in enumerate(dataloader):
        # Annotate the batch with any metadata you want in the CSV
        timer.start_batch(batch_idx=batch_idx, batch_size=len(batch))

        with timer.time("forward"):
            loss = model(batch)

        with timer.time("backward"):
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

        timer.end_batch()

    # Print a timing summary to stdout
    timer.summary()

    # Write CSVs
    csv_logger.log_epoch(epoch, timer)

    # Log to W&B
    wb.log_epoch({"epoch": epoch, "loss": loss.item()})
    wb.log_phase_timings(timer)

wb.finish()
```

#### Output files

| File | Contents |
|---|---|
| `logs/profiler/profiler_batches.csv` | One row per batch — metadata + per-phase durations + GPU memory |
| `logs/profiler/profiler_epochs.csv` | One row per phase per epoch — mean/std/min/max/total |

#### Profiler without W&B

`PhaseTimer` and `ProfileLogger` have no wandb dependency and can be
used standalone:

``` python
from package_name.profiler import PhaseTimer, ProfileLogger

timer = PhaseTimer()
logger = ProfileLogger(log_dir="logs/profiler")

for epoch in range(num_epochs):
    timer.batch_records.clear()
    timer.records.clear()
    for batch_idx, batch in enumerate(dataloader):
        timer.start_batch(batch_idx=batch_idx)
        with timer.time("forward"):
            ...
        with timer.time("backward"):
            ...
        timer.end_batch()
    logger.log_epoch(epoch, timer)
    timer.summary()
```

------------------------------------------------------------------------

## Recommended Developer Workflow

Typical loop:

1.  Write code
2.  Run `uv run tox -e format`
3.  Run `uv run tox`
4.  Commit & push (including `uv.lock` if dependencies changed)
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

It uses uv for environments and locking but keeps setuptools as the build
backend, and avoids heavier frameworks (Poetry, Hatch, etc.) unless
explicitly needed.

------------------------------------------------------------------------

## License

MIT License © 2026 Jan Mikelson
