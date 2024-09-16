"""Pytest fixtures etc."""
from pathlib import Path

import pytest


@pytest.fixture
def repo_url(tmp_path: Path) -> Path:
    """Path to a test repo."""
    return tmp_path
