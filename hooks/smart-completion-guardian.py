#!/usr/bin/env python3
"""
ABOUTME: Smart Completion Guardian - Blocks completion until all tests pass
ABOUTME: Provides detailed fix instructions for Claude to quickly resolve issues
"""

import json
import sys
import subprocess
from pathlib import Path
import re

class SmartCompletionGuardian:
    def __init__(self):
        self.betty_dir = Path('/home/jarvis/projects/Betty')
        self.completion_patterns = [
            'all done', 'complete', 'finished', 'ready', 
            'all set', "that's it", 'task complete'
        ]
        
    def should_check(self, tool_input):
        """Check if this might be a completion attempt"""
        if tool_input.get('tool_name') != 'Bash':
            return False
            
        command = tool_input.get('tool_input', {}).get('command', '').lower()
        
        # Check for completion patterns in echo/print commands
        if 'echo' in command or 'print' in command:
            for pattern in self.completion_patterns:
                if pattern in command.lower():
                    return True
        
        return False
    
    def run_checks(self):
        """Run all quality checks and return issues"""
        issues = []
        
        # 1. Check for syntax errors in JavaScript/TypeScript
        js_check = self.check_javascript()
        if js_check['errors']:
            issues.extend(js_check['errors'])
        
        # 2. Check for Python syntax/imports
        py_check = self.check_python()
        if py_check['errors']:
            issues.extend(py_check['errors'])
        
        # 3. Check for Docker/YAML issues
        docker_check = self.check_docker()
        if docker_check['errors']:
            issues.extend(docker_check['errors'])
        
        # 4. Run quick lint check
        lint_check = self.check_linting()
        if lint_check['errors']:
            issues.extend(lint_check['errors'])
        
        # 5. Check for uncommitted changes
        git_check = self.check_git_status()
        if git_check['warnings']:
            issues.extend(git_check['warnings'])
        
        return issues
    
    def check_javascript(self):
        """Quick JavaScript/TypeScript checks"""
        errors = []
        
        # Check if package.json exists
        package_json = self.betty_dir / 'package.json'
        if package_json.exists():
            # Try to run type check
            result = subprocess.run(
                'npm run type-check 2>&1 || npx tsc --noEmit 2>&1 || true',
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=self.betty_dir
            )
            
            if result.stdout or result.stderr:
                output = result.stdout + result.stderr
                # Parse TypeScript errors
                ts_errors = re.findall(r'(.+?)\((\d+),(\d+)\): error TS\d+: (.+)', output)
                for file_path, line, col, message in ts_errors[:5]:  # Limit to 5
                    errors.append({
                        'type': 'typescript',
                        'file': file_path,
                        'line': line,
                        'column': col,
                        'message': message,
                        'fix_hint': f"Edit {file_path}:{line} to fix: {message}"
                    })
        
        return {'errors': errors}
    
    def check_python(self):
        """Quick Python checks"""
        errors = []
        
        # Find Python files modified recently
        py_files = []
        try:
            result = subprocess.run(
                'find . -name "*.py" -mmin -10 2>/dev/null | head -5',
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.betty_dir
            )
            py_files = result.stdout.strip().split('\n') if result.stdout else []
        except:
            pass
        
        for py_file in py_files:
            if py_file:
                # Quick syntax check
                result = subprocess.run(
                    f'python3 -m py_compile {py_file} 2>&1',
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=self.betty_dir
                )
                
                if result.stderr:
                    # Parse error
                    match = re.search(r'File "(.+?)", line (\d+)', result.stderr)
                    if match:
                        errors.append({
                            'type': 'python_syntax',
                            'file': match.group(1),
                            'line': match.group(2),
                            'message': result.stderr.split('\n')[0],
                            'fix_hint': f"Fix Python syntax at {match.group(1)}:{match.group(2)}"
                        })
        
        return {'errors': errors}
    
    def check_docker(self):
        """Quick Docker/docker-compose checks"""
        errors = []
        
        docker_compose = self.betty_dir / 'docker-compose.yml'
        if docker_compose.exists():
            # Validate docker-compose
            result = subprocess.run(
                'docker-compose config -q 2>&1',
                shell=True,
                capture_output=True,
                text=True,
                timeout=5,
                cwd=self.betty_dir
            )
            
            if result.returncode != 0:
                errors.append({
                    'type': 'docker_compose',
                    'file': 'docker-compose.yml',
                    'message': result.stderr or result.stdout,
                    'fix_hint': 'Fix docker-compose.yml syntax - check YAML formatting'
                })
        
        return {'errors': errors}
    
    def check_linting(self):
        """Quick linting check"""
        errors = []
        
        # Check for ESLint
        if (self.betty_dir / 'package.json').exists():
            result = subprocess.run(
                'npm run lint 2>&1 | head -20',
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=self.betty_dir
            )
            
            if 'error' in result.stdout.lower():
                # Parse first few errors
                lint_errors = re.findall(r'(.+?):(\d+):(\d+)\s+error\s+(.+)', result.stdout)
                for file_path, line, col, message in lint_errors[:3]:
                    errors.append({
                        'type': 'lint',
                        'file': file_path,
                        'line': line,
                        'column': col,
                        'message': message,
                        'fix_hint': f"Run 'npm run lint -- --fix' or edit {file_path}:{line}"
                    })
        
        return {'errors': errors}
    
    def check_git_status(self):
        """Check for uncommitted changes"""
        warnings = []
        
        result = subprocess.run(
            'git status --porcelain',
            shell=True,
            capture_output=True,
            text=True,
            cwd=self.betty_dir
        )
        
        if result.stdout:
            modified_files = len(result.stdout.strip().split('\n'))
            if modified_files > 10:
                warnings.append({
                    'type': 'git_warning',
                    'message': f'{modified_files} files have uncommitted changes',
                    'fix_hint': 'Consider committing changes before marking complete'
                })
        
        return {'warnings': warnings}
    
    def format_block_message(self, issues):
        """Format issues into helpful block message"""
        
        if not issues:
            return None
        
        message = "🛑 Cannot mark complete - found {} issue(s):\n\n".format(len(issues))
        
        # Group by type
        by_type = {}
        for issue in issues:
            issue_type = issue.get('type', 'unknown')
            if issue_type not in by_type:
                by_type[issue_type] = []
            by_type[issue_type].append(issue)
        
        # Format each type
        for issue_type, type_issues in by_type.items():
            if issue_type == 'typescript':
                message += "📘 TypeScript Errors:\n"
            elif issue_type == 'python_syntax':
                message += "🐍 Python Syntax Errors:\n"
            elif issue_type == 'lint':
                message += "🧹 Linting Errors:\n"
            elif issue_type == 'docker_compose':
                message += "🐳 Docker Configuration:\n"
            elif issue_type == 'git_warning':
                message += "⚠️ Git Warnings:\n"
            else:
                message += "❗ Other Issues:\n"
            
            for issue in type_issues[:3]:  # Limit to 3 per type
                if 'file' in issue and 'line' in issue:
                    message += f"  • {issue['file']}:{issue['line']} - {issue.get('message', 'error')[:50]}\n"
                else:
                    message += f"  • {issue.get('message', 'error')[:80]}\n"
                
                if 'fix_hint' in issue:
                    message += f"    → {issue['fix_hint']}\n"
            
            message += "\n"
        
        message += "💡 To fix: Address the issues above, then try completing again.\n"
        message += "   Quick fix: Say 'fix the completion issues' and I'll address them."
        
        return message
    
    def check_completion(self):
        """Main entry point for hook"""
        try:
            # Get tool input from stdin
            tool_input = json.load(sys.stdin)
            
            # Check if this is a completion attempt
            if not self.should_check(tool_input):
                # Not a completion, allow it
                return 0
            
            print("🔍 Betty: Checking if ready for completion...", file=sys.stderr)
            
            # Run all checks
            issues = self.run_checks()
            
            if issues:
                # Block completion and provide guidance
                block_message = self.format_block_message(issues)
                
                # Output the block action
                print(json.dumps({
                    "action": "block",
                    "message": block_message
                }))
                
                # Log to file for learning
                from datetime import datetime
                with open('/home/jarvis/projects/Betty/completion-blocks.jsonl', 'a') as f:
                    f.write(json.dumps({
                        'timestamp': datetime.now().isoformat(),
                        'issues': issues,
                        'blocked': True
                    }) + '\n')
                
                print(f"❌ Betty: Blocked completion - {len(issues)} issues found", file=sys.stderr)
            else:
                # All checks passed
                print("✅ Betty: All checks passed - completion allowed", file=sys.stderr)
                
                # Log success
                from datetime import datetime
                with open('/home/jarvis/projects/Betty/completion-blocks.jsonl', 'a') as f:
                    f.write(json.dumps({
                        'timestamp': datetime.now().isoformat(),
                        'issues': [],
                        'blocked': False
                    }) + '\n')
            
        except Exception as e:
            print(f"Completion guardian error: {e}", file=sys.stderr)
            # On error, allow completion (fail open)
            
        return 0

if __name__ == '__main__':
    guardian = SmartCompletionGuardian()
    sys.exit(guardian.check_completion())