#!/bin/bash

# Claude Code Kompendium - Python Project Installer

set -e

echo "🐍 Installing Claude Code Kompendium for Python..."

# Set project type for main installer
export PROJECT_TYPE="python"

# Run main installer
./install.sh

# Additional Python-specific setup
echo ""
echo "📦 Python-specific configuration:"
echo "  ✓ Syntax checking with py_compile"
echo "  ✓ pytest integration active"
echo "  ✓ ruff/flake8 linting enabled"
echo "  ✓ mypy type checking available"
echo ""
echo "💡 Recommended tools:"
echo "  pip install pytest ruff mypy black"