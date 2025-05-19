#!/bin/bash
# Simple shell script to run pytest tests

# Set the PYTHONPATH to include the src directory
export PYTHONPATH=$PYTHONPATH:$(pwd)/src

# Run pytest with the specified arguments or with default arguments if none provided
if [ $# -eq 0 ]; then
    echo "Running all tests with default arguments..."
    python -m pytest tests/ -v --color=yes
else
    echo "Running tests with arguments: $@"
    python -m pytest "$@"
fi
