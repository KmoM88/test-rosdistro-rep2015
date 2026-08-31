#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================================="
echo "Building test-rosdistro-rep2015 Docker test environment..."
echo "=========================================================="
docker build -t test-rosdistro-rep2015 -f Dockerfile .

echo "=========================================================="
echo "Running REP-2015 Integration Test Suite inside Docker..."
echo "=========================================================="
docker run --rm test-rosdistro-rep2015 /workspace/.venv/bin/python3 /workspace/test_integration.py
