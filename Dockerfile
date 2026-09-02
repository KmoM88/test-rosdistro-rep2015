FROM ubuntu:noble

ENV DEBIAN_FRONTEND=noninteractive

# Install core runtime and build dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    sudo \
    build-essential \
    cmake \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Copy repository files into the container
COPY . /workspace

# Remove embedded .git files from submodules to avoid submodule git lockouts inside container
RUN find submodules/ -name .git -type f -delete

ENV ROSDEP_LOCAL_DEV=true

# Ensure any host-copied virtual environments or caches are purged
RUN rm -rf /workspace/.venv

# Create python virtual environment in /opt/venv and link to /workspace/.venv
RUN python3 -m venv /opt/venv \
    && ln -s /opt/venv /workspace/.venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install \
        -e submodules/rosdistro[test] \
        -e submodules/rosdep[test] \
        -e submodules/rosinstall_generator \
        vcstool \
        colcon-common-extensions

# Initialize rosdep in container
RUN .venv/bin/rosdep init || true \
    && .venv/bin/rosdep update || true

CMD ["/workspace/.venv/bin/python3", "/workspace/test_integration.py"]
