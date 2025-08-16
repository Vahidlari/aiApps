# Docker Image Management

This directory contains scripts and configuration files for building and managing the development Docker image used by the devcontainer.

## Files

- `Dockerfile` - Defines the development environment with Python 3.11 and common AI/ML tools
- `build-docker.sh` - Script to build and optionally push the Docker image to GitHub Container Registry
- `requirements.txt` - Python dependencies for the development environment
- `generate-lock.sh` - Script to generate pip.lock for reproducible builds
- `pip.lock` - Lock file with exact package versions for reproducible builds

## Prerequisites

1. Docker installed and running
2. GitHub account with access to the repository
3. GitHub Personal Access Token with `write:packages` permission

## Usage

### Basic Usage

The `build-docker.sh` script accepts the following arguments:

- `-u, --update-pip-lock` - Generate/update pip.lock file
- `-p, --push` - Push image to GitHub Container Registry
- `-h, --help` - Show help message

### Examples

```bash
cd tools/docker

# Build image only (uses existing pip.lock if available)
./build-docker.sh

# Update pip.lock and build image
./build-docker.sh -u

# Build and push image
./build-docker.sh -p

# Update pip.lock, build and push image
./build-docker.sh -u -p
```

### First-Time Setup

1. **Generate initial pip.lock:**
   ```bash
   cd tools/docker
   ./build-docker.sh -u
   ```

2. **Build and push to registry:**
   ```bash
   ./build-docker.sh -u -p
   ```

### Updating Dependencies

1. **Modify requirements.txt** with new packages
2. **Update pip.lock and rebuild:**
   ```bash
   ./build-docker.sh -u -p
   ```

## Image Tags

The script creates two tags:
- `latest` - Always points to the most recent build
- `YYYYMMDD` - Date-based tag (e.g., `20241201`)

## GitHub Container Registry Setup

1. Go to your GitHub repository settings
2. Navigate to "Packages" section
3. Ensure the package visibility is set as desired (public or private)
4. The image will be available at: `ghcr.io/your-username/aiapps/ai-dev:latest`

## DevContainer Configuration

The `.devcontainer/devcontainer.json` file is configured to use the image from GitHub Container Registry. The image reference is:

```
ghcr.io/${localEnv:GITHUB_REPOSITORY:-your-username/aiapps}/ai-dev:latest
```

## How It Works

### Dockerfile Logic

The Dockerfile handles pip.lock gracefully:

1. **Copies requirements.txt** (always present)
2. **Copies pip.lock** (if it exists, fails gracefully if not)
3. **Installs packages:**
   - If pip.lock exists: Uses it for reproducible build
   - If pip.lock doesn't exist: Installs from requirements.txt

### Build Process

1. **User decides** whether to update pip.lock (`-u` flag)
2. **Script generates** pip.lock if requested (requires Python environment)
3. **Docker builds** image using available files
4. **User decides** whether to push to registry (`-p` flag)

## Troubleshooting

### Permission Denied
Make sure the script is executable:
```bash
chmod +x tools/docker/build-docker.sh
```

### Authentication Issues
- Verify your GitHub token has the correct permissions
- Check that you're logged in to the correct registry
- Ensure the repository name matches your GitHub repository

### Build Failures
- Check that Docker is running
- Verify you have sufficient disk space
- Check the Dockerfile for any syntax errors

### Generating Lock File Manually

To generate a new pip.lock file with exact package versions:

```bash
cd tools/docker
./generate-lock.sh
```

This approach solves the chicken-and-egg problem by making lock file generation optional and explicit.
