#!/bin/bash

# Claude Code Kompendium - Universal Installer
# Automatically configures Claude Code with advanced hooks

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOKS_DIR="$SCRIPT_DIR/hooks"
CLAUDE_CONFIG="${HOME}/.config/claude/settings.json"
CLAUDE_CONFIG_DIR="$(dirname "$CLAUDE_CONFIG")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Claude Code Kompendium Installer    ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════╝${NC}"
echo ""

# Check Python installation
echo -e "${YELLOW}▶ Checking requirements...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is required but not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python 3 found${NC}"

# Create config directory if needed
mkdir -p "$CLAUDE_CONFIG_DIR"
echo -e "${GREEN}✅ Config directory ready${NC}"

# Make hooks executable
echo -e "${YELLOW}▶ Preparing hooks...${NC}"
chmod +x "$HOOKS_DIR"/*.py 2>/dev/null || true
echo -e "${GREEN}✅ Hooks prepared${NC}"

# Backup existing configuration
if [ -f "$CLAUDE_CONFIG" ]; then
    BACKUP_FILE="${CLAUDE_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$CLAUDE_CONFIG" "$BACKUP_FILE"
    echo -e "${GREEN}✅ Backed up existing config to: $BACKUP_FILE${NC}"
else
    echo '{"hooks":{}}' > "$CLAUDE_CONFIG"
    echo -e "${GREEN}✅ Created new configuration${NC}"
fi

# Detect project type
echo -e "${YELLOW}▶ Detecting project type...${NC}"
PROJECT_TYPE="universal"

if [ -f "package.json" ]; then
    PROJECT_TYPE="javascript"
    echo -e "${GREEN}✅ Detected: JavaScript/TypeScript project${NC}"
elif [ -f "requirements.txt" ] || [ -f "setup.py" ] || [ -f "pyproject.toml" ]; then
    PROJECT_TYPE="python"
    echo -e "${GREEN}✅ Detected: Python project${NC}"
elif [ -f "docker-compose.yml" ] || [ -f "Dockerfile" ]; then
    PROJECT_TYPE="docker"
    echo -e "${GREEN}✅ Detected: Docker project${NC}"
else
    echo -e "${BLUE}ℹ Using universal configuration${NC}"
fi

# Install hooks based on project type
echo -e "${YELLOW}▶ Installing hooks...${NC}"

# Create Python script to merge configurations
cat > /tmp/merge_claude_config.py << 'EOF'
import json
import sys

config_file = sys.argv[1]
hooks_dir = sys.argv[2]
project_type = sys.argv[3]

# Load existing config
with open(config_file, 'r') as f:
    config = json.load(f)

if 'hooks' not in config:
    config['hooks'] = {}

# Define hooks to install
hooks_to_install = {
    'PreToolUse': [
        {
            'matcher': 'Bash',
            'hooks': [{
                'type': 'command',
                'command': f'python3 {hooks_dir}/smart-completion-guardian.py',
                'description': 'Block completion until quality checks pass'
            }]
        }
    ],
    'Stop': [
        {
            'matcher': '*',
            'hooks': [
                {
                    'type': 'command',
                    'command': f'python3 {hooks_dir}/auto-documentation-generator.py',
                    'description': 'Generate documentation for features'
                },
                {
                    'type': 'command',
                    'command': f'python3 {hooks_dir}/betty-learning-reporter.py',
                    'description': 'Track patterns and generate reports'
                }
            ]
        }
    ]
}

# Merge hooks
for hook_type, hook_configs in hooks_to_install.items():
    if hook_type not in config['hooks']:
        config['hooks'][hook_type] = []
    
    # Add new hooks if not already present
    for new_config in hook_configs:
        exists = False
        for existing in config['hooks'][hook_type]:
            # Check if similar hook exists
            if existing.get('matcher') == new_config.get('matcher'):
                # Merge hooks lists
                if 'hooks' in existing and 'hooks' in new_config:
                    for new_hook in new_config['hooks']:
                        hook_exists = False
                        for eh in existing['hooks']:
                            if 'smart-completion-guardian' in eh.get('command', ''):
                                hook_exists = True
                                break
                        if not hook_exists:
                            existing['hooks'].append(new_hook)
                exists = True
                break
        
        if not exists:
            config['hooks'][hook_type].append(new_config)

# Save merged config
with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)

print(f"Successfully installed {len(hooks_to_install)} hook types")
EOF

python3 /tmp/merge_claude_config.py "$CLAUDE_CONFIG" "$HOOKS_DIR" "$PROJECT_TYPE"
rm /tmp/merge_claude_config.py

echo -e "${GREEN}✅ Hooks installed${NC}"

# Create directories for outputs
echo -e "${YELLOW}▶ Creating output directories...${NC}"
mkdir -p ~/claude-kompendium-output/{docs,reports,patterns,test-results}
echo -e "${GREEN}✅ Output directories created${NC}"

# Test the installation
echo -e "${YELLOW}▶ Testing installation...${NC}"
TEST_RESULT=$(echo '{"tool_name":"Bash","tool_input":{"command":"echo test"}}' | python3 "$HOOKS_DIR/smart-completion-guardian.py" 2>&1 || true)
if echo "$TEST_RESULT" | grep -q "Betty"; then
    echo -e "${GREEN}✅ Installation test passed${NC}"
else
    echo -e "${YELLOW}⚠ Test output unexpected but continuing${NC}"
fi

# Display summary
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        Installation Complete! 🎉         ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Installed Hooks:${NC}"
echo "  📍 Smart Completion Guardian"
echo "     Blocks completion if tests fail"
echo ""
echo "  📝 Auto Documentation Generator"
echo "     Creates docs for significant changes"
echo ""
echo "  📊 Learning Reporter"
echo "     Tracks patterns and generates insights"
echo ""
echo -e "${BLUE}How to Use:${NC}"
echo "  1. Work normally with Claude Code"
echo "  2. When you try 'All done!' it checks quality"
echo "  3. If issues found, say 'fix the completion issues'"
echo "  4. Documentation generated automatically"
echo ""
echo -e "${BLUE}Output Locations:${NC}"
echo "  📁 ~/claude-kompendium-output/docs/"
echo "  📊 ~/claude-kompendium-output/reports/"
echo "  🧠 ~/claude-kompendium-output/patterns/"
echo ""
echo -e "${YELLOW}Pro Tip:${NC} Try introducing an error and marking complete"
echo "         to see the guardian in action!"
echo ""
echo -e "${GREEN}Happy coding with your enhanced Claude! 🚀${NC}"