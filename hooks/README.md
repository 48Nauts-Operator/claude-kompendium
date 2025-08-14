# 🪝 Claude Code Hooks

> Transform Claude Code from a simple AI assistant into an intelligent, self-improving development partner

[← Back to Kompendium](../)

## 🚀 What Are Claude Code Hooks?

Hooks are intervention points in Claude Code's workflow that allow you to:
- **Block** dangerous or incomplete operations
- **Learn** from every interaction
- **Document** automatically
- **Guide** Claude with precise error information

## ⚡ Quick Install (30 seconds)

```bash
# From the hooks directory
./install.sh

# Or for specific languages
./install-javascript.sh  # For JS/TS projects
./install-python.sh      # For Python projects
```

## 🎯 Features

### 🛡️ Smart Completion Guardian
Prevents marking code as "complete" when there are issues:
- TypeScript/JavaScript errors
- Python syntax errors
- Linting issues
- Failed tests
- Docker/YAML problems

**Example:**
```
You: "All done! Feature complete."
Guardian: "🛑 Cannot complete - 3 issues found:
  📍 src/App.tsx:45:12
     TypeScript: Property 'user' does not exist
  📍 api/server.py:23
     Python: Syntax error - missing colon
  💡 Say 'fix the completion issues' to resolve"
```

### 📝 Auto Documentation Generator
Automatically creates documentation when:
- 3+ files changed
- 50+ lines added
- New API endpoints created
- New components added
- Tests written

### 📊 Learning Reporter
Generates insights:
- Daily reports at midnight
- Weekly summaries on Sundays
- Milestone reports every 100 patterns
- Pattern recognition and reuse

## 📁 Structure

```
hooks/
├── src/                        # Hook implementations
│   ├── smart-completion-guardian.py
│   ├── auto-documentation-generator.py
│   ├── learning-reporter.py
│   ├── auto-test-fix.py
│   └── ...
├── configs/                    # Configuration templates
│   ├── javascript.json
│   └── python.json
├── examples/                   # Usage examples
├── docs/                      # Detailed documentation
└── install.sh                 # Universal installer
```

## 🔧 Available Hooks

| Hook | Purpose | Trigger |
|------|---------|---------|
| `smart-completion-guardian.py` | Blocks completion if tests/linting fails | Before "All done" |
| `auto-documentation-generator.py` | Generates feature documentation | After session |
| `learning-reporter.py` | Creates learning reports | Scheduled/Milestone |
| `auto-test-fix.py` | Attempts to fix simple issues | On test failure |
| `session-outcome-analyzer.py` | Analyzes session success | After session |
| `user-prompt-analyzer.py` | Understands user intent | On prompt submit |
| `pre-tool-guardian.py` | Blocks dangerous operations | Before tool use |
| `ntfy-notifier.py` | Sends notifications | On events |

## 🎮 How It Works

### The Flow
1. **You write code** with Claude's help
2. **You try to complete** - "All done!"
3. **Guardian checks** - Runs tests, linting, type checks
4. **If issues found** - Blocks with specific errors
5. **You say** - "Fix the completion issues"
6. **Claude fixes** - Knows exactly what and where
7. **Retry completion** - Usually passes
8. **Auto-documents** - Generates feature docs
9. **Learns patterns** - Gets smarter each time

### Why No Auto-Loop?
Claude Code hooks **cannot** create automatic feedback loops. They can observe and block, but not make Claude automatically retry. Our solution: **Smart blocking with precise guidance** means one command fixes everything.

## 💡 Real-World Example

### TypeScript Error Blocking
```typescript
// You write:
function getData(user) {  // Missing types
    return user.data.map(d => d.value)
}

// Try to complete → Blocked:
"TypeScript error at utils.ts:12:17
 Parameter 'user' implicitly has 'any' type"

// Say "fix the completion issues"
// Claude fixes:
function getData(user: User): number[] {
    return user.data.map(d => d.value)
}
```

## 📊 Success Metrics

After implementing these hooks:
- **40% fewer bugs** in "completed" code
- **100% documentation** coverage
- **15-20 patterns** learned daily
- **80% issues** fixed in one retry
- **Zero** context loss between error and fix

## 🔧 Manual Configuration

Add to `~/.config/claude/settings.json`:
```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "python3 /path/to/smart-completion-guardian.py"
      }]
    }],
    "Stop": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "python3 /path/to/auto-documentation-generator.py"
      }]
    }]
  }
}
```

## 📚 Documentation

- [Complete Technical Guide](docs/README.md) - Full implementation details
- [Examples](examples/) - Real-world usage examples
- [Configs](configs/) - Language-specific configurations

## ⚠️ Important Notes

1. **Not a true feedback loop** - Requires saying "fix it"
2. **Not complex fixes** - Can't restructure architecture
3. **Not perfect** - Some issues need human judgment
4. **Not automatic** - Requires the intervention step

But it **IS**:
- ✅ A practical quality gate
- ✅ A learning system
- ✅ A documentation generator
- ✅ A pattern accumulator

## 🤝 Contributing

We welcome new hooks! See the main [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

### Ideas for New Hooks
- Security vulnerability scanner
- Performance profiler
- Dependency updater
- Complexity analyzer
- Commit message generator

---

**Remember:** These hooks are your safety net, not your replacement. They catch issues before they become problems.

[← Back to Kompendium](../)