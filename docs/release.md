# Release Process Guide

This guide explains how to use the milestone-driven release system for the Ragora project. The system automatically handles versioning, package publishing, and release management based on your commit messages.

## 🎯 Overview

The release system works by:
1. **Analyzing your commits** using conventional commit format
2. **Determining version bumps** automatically
3. **Triggering releases** when you close a milestone
4. **Publishing packages** to GitHub Package Registry and PyPI

## 📝 How to Write Commit Messages

### Understanding Conventional Commits

Your commit messages should follow this format:
```
type(scope): description

[optional body]

[optional footer(s)]
```

### Commit Types and Their Impact

| Type | Version Bump | When to Use | Example |
|------|-------------|-------------|---------|
| `feat:` | **Minor** (0.1.0 → 0.2.0) | New features for users | `feat: add user authentication` |
| `fix:` | **Patch** (0.1.0 → 0.1.1) | Bug fixes | `fix: resolve login timeout issue` |
| `perf:` | **Patch** | Performance improvements | `perf: optimize database queries` |
| `refactor:` | **Patch** | Code restructuring | `refactor: simplify API endpoints` |
| `style:` | **Patch** | Code formatting, no logic changes | `style: format code with black` |
| `docs:` | **Patch** | Documentation updates | `docs: update API documentation` |
| `test:` | **Patch** | Adding or updating tests | `test: add unit tests for auth module` |
| `build:` | **Patch** | Build system changes | `build: update webpack configuration` |
| `ci:` | **Patch** | CI/CD pipeline changes | `ci: add automated testing workflow` |
| `chore:` | **Patch** | Maintenance tasks | `chore: update dependencies` |

### Breaking Changes (Major Version Bump)

For breaking changes that require a **major version bump** (0.1.0 → 1.0.0), use one of these formats:

```bash
# Option 1: Use exclamation mark
git commit -m "feat!: redesign user API"

# Option 2: Use BREAKING CHANGE footer
git commit -m "feat: add new authentication system

BREAKING CHANGE: All API endpoints now require v2 authentication"
```

### Good vs. Bad Examples

✅ **Good commit messages:**
```bash
feat: add email notification system
fix: resolve memory leak in data processor
docs: update installation instructions
perf: optimize vector search algorithm
feat!: redesign API endpoints

BREAKING CHANGE: Removed deprecated endpoints
```

❌ **Bad commit messages:**
```bash
fixed bug
updated stuff
changes
WIP
more work
```

## 🚀 How to Trigger Releases

### Method 1: Automatic Release (Recommended)

1. **Create a milestone** on GitHub:
   - Go to Issues → Milestones
   - Create a new milestone (e.g., "v1.2.0")
   - Add relevant issues and PRs to the milestone

2. **Make your commits** using conventional commit format:
   ```bash
   git add .
   git commit -m "feat: add new feature"
   git push
   ```

3. **Close the milestone**:
   - Go to the milestone page
   - Click "Close milestone"
   - The release will trigger automatically

### Method 2: Manual Release

1. Go to **Actions** → **Milestone-Driven Release**
2. Click **Run workflow**
3. Optionally specify a milestone title
4. Click **Run workflow**

### Method 3: Dry Run (Testing Mode)

For testing the release workflow without actually publishing to PyPI:

1. Go to **Actions** → **Milestone-Driven Release**
2. Click **Run workflow**
3. **Check the "Dry run mode" checkbox**
4. Optionally specify a milestone title
5. Click **Run workflow**

**What happens in dry run mode:**
- ✅ Creates a GitHub release with all assets
- ✅ Builds Python packages (wheel + source distribution)
- ✅ Creates database server archives (tar.gz and zip)
- ✅ Attaches all files to the GitHub release
- ❌ **SKIPS** publishing to PyPI (safe for testing!)

**Use dry run when:**
- Testing changes to the release workflow
- Verifying package builds correctly
- Checking release notes formatting
- Training team members on the release process

> **Note:** Dry run mode creates a real GitHub release. If you want to test without creating any release, use a test repository instead.

## 🔍 What Happens During a Release

### Step 1: Commit Analysis
The system checks commits since the last tag for:
- Conventional commit format
- Breaking changes
- Feature additions
- Bug fixes

### Step 2: Version Determination
Based on your commits, it determines the new version:
- `feat:` → Minor version bump
- `fix:` → Patch version bump  
- `BREAKING CHANGE` → Major version bump

### Step 3: Release Creation
The system automatically:
- Creates a Git tag (e.g., `v1.2.3`)
- Builds Python packages (wheel + source)
- Creates GitHub release with notes
- Publishes to GitHub Package Registry
- Publishes to PyPI (if configured)
- Creates database server archive
- Attaches milestone summary

### Step 4: What Gets Published

Each release publishes the following artifacts:

1. **Git tag**: `v1.2.3`
2. **GitHub Release**: With auto-generated notes and release assets
3. **Python Package** (Ragora):
   - Published to PyPI (`pip install ragora`)
   - Attached to GitHub release as `.whl` and `.tar.gz` files
4. **Database Server Package**:
   - `ragora-database-server.tar.gz` - Complete database server setup
   - `ragora-database-server.zip` - Windows-friendly format
   - Users download this to deploy Weaviate locally
5. **Installation instructions**: Added to release notes

## 📦 Installing Released Packages

After a release, users can install Ragora and set up the database:

### 1. Install Ragora Package

**From PyPI (Recommended):**
```bash
# Install latest version
pip install ragora

# Install specific version
pip install ragora==1.2.3
```

**From GitHub Releases:**
```bash
# Install wheel directly
pip install https://github.com/vahidlari/aiapps/releases/download/v1.2.3/ragora-1.2.3-py3-none-any.whl
```

### 2. Download Database Server

Download the pre-configured database server from the release:

```bash
# Download from GitHub releases
wget https://github.com/vahidlari/aiapps/releases/download/v1.2.3/ragora-database-server.tar.gz

# Extract and run
tar -xzf ragora-database-server.tar.gz
cd ragora-database-server
./database-manager.sh start
```

**Windows users:** Download `ragora-database-server.zip` instead and extract using Windows tools.

## 🔧 Troubleshooting

### No Release Created?

Check these common issues:

1. **Commit format**: Ensure commits follow conventional format
   ```bash
   # Check recent commits
   git log --oneline -5
   ```

2. **Milestone status**: Verify the milestone is closed
3. **Workflow logs**: Check Actions tab for error details

### Wrong Version Bump?

- `feat:` commits should trigger minor version bumps
- `fix:` commits should trigger patch version bumps
- `BREAKING CHANGE` should trigger major version bumps

### Release Failed?

1. Check GitHub Actions logs for specific errors
2. Verify you have push permissions to the repository
3. Ensure no conflicting tags exist
4. Check PyPI credentials are configured correctly

## 💡 Best Practices

### Commit Message Tips
- Be descriptive but concise
- Use present tense ("add feature" not "added feature")
- Include scope when helpful: `feat(auth): add OAuth support`
- Reference issues when relevant: `fix: resolve login bug (#123)`

### Release Planning
- Group related changes into milestones
- Test thoroughly before closing milestones
- Use meaningful milestone names (e.g., "v1.2.0 - User Management")
- Keep milestones focused on single themes

### Version Strategy
- Use semantic versioning for API compatibility
- Reserve major versions for breaking changes
- Use minor versions for new features
- Use patch versions for bug fixes

## 📚 Quick Reference

### Commit Types Quick Guide
```bash
# New feature (minor version)
git commit -m "feat: add user dashboard"

# Bug fix (patch version)
git commit -m "fix: resolve authentication bug"

# Breaking change (major version)
git commit -m "feat!: redesign API"

# Documentation update (patch version)
git commit -m "docs: update installation guide"

# Performance improvement (patch version)
git commit -m "perf: optimize database queries"
```

### Release Workflow
1. Write conventional commits
2. Create and assign milestone
3. Close milestone → Automatic release
4. Check GitHub Releases for new version
5. Verify package on PyPI

**Testing the release workflow:**
- Use **dry run mode** to test without publishing to PyPI
- All assets are created, but PyPI publishing is skipped

## 🆘 Getting Help

- **Workflow logs**: Check Actions tab for detailed error messages
- **Conventional Commits**: [Official specification](https://www.conventionalcommits.org/)
- **Semantic Versioning**: [SemVer guide](https://semver.org/)
- **GitHub Issues**: Create an issue for bugs or questions

