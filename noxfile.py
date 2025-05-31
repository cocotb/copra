"""Nox configuration for copra development tasks.

Cocotb Installation Optimization:
This noxfile supports several methods to speed up cocotb installation:

1. Pre-built wheel cache (automatic):
   - Wheels are automatically built and cached in .nox/cocotb_cache/ when installing from git
   - Run `nox -s build_cocotb_wheel` to pre-build and cache a cocotb wheel
   - Subsequent nox runs will automatically use compatible cached wheels
   - Wheels are built directly in the cache directory for efficiency

2. Local wheel file (manual):
   - Set COCOTB_LOCAL_WHEEL environment variable to path of a cocotb wheel
   - Example: COCOTB_LOCAL_WHEEL=/path/to/cocotb-2.0.0-py3-none-any.whl nox

3. Local source directory (development):
   - Set COCOTB_LOCAL_PATH environment variable to path of cocotb source
   - Example: COCOTB_LOCAL_PATH=/path/to/cocotb nox

4. Git source (fallback):
   - Default behavior when no cache or local paths are available
   - Automatically builds and caches wheels for future use

Cleaning:
- `nox -s clean` - Clean all build artifacts, caches, and nox environments
- `nox -s clean_cocotb_cache` - Clean only the cocotb wheel cache

Usage examples:
  nox                                    # Use best available cocotb installation
  nox -s build_cocotb_wheel             # Build and cache cocotb wheel
  nox -s clean                          # Clean all build artifacts (like 'make clean')
  nox -s clean_cocotb_cache             # Clean cached wheels only
  COCOTB_LOCAL_PATH=/path/to/cocotb nox  # Use local cocotb development copy
"""

import os
import shutil
from pathlib import Path

import nox

# Default sessions to run when no session is specified
nox.options.sessions = ["lint", "examples", "test"]

# Package information
PACKAGE = "copra"
PYTHON_VERSIONS = ["3.8", "3.9", "3.10", "3.11", "3.12"]

# Paths
HERE = Path(__file__).parent
SRC_DIR = HERE / "src"
DOCS_DIR = HERE / "docs"

# Cocotb installation options
COCOTB_LOCAL_WHEEL = os.environ.get("COCOTB_LOCAL_WHEEL")  # Path to local cocotb wheel
COCOTB_LOCAL_PATH = os.environ.get("COCOTB_LOCAL_PATH")  # Path to local cocotb source
COCOTB_CACHE_DIR = HERE / ".nox" / "cocotb_cache"  # Cache directory for built wheels


def get_cocotb_install_spec(session=None):
    """Get the cocotb installation specification.

    Returns the best available cocotb installation method:
    1. Local wheel file (if COCOTB_LOCAL_WHEEL is set)
    2. Local source path (if COCOTB_LOCAL_PATH is set)
    3. Cached wheel from previous build (if compatible with current session's Python)
    4. Git source (fallback)
    """
    # Option 1: Use explicitly specified local wheel
    if COCOTB_LOCAL_WHEEL and Path(COCOTB_LOCAL_WHEEL).exists():
        if session:
            session.log(f"Using local wheel: {COCOTB_LOCAL_WHEEL}")
        return COCOTB_LOCAL_WHEEL

    # Option 2: Use explicitly specified local source path
    if COCOTB_LOCAL_PATH and Path(COCOTB_LOCAL_PATH).exists():
        if session:
            session.log(f"Using local source: {COCOTB_LOCAL_PATH}")
        return f"-e {COCOTB_LOCAL_PATH}"

    # Option 3: Check for cached wheel from previous build
    if COCOTB_CACHE_DIR.exists():
        wheel_files = list(COCOTB_CACHE_DIR.glob("cocotb-*.whl"))
        if wheel_files:
            # Get Python version info for compatibility checking
            if session:
                # Get Python version from the session
                python_version = session.python
                major, minor = python_version.split(".")[:2]
                python_tag = f"{major}{minor}"
            else:
                # Fallback to system Python if no session
                import sys

                major, minor = sys.version_info.major, sys.version_info.minor
                python_version = f"{major}.{minor}"
                python_tag = f"{major}{minor}"

            # Filter for compatible wheels first
            compatible_wheels = []
            for wheel_file in wheel_files:
                wheel_name = wheel_file.name
                is_compatible = (
                    "py3-none-any" in wheel_name
                    or "py2.py3-none-any" in wheel_name
                    or f"cp{python_tag}" in wheel_name
                )
                if is_compatible:
                    compatible_wheels.append(wheel_file)

            if compatible_wheels:
                # Use the most recent compatible wheel
                latest_wheel = max(compatible_wheels, key=lambda p: p.stat().st_mtime)
                if session:
                    session.log(f"Using cached wheel: {latest_wheel}")
                return str(latest_wheel)
            else:
                if session:
                    session.log(
                        f"No compatible cached wheels found for Python {python_version}, "
                        f"falling back to git source"
                    )

    # Option 4: Fallback to git source
    if session:
        session.log("Using git source (no compatible cached wheel found)")
    return "git+https://github.com/cocotb/cocotb.git"


def install_cocotb_and_cache(session, cocotb_spec):
    """Install cocotb and automatically cache wheels when built from git source."""
    # If we're installing from git source, check if we already have a compatible cached wheel
    if cocotb_spec.startswith("git+"):
        # Check if we already have a compatible cached wheel
        if COCOTB_CACHE_DIR.exists():
            wheel_files = list(COCOTB_CACHE_DIR.glob("cocotb-*.whl"))
            if wheel_files:
                # Get Python version info for compatibility checking
                python_version = session.python
                major, minor = python_version.split(".")[:2]
                python_tag = f"{major}{minor}"

                # Filter for compatible wheels first
                compatible_wheels = []
                for wheel_file in wheel_files:
                    wheel_name = wheel_file.name
                    is_compatible = (
                        "py3-none-any" in wheel_name
                        or "py2.py3-none-any" in wheel_name
                        or f"cp{python_tag}" in wheel_name
                    )
                    if is_compatible:
                        compatible_wheels.append(wheel_file)

                if compatible_wheels:
                    # Use the most recent compatible wheel
                    latest_wheel = max(compatible_wheels, key=lambda p: p.stat().st_mtime)
                    session.log(f"Found compatible cached wheel: {latest_wheel}")
                    session.install(str(latest_wheel))
                    session.log("Installed cocotb from cached wheel")
                    return

        session.log("Installing cocotb from git source, attempting to build and cache wheel...")
        try:
            # Create cache directory
            COCOTB_CACHE_DIR.mkdir(parents=True, exist_ok=True)

            # Build wheel directly in the cache directory
            session.log(
                f"Building wheel for Python {session.python} in cache directory: {COCOTB_CACHE_DIR}"
            )

            # Build the wheel directly in the cache directory
            session.run(
                "python",
                "-m",
                "pip",
                "wheel",
                "--no-deps",
                "--wheel-dir",
                str(COCOTB_CACHE_DIR),
                cocotb_spec,
                external=True,
            )

            # Find the built wheel in cache directory
            wheel_files = list(COCOTB_CACHE_DIR.glob("cocotb-*.whl"))
            if wheel_files:
                # Use the most recently created wheel
                wheel_file = max(wheel_files, key=lambda p: p.stat().st_mtime)
                session.log(f"Built and cached cocotb wheel: {wheel_file}")

                # Install from the cached wheel
                session.install(str(wheel_file))
                session.log("Installed cocotb from newly built cached wheel")
                return
            else:
                session.log("No wheel file found after build, falling back to direct install")

        except Exception as e:
            session.log(f"Could not build and cache cocotb wheel: {e}")
            session.log("Falling back to direct git install")

    # Fallback to direct installation
    session.install(cocotb_spec)
    if cocotb_spec.startswith("git+"):
        session.log("Cocotb installed directly from git source")
    else:
        session.log("Using pre-built cocotb installation")


def install_with_constraints(session, *args, **kwargs):
    """Install packages with pip."""
    requirements = ["pip", "setuptools", "wheel"]
    session.install(*requirements, "--upgrade")

    # Separate cocotb from other packages for special handling
    cocotb_spec = None
    other_args = []

    for arg in args:
        if isinstance(arg, str) and (
            arg.startswith("git+https://github.com/cocotb/cocotb")
            or "cocotb" in arg
            and arg.endswith(".whl")
            or arg.startswith("-e")
            and "cocotb" in arg
        ):
            cocotb_spec = arg
        else:
            other_args.append(arg)

    # Install other packages first
    if other_args:
        session.install(*other_args, **kwargs)

    # Install and potentially cache cocotb
    if cocotb_spec:
        install_cocotb_and_cache(session, cocotb_spec)


@nox.session(python=PYTHON_VERSIONS[-1])
def lint(session):
    """Run the linter."""
    args = session.posargs or ["check", "src", "tests", "examples"]
    cocotb_spec = get_cocotb_install_spec(session)
    session.log(f"Installing cocotb from: {cocotb_spec}")
    install_with_constraints(
        session,
        "ruff",
        "mypy",
        "types-setuptools",
        "packaging",  # Required for version checking in __init__.py
        cocotb_spec,
    )
    session.run("ruff", *args)
    session.run("mypy", "--strict", "src")


@nox.session(python=PYTHON_VERSIONS[-1])
def examples(session):
    """Generate stubs for examples and check them with ruff."""
    cocotb_spec = get_cocotb_install_spec(session)
    session.log(f"Installing cocotb from: {cocotb_spec}")
    install_with_constraints(
        session,
        "ruff",
        cocotb_spec,
    )

    # Install our package without dependencies first, then let pip resolve
    session.install("-e", ".", "--no-deps")
    session.install("packaging")  # Required dependency for our package

    # Generate stubs for each example
    examples_dir = HERE / "examples"
    for example_dir in examples_dir.iterdir():
        if example_dir.is_dir() and (example_dir / "generate_stubs.py").exists():
            session.log(f"Generating stubs for example: {example_dir.name}")
            with session.chdir(example_dir):
                session.run("python", "generate_stubs.py")

                # Check generated stub files with ruff
                stub_files = list(example_dir.glob("*.pyi"))
                if stub_files:
                    session.log(
                        f"Checking generated stub files with ruff: {[f.name for f in stub_files]}"
                    )
                    session.run("ruff", "check", *[str(f) for f in stub_files])
                else:
                    session.log(f"No stub files found in {example_dir.name}")


@nox.session(python=PYTHON_VERSIONS)
def test(session):
    """Run the test suite."""
    cocotb_spec = get_cocotb_install_spec(session)
    session.log(f"Installing cocotb from: {cocotb_spec}")
    install_with_constraints(
        session,
        "pytest",
        "pytest-cov",
        "pytest-mock",
        "pytest-xdist",
        cocotb_spec,
    )
    # Install our package without dependencies first, then let pip resolve
    session.install("-e", ".", "--no-deps")
    session.install("packaging")  # Required dependency for our package
    session.run(
        "pytest",
        "--cov=src",
        "--cov-report=term-missing",
        "-n",
        "auto",
        *session.posargs,
        "tests",
    )


@nox.session(python=PYTHON_VERSIONS[-1])
def docs(session):
    """Build the documentation."""
    cocotb_spec = get_cocotb_install_spec(session)
    session.log(f"Installing cocotb from: {cocotb_spec}")
    install_with_constraints(
        session,
        "sphinx",
        "sphinx-copybutton",
        "furo",
        "myst-parser",
        cocotb_spec,
    )
    session.install("-e", ".")

    # Build docs
    build_dir = DOCS_DIR / "_build"
    if build_dir.exists():
        shutil.rmtree(build_dir)

    session.run(
        "sphinx-build",
        "-b",
        "html",
        "-d",
        f"{build_dir}/doctrees",
        "docs/source",
        f"{build_dir}/html",
    )


@nox.session(python=PYTHON_VERSIONS[-1])
def stubgen_example(session):
    """Run the stub generator on examples."""
    cocotb_spec = get_cocotb_install_spec(session)
    session.log(f"Installing cocotb from: {cocotb_spec}")
    install_with_constraints(session, cocotb_spec)

    # Install our package without dependencies first, then let pip resolve
    session.install("-e", ".", "--no-deps")
    session.install("packaging")  # Required dependency for our package

    # Demonstrate the stub generator with a simple example
    # This shows that the CLI tool is working correctly
    session.log("Testing stub generator CLI functionality...")

    # Test version command
    session.run("copra", "--version")

    # Test help command
    session.run("copra", "--help")

    session.log("Stub generator CLI is working correctly!")
    session.log(
        "To use with a real testbench, run: " "copra your_testbench_module --outfile stubs/dut.pyi"
    )


@nox.session(python=PYTHON_VERSIONS[-1])
def coverage(session):
    """Generate coverage report."""
    install_with_constraints(session, "coverage", "pytest-cov")
    session.run("coverage", "report", "--show-missing")
    session.run("coverage", "html")
    session.log("Coverage report available at htmlcov/index.html")


@nox.session(python=PYTHON_VERSIONS)
def build_cocotb_wheels_all(session):
    """Build cocotb wheels for all Python versions to improve caching."""
    session.log(f"Building cocotb wheel for Python {session.python}...")

    # Create cache directory
    COCOTB_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Install wheel building dependencies
    session.install("pip", "setuptools", "wheel", "--upgrade")

    # Build wheel directly from git source into cache directory
    session.log(
        f"Building wheel for Python {session.python} in cache directory: {COCOTB_CACHE_DIR}"
    )

    session.run(
        "python",
        "-m",
        "pip",
        "wheel",
        "--no-deps",
        "--wheel-dir",
        str(COCOTB_CACHE_DIR),
        "git+https://github.com/cocotb/cocotb.git",
        external=True,
    )

    # List created wheels for this Python version
    wheels = [
        w
        for w in COCOTB_CACHE_DIR.glob("cocotb-*.whl")
        if f"cp{session.python.replace('.', '')}" in w.name
    ]
    if wheels:
        latest_wheel = max(wheels, key=lambda p: p.stat().st_mtime)
        session.log(f"Successfully built wheel for Python {session.python}: {latest_wheel}")
    else:
        session.log(f"No wheel found for Python {session.python} after build")


@nox.session(python=PYTHON_VERSIONS[-1])
def build_cocotb_wheel(session):
    """Build cocotb wheel and cache it for faster subsequent runs.

    Note: This builds a wheel for the current Python version. If you need
    compatibility across multiple Python versions, consider using:
    - COCOTB_LOCAL_PATH for local development
    - COCOTB_LOCAL_WHEEL with a universal wheel
    - build_cocotb_wheels_all to build for all Python versions
    """
    session.log("Building cocotb wheel for caching...")

    # Create cache directory
    COCOTB_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Install wheel building dependencies
    session.install("pip", "setuptools", "wheel", "--upgrade")

    # Build wheel directly from git source into cache directory
    session.log(
        f"Building wheel for Python {session.python} in cache directory: {COCOTB_CACHE_DIR}"
    )
    session.log(f"This wheel will be compatible with Python {session.python}")

    session.run(
        "python",
        "-m",
        "pip",
        "wheel",
        "--no-deps",
        "--wheel-dir",
        str(COCOTB_CACHE_DIR),
        "git+https://github.com/cocotb/cocotb.git",
        external=True,
    )

    # List created wheels
    wheels = list(COCOTB_CACHE_DIR.glob("cocotb-*.whl"))
    if wheels:
        latest_wheel = max(wheels, key=lambda p: p.stat().st_mtime)
        session.log(f"Successfully built and cached cocotb wheel: {latest_wheel}")
        session.log(
            "This wheel will be automatically used in future nox runs "
            "with compatible Python versions."
        )
        session.log(f"Or you can explicitly use it with: COCOTB_LOCAL_WHEEL={latest_wheel}")

        # Check if it's a universal wheel
        if "py3-none-any" in latest_wheel.name or "py2.py3-none-any" in latest_wheel.name:
            session.log("✓ Built universal wheel - compatible with all Python versions")
        else:
            session.log(
                f"⚠ Built platform-specific wheel - only compatible with Python {session.python}"
            )
            session.log("To build for all Python versions, run: nox -s build_cocotb_wheels_all")
    else:
        session.error("Failed to create cocotb wheel")


@nox.session(python=PYTHON_VERSIONS[-1])
def clean(session):
    """Clean all build artifacts and caches (equivalent to 'make clean')."""
    import shutil

    # Directories to clean (similar to what 'make clean' would do)
    clean_dirs = [
        HERE / "build",
        HERE / "dist",
        HERE / ".pytest_cache",
        HERE / ".coverage",
        HERE / ".mypy_cache",
        HERE / ".ruff_cache",
        HERE / "htmlcov",
        DOCS_DIR / "_build",
        COCOTB_CACHE_DIR,  # Our cocotb wheel cache
    ]

    # Clean egg-info directories
    for egg_info in HERE.rglob("*.egg-info"):
        clean_dirs.append(egg_info)

    # Clean __pycache__ directories
    for pycache in HERE.rglob("__pycache__"):
        clean_dirs.append(pycache)

    # Clean nox environments (except current one)
    nox_dir = HERE / ".nox"
    if nox_dir.exists():
        for env_dir in nox_dir.iterdir():
            if env_dir.is_dir() and env_dir.name != session.name:
                clean_dirs.append(env_dir)

    cleaned = []
    for clean_dir in clean_dirs:
        if clean_dir.exists():
            if clean_dir.is_file():
                clean_dir.unlink()
                cleaned.append(str(clean_dir))
            else:
                shutil.rmtree(clean_dir)
                cleaned.append(str(clean_dir))

    if cleaned:
        session.log("Cleaned:")
        for item in cleaned:
            session.log(f"  {item}")
    else:
        session.log("Nothing to clean")


@nox.session(python=PYTHON_VERSIONS[-1])
def clean_cocotb_cache(session):
    """Clean only the cocotb wheel cache."""
    if COCOTB_CACHE_DIR.exists():
        shutil.rmtree(COCOTB_CACHE_DIR)
        session.log(f"Cleaned cocotb cache: {COCOTB_CACHE_DIR}")
    else:
        session.log("Cocotb cache directory does not exist")
