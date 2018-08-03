#!/bin/sh

echo "Running black"
if black --check --diff .; then
    echo "Black OK"
else
    echo "Black FAILED"
fi

echo "Running isort"
if isort --recursive --check-only .; then
    echo "Isort OK"
else
    echo "Isort FAILED"
fi

echo "Running flake8"
if flake8 .; then
    echo "Flake8 OK"
else
    echo "Flake8 FAILED"
fi
