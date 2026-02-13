# Python Package Template

## Purpose

This repository is a **clean, reusable template** for building Python
packages with:

-   Modern `src/` layout
-   Reproducible testing via **tox**
-   Automated CI via **GitHub Actions**
-   Consistent formatting and static analysis
-   Easy local installation (`pip install -e .`)

It is intended for developers or teams maintaining **multiple internal
Python packages** who want consistent quality gates and minimal setup
friction.

------------------------------------------------------------------------

## What This Template Includes

### Packaging

-   `pyproject.toml` using **setuptools**
-   Versioning via **setuptools_scm**
-   Dependencies loaded from `requirements.txt`
-   Editable installs supported

### Testing & Quality (tox)

Preconfigured environments:

-   `py312` --- run unit tests with coverage
-   `lint` --- flake8 linting
-   `type` --- mypy static typing
-   `format_check` --- black + isort verification
-   `format` --- auto-format convenience
-   `docs_check` --- docstring coverage (interrogate)

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
-   Ruff instead of flake8
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