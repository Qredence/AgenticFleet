.PHONY: install test lint format clean run

# Default target
all: install

# Install dependencies
install:
	./install_deps.sh

# Run tests
test:
	@echo "Running test suite using .venv and pytest..."
	@.venv/bin/python -m pytest

# Run linting
lint:
	flake8 src tests
	mypy src tests

# Format code
format:
	black src tests
	isort src tests

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

# Run the application
run:
	python -m agentic_fleet.main

# Help
help:
	@echo "Available targets:"
	@echo "  install  - Install dependencies"
	@echo "  test     - Run tests"
	@echo "  lint     - Run linting"
	@echo "  format   - Format code"
	@echo "  clean    - Clean build artifacts"
	@echo "  run      - Run the application"
	@echo "  help     - Show this help message"
