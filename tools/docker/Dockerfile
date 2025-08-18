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

# Install pipenv
RUN python3.11 -m pip install pipenv

# Copy lock file if it exists (will fail gracefully if not present)
COPY Pipfile* ./

# Install Python packages from Pipfile.lock for reproducible builds
RUN if [ -f Pipfile.lock ]; then \
        echo "Installing packages from Pipfile.lock"; \
        pipenv install --deploy --ignore-pipfile --system; \
    else \
        echo "No Pipfile.lock found, skipping pip installation"; \
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
