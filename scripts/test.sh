#!/bin/sh

EXIT=0

echo "TEST: black"
black --check --diff . || EXIT=$?

echo "TEST: isort"
isort --recursive --check-only . || EXIT=$?

export PYTHONWARNINGS="ignore"
echo "TEST: flake8"
flake8 . || EXIT=$?
export PYTHONWARNINGS="default"

echo "TEST: pytest"
python -m pytest ./tests/ || EXIT=$?

exit $EXIT
