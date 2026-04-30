from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from main import discover_packages


def test_discover_packages_finds_scripts(tmp_path):
    spotify_dir = tmp_path / "automation" / "spotify"
    spotify_dir.mkdir(parents=True)
    (spotify_dir / "__init__.py").touch()
    (spotify_dir / "dedupe_playlists.py").touch()
    (tmp_path / "automation" / "__init__.py").touch()
    (tmp_path / "__init__.py").touch()

    packages = discover_packages(tmp_path)

    assert "spotify" in packages
    assert len(packages["spotify"]) == 1
    assert packages["spotify"][0].name == "dedupe_playlists.py"


def test_discover_packages_ignores_init_files(tmp_path):
    pkg_dir = tmp_path / "mypkg"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").touch()

    packages = discover_packages(tmp_path)

    assert "mypkg" not in packages


def test_discover_packages_returns_empty_for_empty_dir(tmp_path):
    packages = discover_packages(tmp_path)

    assert packages == {}


def test_discover_packages_scripts_sorted_alphabetically(tmp_path):
    pkg_dir = tmp_path / "mypkg"
    pkg_dir.mkdir()
    (pkg_dir / "z_script.py").touch()
    (pkg_dir / "a_script.py").touch()
    (pkg_dir / "m_script.py").touch()

    packages = discover_packages(tmp_path)

    names = [p.name for p in packages["mypkg"]]
    assert names == ["a_script.py", "m_script.py", "z_script.py"]
