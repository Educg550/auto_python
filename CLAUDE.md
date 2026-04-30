# AGENTS.md

## Project overview

This repository is a uv-managed collection of standalone Python scripts grouped by domain. It is **not** a package meant for installation — scripts are run directly.

## Runtime rules

- **Never use `pip install`** — always `uv add <package>` to manage dependencies.
- **Never use `python script.py`** — always `uv run <path-to-script>` to run scripts.
- **Never use `pip`, `venv`, or `virtualenv` directly** — uv handles all of this.

## Running the orchestrator

`main.py` at the project root discovers and runs all packages (or selected ones):

```bash
# Run all packages
uv run main.py

# Run specific packages
uv run main.py --packages spotify
```

A **package** is any subdirectory under `scripts/` that contains runnable `.py` files (not just `__init__.py`). The orchestrator runs all scripts in a package sequentially, alphabetically.

The orchestrator is the primary entry point for cron. Run individual scripts directly only for development/testing.

## Running individual scripts

```bash
uv run scripts/<category>/<script>.py
```

## Adding a dependency

```bash
uv add <package>
```

## Running tests

```bash
uv run pytest tests/
```

## Repository structure

```
auto_python/
├── scripts/          # Runnable scripts, organized by domain
│   ├── data/         # Data processing, transformation, analysis
│   ├── web/          # Web scraping, HTTP clients, API calls
│   ├── files/        # File operations, format conversion, archiving
│   └── automation/   # Task automation, scheduling, system ops
├── lib/              # Shared modules imported across scripts
├── tests/            # Tests for lib/ modules
├── pyproject.toml
└── .python-version
```

## Where to put new scripts

| Script type                          | Directory                  |
|--------------------------------------|----------------------------|
| Data parsing, CSV, JSON, DB queries  | `scripts/data/`            |
| HTTP requests, web scraping, APIs    | `scripts/web/`             |
| File I/O, format conversion          | `scripts/files/`           |
| OS automation, scheduling, sys calls | `scripts/automation/`      |
| Reusable helpers used by ≥2 scripts  | `lib/`                     |
| Does not fit any category            | New subdirectory in `scripts/` |

## Conventions

- Scripts in `scripts/` must be self-contained or import only from `lib/`.
- Do not create a `src/` layout or package structure — this repo is a scripts collection, not a library.
- Do not add `if __name__ == "__main__"` boilerplate unless the file is also imported by other scripts.
- Keep dependencies minimal; prefer the standard library when it covers the use case.
- When a task requires a new dependency, `uv add` it and commit `pyproject.toml` and `uv.lock` together.

