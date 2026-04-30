import argparse
import subprocess
from pathlib import Path

from lib.logger import get_logger

logger = get_logger("orchestrator")

SCRIPTS_DIR = Path(__file__).parent / "scripts"


def discover_packages(scripts_dir: Path = SCRIPTS_DIR) -> dict[str, list[Path]]:
    packages: dict[str, list[Path]] = {}
    for path in sorted(scripts_dir.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        pkg_name = path.parent.name
        packages.setdefault(pkg_name, []).append(path)
    return packages


def run_script(script: Path) -> bool:
    logger.info(f"Running {script}")
    result = subprocess.run(["uv", "run", str(script)])
    if result.returncode != 0:
        logger.error(f"{script.name} failed with exit code {result.returncode}")
        return False
    return True


def run_packages(packages: dict[str, list[Path]]) -> dict[str, list[tuple[Path, bool]]]:
    # TODO: support parallel package execution
    results: dict[str, list[tuple[Path, bool]]] = {}
    for name, scripts in packages.items():
        logger.info(f"[{name}] Starting package")
        pkg_results = []
        # TODO: support parallel script execution within a package
        # TODO: support per-script selection within a package (e.g., --scripts flag)
        for script in scripts:
            ok = run_script(script)
            pkg_results.append((script, ok))
        results[name] = pkg_results
    return results
