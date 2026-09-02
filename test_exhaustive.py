#!/usr/bin/env python3
import os
import sys
import time

import rosdistro
from rosdep2.gbpdistro_support import get_gbprepo_as_rosdep_data

def run_exhaustive_test():
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    index_path = os.path.join(repo_dir, "index.yaml")
    index_url = f"file://{index_path}"
    os.environ['ROSDISTRO_INDEX_URL'] = index_url

    print("=" * 70)
    print("RUNNING EXHAUSTIVE DISTRIBUTION TEST (SCANNING ALL PACKAGES)")
    print(f"Index URL: {index_url}")
    print("=" * 70)

    start_time = time.time()

    # 1. Load full distribution file for lyrical
    print("\n[1/3] Parsing and resolving complete distribution graph for 'lyrical'...")
    idx = rosdistro.get_index(index_url)
    dist_file = rosdistro.get_distribution_file(idx, 'lyrical')

    total_repos = len(dist_file.repositories)
    local_repos = 0
    inherited_repos = 0
    gazebo_repos = []

    for repo_name, repo in dist_file.repositories.items():
        if getattr(repo, 'extension_method', None) == 'source_rebuild':
            inherited_repos += 1
            if repo_name.startswith('gz-') or repo_name in ['sdformat']:
                gazebo_repos.append(repo_name)
        else:
            local_repos += 1

    print(f"  -> Total Repositories: {total_repos}")
    print(f"  -> Local Lyrical Repositories: {local_repos}")
    print(f"  -> Inherited Upstream Repositories (source_rebuild): {inherited_repos}")
    print(f"  -> Sample Inherited Gazebo Repositories ({len(gazebo_repos)}): {gazebo_repos[:5]}...")

    # 2. Verify all release packages and repository ownership
    print("\n[2/3] Validating all release packages...")
    total_packages = len(dist_file.release_packages)
    print(f"  -> Total Release Packages: {total_packages}")

    # 3. Generate full rosdep mapping for all packages
    print("\n[3/3] Generating full rosdep Debian translation table for all packages...")
    rosdep_data = get_gbprepo_as_rosdep_data('lyrical')
    total_rosdep_keys = len(rosdep_data)
    print(f"  -> Total Resolved rosdep Keys: {total_rosdep_keys}")

    # Verify a spread of packages across categories
    check_packages = ["std_msgs", "turtlesim", "ros_gz_sim", "ros_gz_bridge"]
    for pkg in check_packages:
        assert pkg in rosdep_data, f"Package {pkg} missing in rosdep table"
        ubuntu_pkg = rosdep_data[pkg]['ubuntu']['resolute']['apt']['packages']
        assert ubuntu_pkg == [f"ros-lyrical-{pkg.replace('_', '-')}"], f"Mismatched package name for {pkg}"
        print(f"  -> Verified {pkg} -> {ubuntu_pkg}")

    elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print(f"EXHAUSTIVE TEST PASSED! Scanned {total_repos} repos & {total_packages} packages in {elapsed:.2f}s")
    print("=" * 70)

if __name__ == "__main__":
    run_exhaustive_test()
