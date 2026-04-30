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


# --- run_script / run_packages ---

from main import run_packages, run_script


def test_run_script_returns_true_on_success(tmp_path):
    script = tmp_path / "script.py"
    script.touch()

    with patch("main.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        result = run_script(script)

    assert result is True
    mock_run.assert_called_once_with(["uv", "run", str(script)])


def test_run_script_returns_false_on_failure(tmp_path):
    script = tmp_path / "script.py"
    script.touch()

    with patch("main.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1)
        result = run_script(script)

    assert result is False


def test_run_packages_runs_all_scripts(tmp_path):
    script1 = tmp_path / "a_script.py"
    script2 = tmp_path / "b_script.py"
    script1.touch()
    script2.touch()

    packages = {"mypkg": [script1, script2]}

    with patch("main.run_script", return_value=True) as mock_run:
        results = run_packages(packages)

    assert mock_run.call_count == 2
    assert len(results["mypkg"]) == 2
    assert all(ok for _, ok in results["mypkg"])


def test_run_packages_continues_after_script_failure(tmp_path):
    script1 = tmp_path / "a_script.py"
    script2 = tmp_path / "b_script.py"
    script1.touch()
    script2.touch()

    packages = {"mypkg": [script1, script2]}

    with patch("main.run_script", side_effect=[False, True]):
        results = run_packages(packages)

    assert results["mypkg"][0] == (script1, False)
    assert results["mypkg"][1] == (script2, True)


def test_run_packages_returns_results_for_all_packages(tmp_path):
    s1 = tmp_path / "s1.py"
    s2 = tmp_path / "s2.py"
    s1.touch()
    s2.touch()

    packages = {"pkg_a": [s1], "pkg_b": [s2]}

    with patch("main.run_script", return_value=True):
        results = run_packages(packages)

    assert set(results.keys()) == {"pkg_a", "pkg_b"}
