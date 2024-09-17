"""Pytest fixtures etc."""

import subprocess
from pathlib import Path

import pytest


@pytest.fixture(scope="function")
def random_remote(tmp_path: Path) -> Path:
    """Path to an initialized test remote repo."""
    cmd = ["git", "-C", tmp_path, "init", "--bare"]
    subprocess.run(cmd, capture_output=True, check=True)  # noqa:S603
    return tmp_path
