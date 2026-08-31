FROM ubuntu:noble

ENV DEBIAN_FRONTEND=noninteractive

# Install core runtime dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    sudo \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Copy repository files into the container
COPY . /workspace

# Remove embedded .git files from submodules to avoid submodule git lockouts inside container
RUN find submodules/ -name .git -type f -delete

ENV ROSDEP_LOCAL_DEV=true

# Create python virtual environment and install toolchain submodules in editable mode
RUN python3 -m venv .venv \
    && .venv/bin/pip install --upgrade pip \
    && .venv/bin/pip install \
        -e submodules/rosdistro[test] \
        -e submodules/rosdep[test] \
        -e submodules/rosinstall_generator

# Initialize rosdep in container
RUN .venv/bin/rosdep init || true \
    && .venv/bin/rosdep update || true

CMD ["/workspace/.venv/bin/python3", "/workspace/test_integration.py"]
