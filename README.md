# ROS Distribution Extension Test Suite (REP-2015)

This repository serves as a dedicated, standalone integration test environment to validate the modifications implemented in `rosdistro`, `rosdep`, and `rosinstall_generator` to support [REP-2015](https://ros.org/reps/rep-2015.html) (ROS Distribution Extensions).

The test suite validates cross-distribution inheritance by using **`lyrical`** (a downstream ROS 2 distribution from the user fork) directly extending **`jetty`** (a custom upstream Gazebo distribution) using the `source_rebuild` extension method.

---

## Repository Architecture

This repository operates completely autonomously using the following Git submodules:

* **`submodules/rosdistro`**: Fork of `rosdistro` on branch `feature/rep-2015-v3-parser` containing the Version 3 distribution file parser, circular inheritance validation, platform compatibility checks, repository specification merging, and chained in-memory cache resolution.
* **`submodules/rosdep`**: Fork of `rosdep` on branch `feature/rep-2015-tool-integration` supporting REP-2015 distribution prefix translation for `source_rebuild` and `binary_import`.
* **`submodules/rosinstall_generator`**: Fork of `rosinstall_generator` on branch `feature/rep-2015-tool-integration` querying chained distribution caches across distribution boundaries.
* **`submodules/gazebodistro`**: Custom Gazebo package repository on branch `jrivero/jetty-rosdistro` containing the base `jetty` package specifications.
* **`submodules/ros-rosdistro`**: Fork of `rosdistro` distribution metadata on branch `feature/rep-2015-jetty-extension` containing the downstream `lyrical` distribution configured with format version 3 and extending `jetty`.

---

## Getting Started

Clone this repository with the `--recursive` flag to pull all required toolchains and metadata submodules:

```bash
git clone --recursive https://github.com/KmoM88/test-rosdistro-rep2015.git
cd test-rosdistro-rep2015
```

If you already cloned without `--recursive`:
```bash
git submodule update --init --recursive
```

---

## Running the Tests

You can execute the test suite either inside an isolated Docker container (recommended) or manually on the host machine.

### Method 1: Using the Automated Docker Script (Recommended)

Run the unified Docker execution script:
```bash
./run_tests.sh
```

---

### Method 2: Manual Step-by-Step Execution inside Docker

If you prefer to inspect and run each step manually inside the container:

1. **Build the Docker container image**:
   ```bash
   docker build -t test-rosdistro-rep2015 -f Dockerfile .
   ```

2. **Start an interactive container session**:
   ```bash
   docker run --rm -it test-rosdistro-rep2015 bash
   ```

3. **Execute the integration test suite**:
   ```bash
   /workspace/.venv/bin/python3 /workspace/test_integration.py
   ```

4. **Verify individual tools interactively**:
   ```bash
   export ROSDISTRO_INDEX_URL="file:///workspace/index.yaml"
   
   # Test rosinstall_generator resolving an inherited Gazebo package under lyrical:
   .venv/bin/rosinstall_generator gz-sim --rosdistro lyrical --upstream
   
   # Test rosdep database dump:
   .venv/bin/rosdep db | grep -A 5 "ros-lyrical-turtlesim"
   ```

---

### Method 3: Manual Step-by-Step Execution on the Host Machine

To run the tests directly on your host environment (Ubuntu / Linux):

1. **Create and activate a Python virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   ```

2. **Install the modified submodules in editable mode (`-e`)**:
   ```bash
   pip install -e submodules/rosdistro[test]
   pip install -e submodules/rosdep[test]
   pip install -e submodules/rosinstall_generator
   ```

3. **Initialize `rosdep` (if not already initialized on the host)**:
   ```bash
   export ROSDEP_LOCAL_DEV=true
   rosdep init || true
   rosdep update || true
   ```

4. **Export the test index URL pointing to the local `index.yaml`**:
   ```bash
   export ROSDISTRO_INDEX_URL="file://$(pwd)/index.yaml"
   ```

5. **Run the integration test script**:
   ```bash
   python3 test_integration.py
   ```

---

## Expected Outputs

When running `test_integration.py`, the following output confirms all tests pass successfully:

```text
============================================================
Testing REP-2015 Extension: Lyrical extending Gazebo Jetty
Using index: file:///workspace/index.yaml
============================================================

[1/3] Testing rosdistro distribution inheritance and resolution...
WARNING: Target platform 'debian:trixie' specified in derived distribution is not supported by base distribution.
WARNING: Target platform 'fedora:43' specified in derived distribution is not supported by base distribution.
WARNING: Target platform 'rhel:10' specified in derived distribution is not supported by base distribution.
WARNING: Target platform 'ubuntu:resolute' specified in derived distribution is not supported by base distribution.
 -> rosdistro distribution file inheritance verified successfully.

[2/3] Testing rosdistro chained in-memory cache resolution...
 -> rosdistro in-memory chained cache verified successfully.

[3/3] Testing rosinstall_generator repository resolution across distro boundaries...
Generated rosinstall entry:
- git:
    local-name: gz-sim
    uri: https://github.com/gazebosim/gz-sim
    version: 10.5.0
 -> rosinstall_generator resolved inherited Gazebo source successfully.

[4/4] Testing rosdep package resolutions under source_rebuild...
Query rosdistro index file:///workspace/index.yaml
Add distro "jetty"
Add distro "lyrical"
 -> lyrical turtlesim resolves to: ['ros-lyrical-turtlesim']
 -> lyrical std_msgs resolves to: ['ros-lyrical-std-msgs']
 -> lyrical ros_gz_sim resolves to: ['ros-lyrical-ros-gz-sim']
 -> lyrical ros_gz_bridge resolves to: ['ros-lyrical-ros-gz-bridge']
 -> rosdep package prefix resolutions verified successfully.

============================================================
ALL REP-2015 EXTENSION TESTS PASSED SUCCESSFULLY!
============================================================
```

---

## Detailed Breakdown: What is Tested

### 1. `rosdistro`
* **Version 3 Schema Parsing**: Parses distribution files declaring `type: distribution` and `version: 3`.
* **Inheritance & Loop Prevention**: Validates the `extends` directive and detects potential circular inheritance graphs.
* **Platform Compatibility Warnings**: Validates target platforms of derived distributions against base platforms. When `lyrical` specifies platforms exceeding `jetty` (`noble` vs `trixie`, `resolute`, etc.), `rosdistro` issues descriptive warnings without crashing.
* **Repository Specification Merging**: Merges parent repository specifications into the child repository so child distributions inherit source Git URLs while defining local release versions.
* **Chained Cache Resolution**: Resolves multi-tier distribution caches dynamically in-memory without requiring flattened, duplicated on-disk cache files.

### 2. `rosinstall_generator`
* **Cross-Distribution Querying**: Queries package names across chained distribution boundaries using `--rosdistro lyrical`.
* **Upstream Git Checkout Generation**: Successfully extracts the Git repository URL (`https://github.com/gazebosim/gz-sim`) and version tag (`10.5.0`) for `gz-sim` (which is inherited from `jetty`) and formats it as a `.rosinstall` YAML block.

### 3. `rosdep`
* **Package Prefix Translation**: Validates the modified `rosdep` naming logic in `gbpdistro_support.py`.
* **`source_rebuild` Renaming**: Under `source_rebuild`, packages rebuilt into the downstream environment are renamed with the downstream prefix (`ros-lyrical-*`):
  * `turtlesim` $\rightarrow$ `ros-lyrical-turtlesim`
  * `std_msgs` $\rightarrow$ `ros-lyrical-std-msgs`
  * `ros_gz_sim` $\rightarrow$ `ros-lyrical-ros-gz-sim`
  * `ros_gz_bridge` $\rightarrow$ `ros-lyrical-ros-gz-bridge`

---

## Test Adaptations and Exceptions

To ensure tests run hermetically and reproducibly, the following adaptations were implemented:

1. **`rosdep` Isolated Environment**:
   * Standard `rosdep` reads `/etc/ros/rosdep/sources.list.d/`, which can point to public remote internet sources.
   * In `test_integration.py`, an isolated temporary directory (`tempfile.mkdtemp()`) is configured via `ROS_HOME` and `ROSDEP_SOURCE_PATH` with a local dummy sources list. This ensures `rosdep` only tests the in-tree `index.yaml` and does not query external networks.
2. **`ReleaseFile` and Source-Only Repositories**:
   * `rosdep`'s `ReleaseFile` inspects packages that define binary `release:` specifications (GBP releases).
   * Upstream Gazebo `jetty` only declares `source:` Git specifications in its distribution file (source-only build).
   * As expected, `rosinstall_generator` handles source checkouts, while `rosdep` verifies binary package name mapping for released packages (`std_msgs`, `turtlesim`, `ros_gz_sim`).
3. **Chained In-Memory Caches**:
   * In compliance with REP-2015 chained caching, `lyrical-cache.yaml` only declares packages local to `lyrical`. Packages from `jetty` (`gz-sim`, `gz-cmake`, etc.) are resolved and merged dynamically in-memory from `jetty-cache.yaml`.
