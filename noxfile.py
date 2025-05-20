import nox
import shutil
from pathlib import Path

# Default sessions to run when no session is specified
nox.options.sessions = ["lint", "test"]

# Package information
PACKAGE = "copra"
PYTHON_VERSIONS = ["3.8", "3.9", "3.10", "3.11", "3.12"]

# Paths
HERE = Path(__file__).parent
SRC_DIR = HERE / "src"
DOCS_DIR = HERE / "docs"


def install_with_constraints(session, *args, **kwargs):
    """Install packages with pip, using constraints file if available."""
    requirements = ["pip", "setuptools", "wheel"]
    if (HERE / "requirements.txt").exists():
        requirements.append("-r")
        requirements.append("requirements.txt")
    session.install(*requirements, "--upgrade")
    session.install(*args, **kwargs)


@nox.session(python=PYTHON_VERSIONS[-1])
def lint(session):
    """Run the linter."""
    args = session.posargs or ["src", "tests", "--check"]
    install_with_constraints(
        session,
        "ruff",
        "mypy",
        "types-setuptools",
    )
    session.run("ruff", *args)
    session.run("mypy", "--strict", "src")


@nox.session(python=PYTHON_VERSIONS)
def test(session):
    """Run the test suite."""
    install_with_constraints(
        session,
        "pytest",
        "pytest-cov",
        "pytest-mock",
        "pytest-xdist",
        "cocotb",
    )
    session.install("-e", ".")
    session.run(
        "pytest",
        "--cov=src",
        "--cov-report=term-missing",
        "-n", "auto",
        *session.posargs,
        "tests",
    )


@nox.session(python=PYTHON_VERSIONS[-1])
def docs(session):
    """Build the documentation."""
    install_with_constraints(
        session,
        "sphinx",
        "sphinx-copybutton",
        "furo",
        "myst-parser",
    )
    session.install("-e", ".")
    
    # Build docs
    build_dir = DOCS_DIR / "_build"
    if build_dir.exists():
        shutil.rmtree(build_dir)
    
    session.run(
        "sphinx-build",
        "-b", "html",
        "-d", f"{build_dir}/doctrees",
        "docs/source",
        f"{build_dir}/html",
    )


@nox.session(python=PYTHON_VERSIONS[-1])
def stubgen_example(session):
    """Run the stub generator on examples."""
    install_with_constraints(session, ".")
    session.run("copra", "--help")
    # TODO: Add example running once we have the stub generator implemented
    # session.run("copra", "examples/simple_dff")



@nox.session(python=PYTHON_VERSIONS[-1])
def coverage(session):
    """Generate coverage report."""
    install_with_constraints(session, "coverage", "pytest-cov")
    session.run("coverage", "report", "--show-missing")
    session.run("coverage", "html")
    session.log("Coverage report available at htmlcov/index.html")
