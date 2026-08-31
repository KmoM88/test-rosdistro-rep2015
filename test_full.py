#!/usr/bin/env python3
import os
import sys
import subprocess

import rosdistro

def run_cmd(cmd_list, env=None):
    if env is None:
        env = os.environ.copy()
    proc = subprocess.run(cmd_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
    return proc.returncode, proc.stdout, proc.stderr

def run_full_test():
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    index_path = os.path.join(repo_dir, "index.yaml")
    index_url = f"file://{index_path}"

    venv_bin = os.path.dirname(sys.executable)
    rosdep_bin = os.path.join(venv_bin, "rosdep")
    rosinstall_bin = os.path.join(venv_bin, "rosinstall_generator")

    cli_env = os.environ.copy()
    cli_env['ROSDISTRO_INDEX_URL'] = index_url

    print("=" * 70)
    print("RUNNING FULL END-TO-END CLI TEST (LYRICAL EXTENDING JETTY)")
    print(f"Index URL: {index_url}")
    print("=" * 70)

    # -------------------------------------------------------------
    # 1. Standard CLI rosinstall_generator: Inherited Gazebo Packages
    # -------------------------------------------------------------
    print("\n[1/3] Testing standard CLI rosinstall_generator across distro boundaries...")
    for pkg in ["gz-sim", "gz-transport", "sdformat"]:
        code, stdout, stderr = run_cmd([rosinstall_bin, pkg, "--rosdistro", "lyrical", "--upstream"], env=cli_env)
        assert code == 0, f"rosinstall_generator failed for {pkg}: {stderr}"
        assert f"local-name: {pkg}" in stdout, f"local-name {pkg} missing in output"
        assert f"https://github.com/gazebosim/{pkg}" in stdout, f"URL for {pkg} missing in output"
        print(f"  -> rosinstall_generator {pkg}: PASSED")

    # -------------------------------------------------------------
    # 2. Standard CLI rosdep: Package Name & Distro Prefix Resolution
    # -------------------------------------------------------------
    print("\n[2/3] Testing standard CLI rosdep resolution (Ubuntu Resolute)...")
    expected_resolutions = {
        "std_msgs": "ros-lyrical-std-msgs",
        "turtlesim": "ros-lyrical-turtlesim",
        "ros_gz_sim": "ros-lyrical-ros-gz-sim",
        "ros_gz_bridge": "ros-lyrical-ros-gz-bridge",
    }
    for key, expected_pkg in expected_resolutions.items():
        code, stdout, stderr = run_cmd([
            rosdep_bin, "resolve", key,
            "--rosdistro", "lyrical",
            "--os=ubuntu:resolute"
        ], env=cli_env)
        assert code == 0, f"rosdep resolve failed for {key}: {stderr}"
        assert expected_pkg in stdout, f"Expected {expected_pkg} in output, got: {stdout}"
        print(f"  -> rosdep resolve {key} -> {expected_pkg}: PASSED")

    # -------------------------------------------------------------
    # 3. Direct Chained Distribution Cache Resolution
    # -------------------------------------------------------------
    print("\n[3/3] Testing chained distribution cache resolution...")
    idx = rosdistro.get_index(index_url)
    cached_dist = rosdistro.get_cached_distribution(idx, 'lyrical')

    # Verify packages from lyrical
    assert 'std_msgs' in cached_dist.release_packages
    assert 'turtlesim' in cached_dist.release_packages
    # Verify packages chained from jetty
    assert 'gz-sim' in cached_dist.release_packages
    assert 'gz-cmake' in cached_dist.release_packages
    assert 'gz-transport' in cached_dist.release_packages
    print("  -> Chained multi-distribution cache verified successfully.")

    print("\n" + "=" * 70)
    print("ALL FULL END-TO-END TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_full_test()
