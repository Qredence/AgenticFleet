#!/bin/bash

# This script auto-formats code, optionally runs linting, and then keeps re-running tests until all pass.
# It helps you quickly clear up basic style issues and repetitive test loops during development.

DELAY=2  # Seconds to wait between retries (change as needed)

while true; do
    echo "-------------------------------------------"
    echo ">>> Auto-formatting code (black + isort)..."
    make format

    # If you want to auto-fix with ruff (if installed), uncomment:
    # ruff check src tests --fix

    echo ">>> (Optional) Running lint check (flake8 + mypy)..."
    # These will warn but won't block/test/fix. You can comment this out if too verbose.
    make lint || echo "Lint found issues. Please address those not fixed automatically."

    echo ">>> Running tests..."
    make test
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 0 ]; then
        echo ">>> All tests passed!"
        break
    else
        echo ">>> Some tests failed. Running format + lint and retrying in $DELAY seconds..."
        sleep $DELAY
    fi
done
