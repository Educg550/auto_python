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
