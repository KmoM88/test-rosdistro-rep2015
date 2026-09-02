#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess
import tempfile
import yaml
from urllib.request import pathname2url

import rosdistro
from rosdep2.gbpdistro_support import get_gbprepo_as_rosdep_data
import rosdep2.rosdistrohelper
from rosdep2.sources_list import update_sources_list

def run_integration_test():
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    index_path = os.path.join(repo_dir, "index.yaml")
    index_url = f"file://{index_path}"
    
    print("=" * 60)
    print(f"Testing REP-2015 Extension: Lyrical extending Gazebo Jetty")
    print(f"Using index: {index_url}")
    print("=" * 60)
    
    os.environ['ROSDISTRO_INDEX_URL'] = index_url
    idx = rosdistro.get_index(index_url)

    # -------------------------------------------------------------
    # 1. Test rosdistro: Version 3 Distribution File Inheritance
    # -------------------------------------------------------------
    print("\n[1/3] Testing rosdistro distribution inheritance and resolution...")
    dist_file = rosdistro.get_distribution_file(idx, 'lyrical')
    
    # Verify local packages in lyrical
    assert 'std_msgs' in dist_file.release_packages, "std_msgs should be in lyrical release_packages"
    assert 'turtlesim' in dist_file.release_packages, "turtlesim should be in lyrical release_packages"
    
    # Verify inherited Gazebo packages from jetty
    assert 'gz-sim' in dist_file.repositories, "gz-sim should be inherited in lyrical repositories"
    assert 'gz-transport' in dist_file.repositories, "gz-transport should be inherited in lyrical repositories"
    assert 'sdformat' in dist_file.repositories, "sdformat should be inherited in lyrical repositories"
    
    # Verify inherited source repository metadata
    gz_sim_repo = dist_file.repositories['gz-sim']
    assert gz_sim_repo.source_repository is not None, "gz-sim must have source_repository defined"
    assert gz_sim_repo.source_repository.type == 'git', "gz-sim source repository type must be git"
    assert gz_sim_repo.source_repository.url == 'https://github.com/gazebosim/gz-sim', "gz-sim git URL mismatch"
    assert gz_sim_repo.source_repository.version == 'gz-sim10', "gz-sim branch/version mismatch"
    print(" -> rosdistro distribution file inheritance verified successfully.")

    # -------------------------------------------------------------
    # 2. Test rosdistro: Chained In-Memory Cache Resolution
    # -------------------------------------------------------------
    print("\n[2/3] Testing rosdistro chained in-memory cache resolution...")
    cached_dist = rosdistro.get_cached_distribution(idx, 'lyrical')
    
    # Verify local packages in cache
    assert 'std_msgs' in cached_dist.release_packages, "std_msgs missing in chained cache"
    assert 'turtlesim' in cached_dist.release_packages, "turtlesim missing in chained cache"
    
    # Verify chained packages from jetty cache
    assert 'gz-sim' in cached_dist.release_packages, "gz-sim missing in chained cache"
    assert 'gz-cmake' in cached_dist.release_packages, "gz-cmake missing in chained cache"
    assert 'gz-common' in cached_dist.release_packages, "gz-common missing in chained cache"
    print(" -> rosdistro in-memory chained cache verified successfully.")

    # -------------------------------------------------------------
    # 3. Test rosinstall_generator: Cross-Distribution Source Resolution
    # -------------------------------------------------------------
    print("\n[3/3] Testing rosinstall_generator repository resolution across distro boundaries...")
    env = os.environ.copy()
    env['ROSDISTRO_INDEX_URL'] = index_url
    
    output = subprocess.check_output([
        sys.executable,
        os.path.join(os.path.dirname(sys.executable), 'rosinstall_generator'),
        'gz-sim',
        '--rosdistro', 'lyrical',
        '--upstream'
    ], env=env).decode('utf-8')
    
    print("Generated rosinstall entry:")
    print(output.strip())
    assert 'local-name: gz-sim' in output, "local-name: gz-sim missing in rosinstall output"
    assert 'uri: https://github.com/gazebosim/gz-sim' in output, "Git URI missing in rosinstall output"
    assert 'gz-sim10_10.5.0' in output, "Expected release tag gz-sim10_10.5.0 in rosinstall output"
    print(" -> rosinstall_generator resolved inherited Gazebo source successfully.")

    # -------------------------------------------------------------
    # 4. Test rosdep: Package Name & Distro Prefix Translation
    # -------------------------------------------------------------
    print("\n[4/4] Testing rosdep package resolutions under source_rebuild...")
    tmpdir = tempfile.mkdtemp()
    try:
        os.environ['ROS_HOME'] = tmpdir
        sources_list_dir = os.path.join(tmpdir, 'sources.list.d')
        os.makedirs(sources_list_dir)
        os.environ['ROSDEP_SOURCE_PATH'] = sources_list_dir

        dummy_yaml = os.path.join(tmpdir, 'dummy.yaml')
        with open(dummy_yaml, 'w') as y:
            y.write('')
        dummy_url = f"file://{pathname2url(dummy_yaml)}"
        with open(os.path.join(sources_list_dir, '20-default.list'), 'w') as f:
            f.write(f"yaml {dummy_url}\n")

        # Reset rosdep helper caches
        rosdep2.rosdistrohelper._RDCache.index_url = index_url
        rosdep2.rosdistrohelper._RDCache.index = None
        rosdep2.rosdistrohelper._RDCache.release_files = {}

        update_sources_list()
        rosdep_lyrical = get_gbprepo_as_rosdep_data('lyrical')
        
        # Verify standard ROS 2 packages resolve with ros-lyrical- prefix
        assert 'std_msgs' in rosdep_lyrical
        assert 'turtlesim' in rosdep_lyrical
        res_turtlesim = rosdep_lyrical['turtlesim']['ubuntu']['resolute']['apt']['packages']
        print(f" -> lyrical turtlesim resolves to: {res_turtlesim}")
        assert res_turtlesim == ['ros-lyrical-turtlesim']

        res_std_msgs = rosdep_lyrical['std_msgs']['ubuntu']['resolute']['apt']['packages']
        print(f" -> lyrical std_msgs resolves to: {res_std_msgs}")
        assert res_std_msgs == ['ros-lyrical-std-msgs']

        # Verify Gazebo bridge integration packages resolve with ros-lyrical- prefix
        assert 'ros_gz_sim' in rosdep_lyrical
        assert 'ros_gz_bridge' in rosdep_lyrical
        res_ros_gz_sim = rosdep_lyrical['ros_gz_sim']['ubuntu']['resolute']['apt']['packages']
        print(f" -> lyrical ros_gz_sim resolves to: {res_ros_gz_sim}")
        assert res_ros_gz_sim == ['ros-lyrical-ros-gz-sim']

        res_ros_gz_bridge = rosdep_lyrical['ros_gz_bridge']['ubuntu']['resolute']['apt']['packages']
        print(f" -> lyrical ros_gz_bridge resolves to: {res_ros_gz_bridge}")
        assert res_ros_gz_bridge == ['ros-lyrical-ros-gz-bridge']

        print(" -> rosdep package prefix resolutions verified successfully.")
    finally:
        shutil.rmtree(tmpdir)

    print("\n" + "=" * 60)
    print("ALL REP-2015 EXTENSION TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_integration_test()
