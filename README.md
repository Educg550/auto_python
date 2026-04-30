# auto-python

A collection of Python utility scripts managed with [uv](https://docs.astral.sh/uv/).

## Requirements

- [uv](https://docs.astral.sh/uv/) — install with `curl -LsSf https://astral.sh/uv/install.sh | sh`

## Orchestrator

`main.py` at the project root discovers and runs all script packages automatically.
A **package** is any subdirectory under `scripts/` that contains runnable `.py` files.

```bash
# Run all packages
uv run main.py

# Run specific packages
uv run main.py --packages spotify

# Run multiple packages
uv run main.py --packages spotify web
```

### Cron setup

The orchestrator is designed to be run on a schedule. Example crontab entries:

```cron
# Run all packages every day at 03:00
0 3 * * * cd /path/to/auto_python && uv run main.py >> /var/log/auto_python.log 2>&1

# Run only the spotify package every hour
0 * * * * cd /path/to/auto_python && uv run main.py --packages spotify >> /var/log/auto_python.log 2>&1
```

The orchestrator logs each script's result and prints a summary at the end.
If a script fails, execution continues — remaining scripts still run.

## Running individual scripts

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
