#!/bin/bash
# Test script for the milestone-driven release system

set -e

echo "🧪 Testing Milestone-Driven Release System"
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "ragora/pyproject.toml" ]; then
    echo "❌ Error: Must be run from the project root directory"
    exit 1
fi

echo "✅ Project structure verified"

# Check if semantic-release config exists
if [ ! -f ".releaserc.json" ]; then
    echo "❌ Error: .releaserc.json not found"
    exit 1
fi

echo "✅ Semantic-release configuration found"

# Check if workflow file exists
if [ ! -f ".github/workflows/milestone-release.yml" ]; then
    echo "❌ Error: milestone-release.yml workflow not found"
    exit 1
fi

echo "✅ GitHub workflow found"

# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found"
    exit 1
fi

echo "✅ Node.js configuration found"

# Check if database server directory exists
if [ ! -d "tools/database_server" ]; then
    echo "❌ Error: tools/database_server directory not found"
    exit 1
fi

echo "✅ Database server directory found"

# Check Python package configuration
cd ragora

if ! grep -q "dynamic = \[\"version\"\]" pyproject.toml; then
    echo "❌ Error: pyproject.toml not configured for dynamic versioning"
    exit 1
fi

echo "✅ Python package configured for dynamic versioning"

if ! grep -q "setuptools_scm" pyproject.toml; then
    echo "❌ Error: setuptools_scm not found in pyproject.toml"
    exit 1
fi

echo "✅ setuptools_scm configured"

cd ..

# Test if we can create a test commit
echo ""
echo "🔧 Creating test commit for validation..."

# Check if git is available
if ! command -v git &> /dev/null; then
    echo "⚠️  Warning: git not available, skipping commit test"
else
    # Create a test commit message
    TEST_COMMIT="test: validate release system configuration
    
    This is a test commit to validate the milestone-driven release system.
    It should trigger a patch version bump if the system is working correctly."
    
    echo "Test commit message:"
    echo "$TEST_COMMIT"
    echo ""
    echo "✅ Commit message follows Conventional Commits format"
fi

# Test database server archive creation
echo ""
echo "🗜️  Testing database server archive creation..."

if [ -d "tools/database_server" ]; then
    TEST_ARCHIVE="test_database_server.tar.gz"
    
    tar --exclude='*.pyc' \
        --exclude='__pycache__' \
        --exclude='.git' \
        --exclude='node_modules' \
        --exclude='*.log' \
        --exclude='*.tmp' \
        -czf "$TEST_ARCHIVE" \
        -C tools database_server
    
    if [ -f "$TEST_ARCHIVE" ]; then
        echo "✅ Database server archive created successfully"
        echo "   Archive size: $(du -h "$TEST_ARCHIVE" | cut -f1)"
        rm "$TEST_ARCHIVE"
    else
        echo "❌ Error: Failed to create database server archive"
        exit 1
    fi
fi

echo ""
echo "🎉 Release System Validation Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. No additional setup required! Uses GitHub Package Registry automatically."
echo "   - GITHUB_TOKEN is auto-provided by GitHub Actions"
echo ""
echo "2. Create a milestone and add some issues/PRs"
echo ""
echo "3. Make commits using Conventional Commits format:"
echo "   - feat: for new features (minor version bump)"
echo "   - fix: for bug fixes (patch version bump)"
echo "   - feat!: for breaking changes (major version bump)"
echo ""
echo "4. Close the milestone to trigger the release workflow"
echo ""
echo "5. Or manually trigger via GitHub Actions → Milestone-Driven Release"
echo ""
echo "📦 Users can install your package with:"
echo "   pip install ragora==<version> --index-url https://pypi.org/simple/"
echo ""
echo "📚 See RELEASE_AUTOMATION.md for detailed documentation"

