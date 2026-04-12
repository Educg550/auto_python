# auto-python

A collection of Python utility scripts managed with [uv](https://docs.astral.sh/uv/).

## Requirements

- [uv](https://docs.astral.sh/uv/) — install with `curl -LsSf https://astral.sh/uv/install.sh | sh`

## Running scripts

```bash
uv run scripts/<category>/<script>.py
```

## Adding dependencies

```bash
uv add <package>
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

## Conventions

- Each script in `scripts/` must be self-contained or import only from `lib/`.
- Place reusable logic in `lib/` so multiple scripts can share it.
- New categories get a new subdirectory under `scripts/`.
- Run tests with `uv run pytest tests/`.
