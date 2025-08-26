# Copyright cocotb contributors
# Licensed under the Revised BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-3-Clause

import os
import shutil
from pathlib import Path

import nox

nox.options.sessions = ["lint", "examples", "test"] # default sessions

# package info
PACKAGE = "copra"
PYTHON_VERSIONS = ["3.8", "3.9", "3.10", "3.11", "3.12"]


@nox.session(python=PYTHON_VERSIONS[-1])
def lint(session):
    """Run the linter."""
    args = session.posargs or ["check", "src", "tests", "examples"]
    
    session.run("uv", "pip", "install", "--system", "ruff", "mypy")
    session.run("ruff", *args)
    session.run("mypy", "--disable-error-code=unused-ignore",
                "--disable-error-code=import-not-found", "src")


@nox.session(python=PYTHON_VERSIONS)
def test(session):
    """Run the test suite."""
    session.run("uv", "pip", "install", "--system", "pytest", "pytest-cov")
    session.run("uv", "pip", "install", "--system", "-e", ".")
    session.run("pytest", "tests/", "-v", "--cov=copra", "--cov-report=term-missing")


@nox.session(python=PYTHON_VERSIONS[-1])
def examples(session):
    """Run the examples."""
    session.run("uv", "pip", "install", "--system", "-e", ".")
    
    # Run examples that have test files
    examples_with_tests = [
        "examples/simple_dff",
        "examples/adder", 
        "examples/matrix_multiplier",
        "examples/multi_dim_array"
    ]
    
    for example_dir in examples_with_tests:
        if Path(example_dir).exists():
            session.log(f"Running example in {example_dir}")
            with session.chdir(example_dir):
                session.run("make", "clean", external=True)
                session.run("make", external=True)
