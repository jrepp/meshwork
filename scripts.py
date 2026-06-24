#!/usr/bin/env python3
"""Development scripts for meshwork."""

import subprocess
import sys


def run(cmd: str, **kwargs) -> int:
    """Run command and return exit code."""
    print(f"→ {cmd}")
    return subprocess.run(cmd, shell=True, **kwargs).returncode


def test() -> int:
    """Run tests."""
    return run(f"{sys.executable} -m pytest")


def coverage() -> int:
    """Run tests with coverage."""
    return run(
        f"{sys.executable} -m pytest --cov=meshwork --cov-report=term-missing "
        "--cov-report=html --cov-report=xml"
    )


def integration() -> int:
    """Run integration tests."""
    return run(
        f'{sys.executable} -m pytest -o addopts="-v --strict-markers" '
        "-m integration tests/integration"
    )


def lint() -> int:
    """Check code quality."""
    return run(f"{sys.executable} -m ruff check .")


def format_check() -> int:
    """Check code formatting."""
    return run(f"{sys.executable} -m ruff format --check .")


def format_code() -> int:
    """Format code."""
    return run(f"{sys.executable} -m ruff format .")


def typecheck() -> int:
    """Type check code."""
    return run(
        f"{sys.executable} -m mypy "
        "meshwork/core meshwork/transports/memory.py tests/test_public_api.py"
    )


def conformance() -> int:
    """Check Python source conformance."""
    return run(f"{sys.executable} -m compileall -q meshwork tests scripts.py")


def check() -> int:
    """Run all checks."""
    return format_check() or lint() or typecheck() or conformance() or test()


def fix() -> int:
    """Fix all auto-fixable issues."""
    return run(f"{sys.executable} -m ruff check --fix .") or format_code()


def clean() -> int:
    """Clean build artifacts."""
    paths = [
        ".pytest_cache",
        "htmlcov",
        ".coverage",
        "coverage.xml",
        "dist",
        "build",
        "*.egg-info",
        "__pycache__",
        "*/__pycache__",
        "*/*/__pycache__",
        ".mypy_cache",
        ".ruff_cache",
    ]

    for pattern in paths:
        run(f"rm -rf {pattern}")

    return 0


def install() -> int:
    """Install dependencies."""
    return run("uv sync --group dev")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Available commands:")
        print("  test      - Run tests")
        print("  coverage  - Run tests with coverage")
        print("  integration - Run integration tests")
        print("  lint      - Check code quality")
        print("  fmt-check - Check code formatting")
        print("  format    - Format code")
        print("  typecheck - Type check code")
        print("  conform   - Check Python source conformance")
        print("  check     - Run all checks")
        print("  fix       - Fix auto-fixable issues")
        print("  clean     - Clean build artifacts")
        print("  install   - Install dependencies")
        return 1

    cmd = sys.argv[1]

    commands = {
        "test": test,
        "coverage": coverage,
        "integration": integration,
        "lint": lint,
        "fmt-check": format_check,
        "format": format_code,
        "typecheck": typecheck,
        "conform": conformance,
        "check": check,
        "fix": fix,
        "clean": clean,
        "install": install,
    }

    if cmd not in commands:
        print(f"Unknown command: {cmd}")
        return 1

    return commands[cmd]()


if __name__ == "__main__":
    sys.exit(main())
