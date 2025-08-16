# Use Ubuntu 22.04 as base image
FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    software-properties-common \
    curl \
    wget \
    git \
    vim \
    nano \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Install Python 3.11
RUN add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python3.11 python3.11-dev python3.11-venv python3.11-distutils && \
    rm -rf /var/lib/apt/lists/*

# Create symbolic links for python3.11
RUN ln -sf /usr/bin/python3.11 /usr/local/bin/python3.11 && \
    ln -sf /usr/bin/python3.11 /usr/local/bin/python3 && \
    ln -sf /usr/bin/python3.11 /usr/local/bin/python

# Upgrade pip
RUN python3.11 -m pip install --upgrade pip setuptools wheel

# Copy lock file if it exists (will fail gracefully if not present)
COPY pip.lock* ./

# Install Python packages only if pip.lock exists
RUN if [ -f pip.lock ]; then \
        echo "Using pip.lock for reproducible build"; \
        pip3 install -r pip.lock; \
    else \
        echo "No pip.lock found, skipping pip installation"; \
    fi

# Create a non-root user
RUN useradd -m -s /bin/bash vscode && \
    usermod -aG sudo vscode && \
    echo "vscode ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Set working directory
WORKDIR /workspace

# Change ownership of the workspace
RUN chown -R vscode:vscode /workspace

# Switch to non-root user
USER vscode

# Set default shell
SHELL ["/bin/bash", "-c"]

# Expose Jupyter port
EXPOSE 8888

# Default command
CMD ["/bin/bash"]
