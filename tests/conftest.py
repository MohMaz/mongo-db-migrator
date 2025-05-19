"""Pytest configuration file."""

import os
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment before each test."""
    # Create necessary directories
    os.makedirs("reports", exist_ok=True)
    os.makedirs("migration-output", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    yield

    # Clean up after tests
    for dir_path in ["reports", "migration-output", "logs"]:
        for file in Path(dir_path).glob("*"):
            if file.is_file():
                file.unlink()
