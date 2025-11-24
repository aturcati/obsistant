# Obsistant Justfile
# Define tasks for the project

# Set up with `just --list` to see available commands

default:
    @just --list

install:
    # Install the package
    uv sync

dev-install:
    # Install development dependencies
    uv sync --extra dev

test:
    # Run tests
    uv run pytest

test-coverage:
    # Run tests with coverage
    uv run pytest --cov=obsistant --cov-report=html --cov-report=term

lint:
    # Run linting
    uv run ruff check .
    uv run ty check obsistant

format:
    # Format code
    uv run black .
    uv run ruff format .

format-check:
    # Check if code is formatted
    uv run black --check .
    uv run ruff format --check .

clean:
    # Clean build artifacts
    rm -rf build/
    rm -rf dist/
    rm -rf *.egg-info/
    rm -rf .pytest_cache/
    rm -rf .coverage
    rm -rf htmlcov/
    rm -rf .ty_cache/
    rm -rf .ruff_cache/
    find . -type d -name __pycache__ -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete

build:
    # Build the package
    just clean
    uv build

publish:
    # Publish to PyPI
    just build
    uv publish

pre-commit-install:
    # Install pre-commit hooks
    uv run pre-commit install

pre-commit-run:
    # Run pre-commit on all files
    uv run pre-commit run --all-files

check:
    # Run all checks (lint and test)
    just lint
    just test

ci:
    # Run CI checks
    just format-check
    just lint
    just test
