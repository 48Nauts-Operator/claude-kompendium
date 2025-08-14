#!/bin/bash

# Claude Code Kompendium - JavaScript/TypeScript Project Installer

set -e

echo "🚀 Installing Claude Code Kompendium for JavaScript/TypeScript..."

# Set project type for main installer
export PROJECT_TYPE="javascript"

# Run main installer
./install.sh

# Additional JS-specific setup
echo ""
echo "📦 JavaScript-specific configuration:"
echo "  ✓ TypeScript checking enabled"
echo "  ✓ ESLint integration active"
echo "  ✓ npm test will be run before completion"
echo ""
echo "💡 Make sure you have these in package.json:"
echo '  "scripts": {'
echo '    "lint": "eslint .",'
echo '    "type-check": "tsc --noEmit",'
echo '    "test": "jest"'
echo '  }'