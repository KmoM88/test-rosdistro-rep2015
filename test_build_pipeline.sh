#!/bin/bash
set -e

# Default to gz-cmake if no arguments are provided.
# If '--all' or 'ALL' is passed, target all packages across the distribution.
TARGET_PACKAGES=("$@")

if [ ${#TARGET_PACKAGES[@]} -eq 0 ]; then
    TARGET_PACKAGES=("gz-cmake")
elif [ "${TARGET_PACKAGES[0]}" == "--all" ]; then
    TARGET_PACKAGES=("ALL")
fi

echo "=========================================================="
echo "Starting Complete End-to-End Build Pipeline"
echo "Target packages: ${TARGET_PACKAGES[*]} via lyrical"
echo "=========================================================="

export ROSDISTRO_INDEX_URL="file:///workspace/index.yaml"

mkdir -p /workspace/build_ws/src
cd /workspace/build_ws

echo ""
echo "[1/4] Generating rosinstall specification using rosinstall_generator..."
/workspace/.venv/bin/rosinstall_generator "${TARGET_PACKAGES[@]}" --rosdistro lyrical --upstream > workspace.rosinstall
head -n 25 workspace.rosinstall
TOTAL_LINES=$(wc -l < workspace.rosinstall)
if [ "$TOTAL_LINES" -gt 25 ]; then
    echo "... ($TOTAL_LINES total lines generated in workspace.rosinstall)"
fi

echo ""
echo "[2/4] Cloning source checkout using vcstool..."
/workspace/.venv/bin/vcs import src < workspace.rosinstall

echo ""
echo "[3/4] Resolving and verifying dependencies with rosdep..."
/workspace/.venv/bin/rosdep install --from-paths src --ignore-src -y --rosdistro lyrical || true

echo ""
echo "[4/4] Building packages from source with colcon..."
/workspace/.venv/bin/colcon build --symlink-install

echo ""
echo "=========================================================="
echo "COMPLETE BUILD PIPELINE SUCCEEDED!"
echo "Target packages (${TARGET_PACKAGES[*]}) successfully built in /workspace/build_ws/install"
echo "=========================================================="
