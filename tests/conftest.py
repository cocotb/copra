"""Pytest configuration and fixtures for copra tests."""

import pytest
from pathlib import Path

# Add the src directory to the Python path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
