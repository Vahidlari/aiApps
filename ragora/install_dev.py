#!/usr/bin/env python3
"""Development installation script for the knowledge base manager package.

This script installs the package in development mode (-e) which is perfect
for development containers and local development.
"""

import os
import subprocess
import sys


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(
            cmd, shell=True, check=True, capture_output=True, text=True
        )
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"   Error: {e.stderr.strip()}")
        return False


def main():
    """Main installation process."""
    print("🚀 Installing Knowledge Base Manager Package in Development Mode")
    print("=" * 60)

    # Check if we're in the right directory
    if not os.path.exists("ragora"):
        print("❌ Error: ragora directory not found")
        print("   Please run this script from the ragora directory")
        sys.exit(1)

    # Install in editable mode
    success = run_command("pip install -e .", "Installing package in editable mode")

    if not success:
        print("❌ Installation failed")
        sys.exit(1)

    # Install development dependencies
    if os.path.exists("requirements-dev.txt"):
        success = run_command(
            "pip install -r requirements-dev.txt", "Installing development dependencies"
        )

        if not success:
            print(
                "⚠️  Development dependencies installation failed, but core package is installed"
            )

    print("\n" + "=" * 60)
    print("✅ Installation completed successfully!")
    print("\n📋 Next steps:")
    print(
        "   1. Start Weaviate: docker run -d --name weaviate -p 8080:8080 semitechnologies/weaviate:1.22.4"
    )
    print(
        "   2. Test the installation: python -c 'from ragora import KnowledgeBaseManager; print(\"✅ Package imported successfully\")'"
    )
    print("   3. Run examples: python ragora/examples/basic_usage.py")
    print("   4. Use CLI: kbm status")
    print("\n🎯 Package is now installed in editable mode!")
    print("   Any changes to the source code will be immediately available.")


if __name__ == "__main__":
    main()
