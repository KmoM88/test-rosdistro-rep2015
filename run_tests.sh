#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

MODE="${1:-light}"

echo "=========================================================="
echo "Building test-rosdistro-rep2015 Docker test environment..."
echo "=========================================================="
docker build -t test-rosdistro-rep2015 -f Dockerfile .

case "$MODE" in
    light)
        echo "=========================================================="
        echo "Running Light Integration Test Suite (test_integration.py)..."
        echo "=========================================================="
        docker run --rm test-rosdistro-rep2015 /workspace/.venv/bin/python3 /workspace/test_integration.py
        ;;
    full)
        echo "=========================================================="
        echo "Running Light Integration Tests (test_integration.py)..."
        echo "=========================================================="
        docker run --rm test-rosdistro-rep2015 /workspace/.venv/bin/python3 /workspace/test_integration.py
        echo ""
        echo "=========================================================="
        echo "Running Full End-to-End CLI Tests (test_full.py)..."
        echo "=========================================================="
        docker run --rm test-rosdistro-rep2015 /workspace/.venv/bin/python3 /workspace/test_full.py
        ;;
    *)
        echo "Error: Unknown test mode '$MODE'. Supported modes are 'light' or 'full'."
        exit 1
        ;;
esac
