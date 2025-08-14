# Contributing to Claude Code Kompendium

Thank you for your interest in contributing! We welcome all contributions that improve the Claude Code experience.

## How to Contribute

### 1. Fork and Clone
```bash
git clone https://github.com/YOUR-USERNAME/claude-kompendium.git
cd claude-kompendium
```

### 2. Create a Branch
```bash
git checkout -b feature/your-feature-name
```

### 3. Make Your Changes
- Add new hooks to `hooks/`
- Update documentation
- Add tests if applicable
- Follow existing code style

### 4. Test Your Changes
```bash
# Test your hook manually
echo '{"tool_name":"Bash","tool_input":{"command":"test"}}' | python3 hooks/your-hook.py

# Run any existing tests
python3 -m pytest tests/
```

### 5. Submit Pull Request
- Clear description of changes
- Examples of usage
- Any breaking changes noted

## Hook Contribution Guidelines

### Structure
```python
#!/usr/bin/env python3
"""
Brief description of what the hook does
When it triggers and why it's useful
"""

import json
import sys

class YourHookName:
    def __init__(self):
        # Initialization
        pass
    
    def process(self):
        # Main logic
        hook_data = json.load(sys.stdin)
        
        # Process and potentially block
        if should_block:
            print(json.dumps({
                "action": "block",
                "message": "Helpful message"
            }))
        
        return 0

if __name__ == '__main__':
    hook = YourHookName()
    sys.exit(hook.process())
```

### Documentation
Each hook should include:
- Clear docstring
- Usage example
- Configuration snippet
- Expected behavior

## Ideas for Contributions

### High Priority
- 🔒 Security vulnerability scanner
- 📊 Performance profiler
- 🔄 Dependency updater
- 📈 Code complexity analyzer

### Nice to Have
- 🎨 Code formatter integration
- 📝 Commit message generator
- 🌍 i18n checker
- 🧪 Coverage reporter

## Code Style

- Python 3.8+ compatible
- Clear variable names
- Comments for complex logic
- Error handling with graceful failures

## Testing

- Test with various inputs
- Handle edge cases
- Fail gracefully (don't break Claude)
- Include test files in `tests/`

## Documentation

Update relevant docs:
- README.md for major features
- docs/ for detailed guides
- Examples in examples/

## Questions?

Open an issue for:
- Feature discussions
- Implementation questions
- Bug reports

## License

By contributing, you agree that your contributions will be licensed under the MIT License.