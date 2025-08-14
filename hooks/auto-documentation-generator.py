#!/usr/bin/env python3
"""
ABOUTME: Betty Auto-Documentation Generator - Creates comprehensive docs for new features
ABOUTME: Triggers on significant code changes and generates structured documentation
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path
import hashlib
import re

class BettyDocumentationGenerator:
    def __init__(self):
        self.betty_dir = Path('/home/jarvis/projects/Betty')
        self.docs_dir = self.betty_dir / 'docs' / 'auto-generated'
        self.features_dir = self.docs_dir / 'features'
        self.reports_dir = self.docs_dir / 'reports'
        
        # Create directories
        self.features_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Thresholds for triggering documentation
        self.thresholds = {
            'files_changed': 3,      # Document if 3+ files changed
            'lines_added': 50,       # Document if 50+ lines added
            'new_functions': 2,      # Document if 2+ new functions
            'new_api_endpoint': 1,   # Always document new API endpoints
            'new_component': 1,      # Always document new components
        }
        
    def analyze_session(self):
        """Main entry point - analyzes session for documentation needs"""
        try:
            # Get session data from stdin
            hook_data = json.load(sys.stdin)
            
            # Extract session information
            session_id = hook_data.get('session_id', '')
            tools_used = hook_data.get('tools_used', [])
            duration = hook_data.get('duration', 0)
            original_prompt = hook_data.get('original_prompt', '')
            
            # Analyze what was built/changed
            changes = self.analyze_changes(tools_used)
            
            # Determine if documentation is needed
            if self.needs_documentation(changes):
                # Generate feature documentation
                doc_path = self.generate_feature_documentation(
                    original_prompt, 
                    changes, 
                    tools_used,
                    duration
                )
                
                print(f"📝 Betty: Generated feature documentation at {doc_path}", file=sys.stderr)
                
                # Send notification
                self.notify_documentation_created(doc_path, changes)
                
            # Always check for learning report needs
            if self.needs_learning_report(tools_used):
                report_path = self.generate_learning_report(tools_used, duration)
                print(f"📊 Betty: Generated learning report at {report_path}", file=sys.stderr)
                
        except Exception as e:
            print(f"Documentation generator error: {e}", file=sys.stderr)
            
        return 0
    
    def analyze_changes(self, tools_used):
        """Analyze what changed during the session"""
        changes = {
            'files_created': [],
            'files_modified': [],
            'files_deleted': [],
            'functions_added': [],
            'api_endpoints': [],
            'components': [],
            'tests_added': [],
            'configs_changed': [],
            'total_lines_added': 0,
            'total_lines_removed': 0,
            'languages': set(),
            'patterns_used': [],
        }
        
        for tool in tools_used:
            tool_name = tool.get('name', '')
            params = tool.get('params', {})
            
            # Track file operations
            if tool_name == 'Write':
                file_path = params.get('file_path', '')
                changes['files_created'].append(file_path)
                self.analyze_file_content(file_path, params.get('content', ''), changes)
                
            elif tool_name in ['Edit', 'MultiEdit']:
                file_path = params.get('file_path', '')
                if file_path not in changes['files_modified']:
                    changes['files_modified'].append(file_path)
                    
            elif tool_name == 'Bash':
                command = params.get('command', '')
                if 'rm' in command:
                    # Try to extract deleted files
                    self.extract_deleted_files(command, changes)
                elif 'npm install' in command or 'pip install' in command:
                    changes['configs_changed'].append('dependencies')
                    
        # Deduplicate and clean
        changes['languages'] = list(changes['languages'])
        changes['files_modified'] = [f for f in changes['files_modified'] 
                                    if f not in changes['files_created']]
        
        return changes
    
    def analyze_file_content(self, file_path, content, changes):
        """Analyze content of created/modified files"""
        
        # Detect language
        ext = Path(file_path).suffix
        language_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.jsx': 'React',
            '.tsx': 'React TypeScript',
            '.md': 'Markdown',
            '.json': 'JSON',
            '.yml': 'YAML',
            '.yaml': 'YAML',
            '.sh': 'Shell',
        }
        
        if ext in language_map:
            changes['languages'].add(language_map[ext])
        
        # Count lines
        lines = content.split('\n')
        changes['total_lines_added'] += len(lines)
        
        # Detect functions/classes
        if ext in ['.py', '.js', '.ts']:
            functions = self.extract_functions(content, ext)
            changes['functions_added'].extend(functions)
        
        # Detect API endpoints
        if 'router' in content.lower() or '@app' in content:
            endpoints = self.extract_api_endpoints(content)
            changes['api_endpoints'].extend(endpoints)
        
        # Detect React components
        if ext in ['.jsx', '.tsx'] or 'React' in content:
            components = self.extract_components(content)
            changes['components'].extend(components)
        
        # Detect tests
        if 'test' in file_path.lower() or 'spec' in file_path.lower():
            changes['tests_added'].append(file_path)
    
    def extract_functions(self, content, ext):
        """Extract function names from code"""
        functions = []
        
        if ext == '.py':
            # Python functions
            pattern = r'def\s+(\w+)\s*\('
            functions = re.findall(pattern, content)
        elif ext in ['.js', '.ts']:
            # JavaScript/TypeScript functions
            patterns = [
                r'function\s+(\w+)\s*\(',
                r'const\s+(\w+)\s*=\s*\([^)]*\)\s*=>',
                r'const\s+(\w+)\s*=\s*async\s*\([^)]*\)\s*=>',
            ]
            for pattern in patterns:
                functions.extend(re.findall(pattern, content))
        
        return functions
    
    def extract_api_endpoints(self, content):
        """Extract API endpoints from code"""
        endpoints = []
        
        # Express/FastAPI patterns
        patterns = [
            r'router\.(get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]',
            r'@app\.(get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]',
            r'@router\.(get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, tuple):
                    endpoints.append(f"{match[0].upper()} {match[1]}")
                else:
                    endpoints.append(match)
        
        return endpoints
    
    def extract_components(self, content):
        """Extract React component names"""
        components = []
        
        # React component patterns
        patterns = [
            r'function\s+([A-Z]\w+)\s*\(',
            r'const\s+([A-Z]\w+)\s*=',
            r'class\s+([A-Z]\w+)\s+extends\s+',
            r'export\s+default\s+(?:function\s+)?([A-Z]\w+)',
        ]
        
        for pattern in patterns:
            components.extend(re.findall(pattern, content))
        
        return list(set(components))  # Deduplicate
    
    def needs_documentation(self, changes):
        """Determine if changes warrant documentation"""
        
        # Always document new API endpoints
        if changes['api_endpoints']:
            return True
        
        # Always document new components
        if changes['components']:
            return True
        
        # Check thresholds
        if len(changes['files_created']) + len(changes['files_modified']) >= self.thresholds['files_changed']:
            return True
        
        if changes['total_lines_added'] >= self.thresholds['lines_added']:
            return True
        
        if len(changes['functions_added']) >= self.thresholds['new_functions']:
            return True
        
        # Document if tests were added (good practice)
        if changes['tests_added']:
            return True
        
        return False
    
    def generate_feature_documentation(self, prompt, changes, tools_used, duration):
        """Generate comprehensive feature documentation"""
        
        # Create feature name from prompt
        feature_name = self.extract_feature_name(prompt)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{feature_name}_{timestamp}.md"
        doc_path = self.features_dir / filename
        
        # Generate documentation content
        content = f"""# Feature Documentation: {feature_name.replace('_', ' ').title()}

## Overview
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Session Duration**: {duration / 60000:.1f} minutes
**Original Request**: {prompt[:500]}

## What Was Built

### Files Changed
**Created**: {len(changes['files_created'])} files
**Modified**: {len(changes['files_modified'])} files
**Total Lines Added**: {changes['total_lines_added']}

### Components Added
"""
        
        # List new components
        if changes['components']:
            content += f"**React Components** ({len(changes['components'])}):\n"
            for component in changes['components']:
                content += f"- `{component}`\n"
            content += "\n"
        
        # List new functions
        if changes['functions_added']:
            content += f"**Functions** ({len(changes['functions_added'])}):\n"
            for func in changes['functions_added'][:20]:  # Limit to 20
                content += f"- `{func}()`\n"
            content += "\n"
        
        # List API endpoints
        if changes['api_endpoints']:
            content += f"**API Endpoints** ({len(changes['api_endpoints'])}):\n"
            for endpoint in changes['api_endpoints']:
                content += f"- `{endpoint}`\n"
            content += "\n"
        
        # File details
        content += "## Files Created\n"
        for file_path in changes['files_created'][:20]:  # Limit to 20
            content += f"- `{file_path}`\n"
        
        if changes['files_modified']:
            content += "\n## Files Modified\n"
            for file_path in changes['files_modified'][:20]:
                content += f"- `{file_path}`\n"
        
        # Tests
        if changes['tests_added']:
            content += f"\n## Tests Added\n"
            for test_file in changes['tests_added']:
                content += f"- `{test_file}`\n"
        
        # Languages used
        if changes['languages']:
            content += f"\n## Technologies Used\n"
            for lang in changes['languages']:
                content += f"- {lang}\n"
        
        # Tool usage pattern
        content += f"\n## Development Pattern\n"
        tool_sequence = self.extract_tool_pattern(tools_used)
        content += f"Tool sequence: `{tool_sequence}`\n"
        
        # How to use
        content += """
## Usage

### Prerequisites
- Ensure all dependencies are installed
- Check environment variables are set
- Verify database connections

### Running the Feature
```bash
# Add specific commands here based on the feature
```

### Testing
"""
        if changes['tests_added']:
            content += "Run the tests with:\n```bash\nnpm test\n# or\npytest\n```\n"
        else:
            content += "⚠️ No tests were added for this feature. Consider adding tests.\n"
        
        # Integration notes
        content += """
## Integration Notes

### Dependencies
Check if new dependencies were added to package.json or requirements.txt

### Configuration
Review any configuration changes needed

### Breaking Changes
⚠️ Review modified files for potential breaking changes

## Additional Notes
This documentation was auto-generated by Betty based on the session activity.
For more details, check the individual files or the session logs.

---
*Generated by Betty Documentation System*
"""
        
        # Write documentation
        with open(doc_path, 'w') as f:
            f.write(content)
        
        return doc_path
    
    def extract_feature_name(self, prompt):
        """Extract a feature name from the prompt"""
        
        # Common patterns
        patterns = [
            r'(?:add|create|implement|build)\s+(?:a\s+)?(\w+(?:\s+\w+)?)',
            r'(?:fix|update|refactor)\s+(?:the\s+)?(\w+(?:\s+\w+)?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, prompt.lower())
            if match:
                name = match.group(1).replace(' ', '_')
                return name[:50]  # Limit length
        
        # Fallback: use first few words
        words = prompt.split()[:3]
        return '_'.join(words)[:50]
    
    def extract_tool_pattern(self, tools_used):
        """Extract tool usage pattern"""
        sequence = []
        for tool in tools_used[:10]:  # First 10 tools
            sequence.append(tool.get('name', 'Unknown'))
        
        return ' → '.join(sequence)
    
    def extract_deleted_files(self, command, changes):
        """Try to extract deleted files from rm command"""
        # Simple pattern matching
        if 'rm' in command:
            parts = command.split()
            for part in parts:
                if part.startswith('/') or part.startswith('./'):
                    if part not in ['-rf', '-f', '-r']:
                        changes['files_deleted'].append(part)
    
    def needs_learning_report(self, tools_used):
        """Check if a learning report should be generated"""
        
        # Generate report if:
        # - More than 20 tools were used (complex session)
        # - Errors were encountered and resolved
        # - New patterns were discovered
        
        if len(tools_used) > 20:
            return True
        
        # Check for error resolution patterns
        had_errors = any('error' in str(t).lower() for t in tools_used[:len(tools_used)//2])
        resolved = any('success' in str(t).lower() or 'complete' in str(t).lower() 
                      for t in tools_used[len(tools_used)//2:])
        
        if had_errors and resolved:
            return True
        
        return False
    
    def generate_learning_report(self, tools_used, duration):
        """Generate a learning report"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"learning_report_{timestamp}.md"
        report_path = self.reports_dir / filename
        
        # Analyze patterns
        patterns = self.analyze_patterns(tools_used)
        errors = self.analyze_errors(tools_used)
        
        content = f"""# Betty Learning Report

## Session Summary
**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Duration**: {duration / 60000:.1f} minutes
**Tools Used**: {len(tools_used)}

## Patterns Discovered

### Tool Usage Patterns
"""
        
        for pattern, count in patterns['tool_patterns'].items():
            content += f"- `{pattern}`: {count} occurrences\n"
        
        content += f"""
### Error Resolution Patterns
**Errors Encountered**: {len(errors['errors'])}
**Errors Resolved**: {errors['resolved']}
**Success Rate**: {errors['success_rate']:.1%}

### Common Error Types
"""
        
        for error_type, count in errors['error_types'].items():
            content += f"- {error_type}: {count} occurrences\n"
        
        content += f"""
## Learning Outcomes

### New Capabilities Demonstrated
"""
        
        # Identify new capabilities
        capabilities = self.identify_capabilities(tools_used)
        for cap in capabilities:
            content += f"- {cap}\n"
        
        content += f"""
## Efficiency Metrics

- **Average Tool Execution**: {self.calculate_avg_execution(tools_used):.2f}s
- **Error Recovery Time**: {errors.get('avg_recovery_time', 0):.1f} minutes
- **Pattern Reuse**: {patterns.get('reuse_count', 0)} times

## Recommendations

### Patterns to Remember
"""
        
        for pattern in patterns.get('valuable_patterns', [])[:5]:
            content += f"- {pattern}\n"
        
        content += """
### Areas for Improvement
"""
        
        for improvement in self.suggest_improvements(tools_used, errors):
            content += f"- {improvement}\n"
        
        content += """
---
*This report was auto-generated by Betty's Learning System*
"""
        
        with open(report_path, 'w') as f:
            f.write(content)
        
        return report_path
    
    def analyze_patterns(self, tools_used):
        """Analyze patterns in tool usage"""
        patterns = {
            'tool_patterns': {},
            'valuable_patterns': [],
            'reuse_count': 0
        }
        
        # Find repeated sequences
        for i in range(len(tools_used) - 2):
            sequence = f"{tools_used[i].get('name')}→{tools_used[i+1].get('name')}"
            patterns['tool_patterns'][sequence] = patterns['tool_patterns'].get(sequence, 0) + 1
        
        # Identify valuable patterns (used 3+ times)
        patterns['valuable_patterns'] = [
            p for p, count in patterns['tool_patterns'].items() 
            if count >= 3
        ]
        
        patterns['reuse_count'] = sum(
            count - 1 for count in patterns['tool_patterns'].values() 
            if count > 1
        )
        
        return patterns
    
    def analyze_errors(self, tools_used):
        """Analyze error patterns"""
        errors = {
            'errors': [],
            'resolved': 0,
            'error_types': {},
            'success_rate': 0,
            'avg_recovery_time': 0
        }
        
        for i, tool in enumerate(tools_used):
            if 'error' in str(tool).lower():
                error_type = self.classify_error(tool)
                errors['error_types'][error_type] = errors['error_types'].get(error_type, 0) + 1
                errors['errors'].append((i, error_type))
                
                # Check if resolved
                if self.was_resolved(tools_used[i:min(i+10, len(tools_used))]):
                    errors['resolved'] += 1
        
        if errors['errors']:
            errors['success_rate'] = errors['resolved'] / len(errors['errors'])
        
        return errors
    
    def classify_error(self, tool):
        """Classify error type"""
        error_str = str(tool).lower()
        
        if 'permission' in error_str:
            return 'Permission Error'
        elif 'not found' in error_str:
            return 'Not Found Error'
        elif 'syntax' in error_str:
            return 'Syntax Error'
        elif 'connection' in error_str:
            return 'Connection Error'
        elif 'timeout' in error_str:
            return 'Timeout Error'
        else:
            return 'Other Error'
    
    def was_resolved(self, subsequent_tools):
        """Check if error was resolved in subsequent tools"""
        for tool in subsequent_tools:
            if 'success' in str(tool).lower() or 'complete' in str(tool).lower():
                return True
        return False
    
    def identify_capabilities(self, tools_used):
        """Identify demonstrated capabilities"""
        capabilities = set()
        
        tool_names = [t.get('name') for t in tools_used]
        
        if 'Write' in tool_names:
            capabilities.add('File creation')
        if 'Edit' in tool_names or 'MultiEdit' in tool_names:
            capabilities.add('Code modification')
        if 'Grep' in tool_names:
            capabilities.add('Pattern searching')
        if 'Bash' in tool_names:
            capabilities.add('Command execution')
        
        # Check for specific patterns
        if self.has_test_pattern(tools_used):
            capabilities.add('Test-driven development')
        if self.has_debug_pattern(tools_used):
            capabilities.add('Debugging and error resolution')
        
        return list(capabilities)
    
    def has_test_pattern(self, tools_used):
        """Check if testing pattern was used"""
        for tool in tools_used:
            if tool.get('name') == 'Bash':
                cmd = tool.get('params', {}).get('command', '')
                if 'test' in cmd or 'jest' in cmd or 'pytest' in cmd:
                    return True
        return False
    
    def has_debug_pattern(self, tools_used):
        """Check if debugging pattern was used"""
        # Look for read-edit-test cycle
        for i in range(len(tools_used) - 2):
            if (tools_used[i].get('name') == 'Read' and 
                tools_used[i+1].get('name') in ['Edit', 'MultiEdit'] and
                tools_used[i+2].get('name') == 'Bash'):
                return True
        return False
    
    def calculate_avg_execution(self, tools_used):
        """Calculate average tool execution time"""
        # Simplified - would need actual timing data
        return len(tools_used) * 0.5  # Assume 0.5s per tool
    
    def suggest_improvements(self, tools_used, errors):
        """Suggest improvements based on session"""
        suggestions = []
        
        if errors['errors'] and errors['success_rate'] < 0.5:
            suggestions.append("Low error resolution rate - consider better error handling")
        
        if len(tools_used) > 50:
            suggestions.append("Long session - consider breaking into smaller tasks")
        
        # Check for repeated edits to same file
        file_edits = {}
        for tool in tools_used:
            if tool.get('name') in ['Edit', 'MultiEdit']:
                file_path = tool.get('params', {}).get('file_path')
                if file_path:
                    file_edits[file_path] = file_edits.get(file_path, 0) + 1
        
        for file_path, count in file_edits.items():
            if count > 5:
                suggestions.append(f"File '{Path(file_path).name}' edited {count} times - consider refactoring")
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    def notify_documentation_created(self, doc_path, changes):
        """Send notification about created documentation"""
        try:
            import requests
            
            feature_type = "API" if changes['api_endpoints'] else "Feature"
            files_changed = len(changes['files_created']) + len(changes['files_modified'])
            
            message = f"Documentation generated for new {feature_type}\n"
            message += f"Files changed: {files_changed}\n"
            message += f"Lines added: {changes['total_lines_added']}\n"
            message += f"Location: {doc_path.name}"
            
            requests.post(
                'https://ntfy.da-tech.io/Betty',
                data=message.encode('utf-8'),
                headers={
                    'Title': f'Documentation: New {feature_type}',
                    'Priority': 'low',
                    'Tags': 'docs,feature'
                },
                timeout=2
            )
        except:
            pass

if __name__ == '__main__':
    generator = BettyDocumentationGenerator()
    sys.exit(generator.analyze_session())