#!/usr/bin/env python3
"""
Simple script to run stub comparison and show detailed results.
"""

import sys
import pathlib

# Add the pytest directory to the path so we can import the test
sys.path.insert(0, str(pathlib.Path(__file__).parent / 'pytest'))

from test_stub_comparison import test_stub_comparison

if __name__ == "__main__":
    test_stub_comparison()
