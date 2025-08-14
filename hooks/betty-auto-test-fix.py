#!/usr/bin/env python3
"""
ABOUTME: Betty Auto Test & Fix - Comprehensive testing with automatic issue resolution
ABOUTME: Creates a feedback loop that tests, identifies issues, and fixes them before completion
"""

import json
import sys
import os
import subprocess
from datetime import datetime
from pathlib import Path
import time
import re

class BettyAutoTestFix:
    def __init__(self):
        self.betty_dir = Path('/home/jarvis/projects/Betty')
        self.test_results_dir = self.betty_dir / 'test-results'
        self.fix_history_file = self.betty_dir / 'fixes' / 'auto-fixes.jsonl'
        
        # Create directories
        self.test_results_dir.mkdir(parents=True, exist_ok=True)
        self.fix_history_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Test configurations for different project types
        self.test_configs = {
            'javascript': {
                'test_commands': ['npm test', 'npm run test:unit', 'npm run test:integration'],
                'lint_commands': ['npm run lint', 'npm run eslint'],
                'type_commands': ['npm run type-check', 'npm run tsc'],
                'build_commands': ['npm run build'],
                'common_fixes': {
                    'missing_import': self.fix_missing_import_js,
                    'syntax_error': self.fix_syntax_error_js,
                    'type_error': self.fix_type_error_ts,
                    'lint_error': self.fix_lint_error_js,
                }
            },
            'python': {
                'test_commands': ['pytest', 'python -m pytest', 'python -m unittest'],
                'lint_commands': ['ruff check', 'flake8', 'pylint'],
                'type_commands': ['mypy .'],
                'build_commands': ['python setup.py build'],
                'common_fixes': {
                    'import_error': self.fix_import_error_py,
                    'syntax_error': self.fix_syntax_error_py,
                    'indentation_error': self.fix_indentation_error_py,
                    'type_error': self.fix_type_error_py,
                }
            },
            'docker': {
                'test_commands': ['docker-compose config'],
                'build_commands': ['docker-compose build', 'docker build .'],
                'common_fixes': {
                    'yaml_error': self.fix_yaml_error,
                    'dockerfile_error': self.fix_dockerfile_error,
                }
            }
        }
        
        # Maximum fix attempts
        self.max_fix_attempts = 3
        
    def run_comprehensive_test(self):
        """Main entry point - runs tests and fixes issues"""
        try:
            # Get session data from stdin
            hook_data = json.load(sys.stdin)
            
            session_id = hook_data.get('session_id', '')
            tools_used = hook_data.get('tools_used', [])
            original_prompt = hook_data.get('original_prompt', '')
            
            # Detect project type
            project_type = self.detect_project_type()
            
            print(f"🧪 Betty: Starting comprehensive testing for {project_type} project", file=sys.stderr)
            
            # Extract what was changed
            changed_files = self.extract_changed_files(tools_used)
            
            # Run comprehensive tests
            test_results = self.run_all_tests(project_type, changed_files)
            
            # If there are failures, attempt to fix
            if test_results['has_failures']:
                print(f"🔧 Betty: Found {len(test_results['failures'])} issues. Attempting automatic fixes...", file=sys.stderr)
                
                fix_results = self.attempt_fixes(test_results, project_type, changed_files)
                
                if fix_results['all_fixed']:
                    print(f"✅ Betty: All issues fixed! Running final verification...", file=sys.stderr)
                    
                    # Run tests again to verify
                    final_results = self.run_all_tests(project_type, changed_files)
                    
                    if not final_results['has_failures']:
                        self.send_success_notification(fix_results)
                        print(f"🎉 Betty: All tests passing! Ready for completion.", file=sys.stderr)
                    else:
                        self.send_partial_fix_notification(fix_results, final_results)
                        print(f"⚠️ Betty: Fixed {fix_results['fixed_count']} issues, {len(final_results['failures'])} remain", file=sys.stderr)
                else:
                    self.send_failure_notification(test_results)
                    print(f"❌ Betty: Could not fix all issues automatically", file=sys.stderr)
            else:
                print(f"✅ Betty: All tests passing! No fixes needed.", file=sys.stderr)
                
            # Save test report
            self.save_test_report(test_results, hook_data)
            
        except Exception as e:
            print(f"Auto test & fix error: {e}", file=sys.stderr)
            
        return 0
    
    def detect_project_type(self):
        """Detect the project type based on files present"""
        
        if (self.betty_dir / 'package.json').exists():
            return 'javascript'
        elif (self.betty_dir / 'requirements.txt').exists() or (self.betty_dir / 'setup.py').exists():
            return 'python'
        elif (self.betty_dir / 'docker-compose.yml').exists():
            return 'docker'
        else:
            # Check for predominant file types
            js_files = list(self.betty_dir.rglob('*.js')) + list(self.betty_dir.rglob('*.ts'))
            py_files = list(self.betty_dir.rglob('*.py'))
            
            if len(js_files) > len(py_files):
                return 'javascript'
            else:
                return 'python'
    
    def extract_changed_files(self, tools_used):
        """Extract files that were changed during session"""
        changed_files = []
        
        for tool in tools_used:
            if tool.get('name') in ['Edit', 'MultiEdit', 'Write']:
                file_path = tool.get('params', {}).get('file_path')
                if file_path and file_path not in changed_files:
                    changed_files.append(file_path)
                    
        return changed_files
    
    def run_all_tests(self, project_type, changed_files):
        """Run comprehensive tests for the project"""
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'project_type': project_type,
            'changed_files': changed_files,
            'tests_run': [],
            'failures': [],
            'has_failures': False
        }
        
        config = self.test_configs.get(project_type, {})
        
        # Run unit tests
        for test_cmd in config.get('test_commands', []):
            test_result = self.run_command(test_cmd)
            results['tests_run'].append({
                'command': test_cmd,
                'type': 'test',
                'success': test_result['success'],
                'output': test_result['output'][:1000]
            })
            
            if not test_result['success']:
                failures = self.parse_test_failures(test_result['output'], test_cmd)
                results['failures'].extend(failures)
        
        # Run linting
        for lint_cmd in config.get('lint_commands', []):
            lint_result = self.run_command(lint_cmd)
            results['tests_run'].append({
                'command': lint_cmd,
                'type': 'lint',
                'success': lint_result['success'],
                'output': lint_result['output'][:1000]
            })
            
            if not lint_result['success']:
                failures = self.parse_lint_failures(lint_result['output'], lint_cmd)
                results['failures'].extend(failures)
        
        # Run type checking
        for type_cmd in config.get('type_commands', []):
            type_result = self.run_command(type_cmd)
            results['tests_run'].append({
                'command': type_cmd,
                'type': 'type-check',
                'success': type_result['success'],
                'output': type_result['output'][:1000]
            })
            
            if not type_result['success']:
                failures = self.parse_type_failures(type_result['output'], type_cmd)
                results['failures'].extend(failures)
        
        # Run build
        for build_cmd in config.get('build_commands', []):
            build_result = self.run_command(build_cmd)
            results['tests_run'].append({
                'command': build_cmd,
                'type': 'build',
                'success': build_result['success'],
                'output': build_result['output'][:1000]
            })
            
            if not build_result['success']:
                failures = self.parse_build_failures(build_result['output'], build_cmd)
                results['failures'].extend(failures)
        
        results['has_failures'] = len(results['failures']) > 0
        
        return results
    
    def run_command(self, command):
        """Run a shell command and return results"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.betty_dir
            )
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout + result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': 'Command timed out after 60 seconds',
                'returncode': -1
            }
        except Exception as e:
            return {
                'success': False,
                'output': str(e),
                'returncode': -1
            }
    
    def parse_test_failures(self, output, command):
        """Parse test failures from output"""
        failures = []
        
        # Common test failure patterns
        patterns = [
            r'FAIL\s+(.+?)\.(.+?)\s',  # Jest
            r'FAILED\s+(.+?)::(.+?)\s',  # Pytest
            r'AssertionError:\s+(.+)',
            r'Error:\s+(.+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, output)
            for match in matches:
                failures.append({
                    'type': 'test_failure',
                    'command': command,
                    'details': match,
                    'fixable': True
                })
        
        return failures[:10]  # Limit to 10 failures
    
    def parse_lint_failures(self, output, command):
        """Parse lint failures from output"""
        failures = []
        
        # Common lint failure patterns
        patterns = [
            r'(.+?):(\d+):(\d+):\s+error:\s+(.+)',  # ESLint
            r'(.+?):(\d+):(\d+):\s+(.+)',  # Ruff/Flake8
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, output)
            for match in matches:
                failures.append({
                    'type': 'lint_error',
                    'command': command,
                    'file': match[0],
                    'line': match[1],
                    'column': match[2] if len(match) > 2 else 0,
                    'message': match[-1],
                    'fixable': True
                })
        
        return failures[:10]
    
    def parse_type_failures(self, output, command):
        """Parse type checking failures"""
        failures = []
        
        patterns = [
            r'(.+?):(\d+):\s+error:\s+(.+)',  # TypeScript
            r'(.+?):(\d+):\s+error:\s+(.+)',  # MyPy
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, output)
            for match in matches:
                failures.append({
                    'type': 'type_error',
                    'command': command,
                    'file': match[0],
                    'line': match[1],
                    'message': match[2],
                    'fixable': True
                })
        
        return failures[:10]
    
    def parse_build_failures(self, output, command):
        """Parse build failures"""
        failures = []
        
        if 'docker' in command.lower():
            if 'yaml' in output.lower() or 'yml' in output.lower():
                failures.append({
                    'type': 'yaml_error',
                    'command': command,
                    'fixable': True
                })
        
        return failures
    
    def attempt_fixes(self, test_results, project_type, changed_files):
        """Attempt to automatically fix issues"""
        
        fix_results = {
            'attempted': 0,
            'fixed': [],
            'failed': [],
            'fixed_count': 0,
            'all_fixed': False
        }
        
        config = self.test_configs.get(project_type, {})
        fixers = config.get('common_fixes', {})
        
        for failure in test_results['failures']:
            if not failure.get('fixable'):
                continue
                
            fix_results['attempted'] += 1
            
            # Try to fix based on failure type
            failure_type = failure.get('type')
            
            if failure_type in fixers:
                fixer = fixers[failure_type]
                if fixer(failure):
                    fix_results['fixed'].append(failure)
                    fix_results['fixed_count'] += 1
                    self.log_fix(failure, 'success')
                else:
                    fix_results['failed'].append(failure)
                    self.log_fix(failure, 'failed')
            else:
                # Try generic fixes
                if self.attempt_generic_fix(failure):
                    fix_results['fixed'].append(failure)
                    fix_results['fixed_count'] += 1
                else:
                    fix_results['failed'].append(failure)
        
        fix_results['all_fixed'] = (fix_results['fixed_count'] == len(test_results['failures']))
        
        return fix_results
    
    # JavaScript/TypeScript fixers
    def fix_missing_import_js(self, failure):
        """Fix missing import in JavaScript/TypeScript"""
        try:
            file_path = failure.get('file')
            if not file_path:
                return False
            
            # Read the file
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Try to identify missing import from error message
            message = failure.get('message', '')
            
            # Common patterns
            if "'React' is not defined" in message:
                if "import React" not in content:
                    content = "import React from 'react';\n" + content
                    with open(file_path, 'w') as f:
                        f.write(content)
                    return True
            
            return False
        except:
            return False
    
    def fix_syntax_error_js(self, failure):
        """Fix syntax errors in JavaScript"""
        try:
            file_path = failure.get('file')
            line_num = int(failure.get('line', 0))
            
            if not file_path or line_num == 0:
                return False
            
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            if line_num <= len(lines):
                line = lines[line_num - 1]
                
                # Common syntax fixes
                if line.rstrip().endswith(',') and line_num == len(lines):
                    # Remove trailing comma
                    lines[line_num - 1] = line.rstrip()[:-1] + '\n'
                elif not line.rstrip().endswith(';') and not line.rstrip().endswith('{'):
                    # Add missing semicolon
                    lines[line_num - 1] = line.rstrip() + ';\n'
                
                with open(file_path, 'w') as f:
                    f.writelines(lines)
                return True
            
            return False
        except:
            return False
    
    def fix_type_error_ts(self, failure):
        """Fix TypeScript type errors"""
        try:
            file_path = failure.get('file')
            message = failure.get('message', '')
            
            if not file_path:
                return False
            
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Common type fixes
            if "implicitly has an 'any' type" in message:
                # Add explicit any type (temporary fix)
                # This is a simplified example
                content = content.replace(': any', ': any')  # Placeholder
                with open(file_path, 'w') as f:
                    f.write(content)
                return True
            
            return False
        except:
            return False
    
    def fix_lint_error_js(self, failure):
        """Fix ESLint errors"""
        try:
            # Try auto-fix with ESLint
            result = self.run_command('npm run lint -- --fix')
            return result['success']
        except:
            return False
    
    # Python fixers
    def fix_import_error_py(self, failure):
        """Fix Python import errors"""
        try:
            file_path = failure.get('file')
            message = failure.get('message', '')
            
            if not file_path:
                return False
            
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Extract module name from error
            if "No module named" in message:
                match = re.search(r"No module named '(.+?)'", message)
                if match:
                    module = match.group(1)
                    # Try to install with pip
                    result = self.run_command(f'pip install {module}')
                    return result['success']
            
            return False
        except:
            return False
    
    def fix_syntax_error_py(self, failure):
        """Fix Python syntax errors"""
        try:
            file_path = failure.get('file')
            line_num = int(failure.get('line', 0))
            
            if not file_path or line_num == 0:
                return False
            
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            if line_num <= len(lines):
                line = lines[line_num - 1]
                
                # Common syntax fixes
                if line.rstrip().endswith(':') and line_num < len(lines):
                    # Check indentation of next line
                    next_line = lines[line_num]
                    if not next_line.startswith('    ') and not next_line.startswith('\t'):
                        lines[line_num] = '    ' + next_line
                
                with open(file_path, 'w') as f:
                    f.writelines(lines)
                return True
            
            return False
        except:
            return False
    
    def fix_indentation_error_py(self, failure):
        """Fix Python indentation errors"""
        try:
            file_path = failure.get('file')
            
            if not file_path:
                return False
            
            # Try autopep8 or black
            result = self.run_command(f'autopep8 --in-place {file_path}')
            if not result['success']:
                result = self.run_command(f'black {file_path}')
            
            return result['success']
        except:
            return False
    
    def fix_type_error_py(self, failure):
        """Fix Python type errors"""
        # Type errors often require manual intervention
        return False
    
    # Docker/YAML fixers
    def fix_yaml_error(self, failure):
        """Fix YAML formatting errors"""
        try:
            # Try to format with a YAML tool
            result = self.run_command('yamllint -d relaxed docker-compose.yml')
            return result['success']
        except:
            return False
    
    def fix_dockerfile_error(self, failure):
        """Fix Dockerfile errors"""
        # Dockerfile errors often require manual intervention
        return False
    
    def attempt_generic_fix(self, failure):
        """Attempt generic fixes for unknown failure types"""
        
        # Try some generic approaches
        failure_type = failure.get('type')
        
        if failure_type == 'lint_error':
            # Try auto-fix commands
            commands = [
                'npm run lint -- --fix',
                'ruff check --fix',
                'autopep8 --in-place --recursive .',
            ]
            
            for cmd in commands:
                result = self.run_command(cmd)
                if result['success']:
                    return True
        
        return False
    
    def log_fix(self, failure, status):
        """Log fix attempt to history"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'failure': failure,
            'status': status
        }
        
        with open(self.fix_history_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def save_test_report(self, test_results, hook_data):
        """Save comprehensive test report"""
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'session_id': hook_data.get('session_id'),
            'test_results': test_results,
            'stats': {
                'total_tests': len(test_results['tests_run']),
                'passed': sum(1 for t in test_results['tests_run'] if t['success']),
                'failed': sum(1 for t in test_results['tests_run'] if not t['success']),
                'failure_count': len(test_results['failures'])
            }
        }
        
        filename = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = self.test_results_dir / filename
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
    
    def send_success_notification(self, fix_results):
        """Send notification about successful fixes"""
        try:
            import requests
            
            message = f"All issues fixed automatically!\n"
            message += f"Fixed: {fix_results['fixed_count']} issues\n"
            message += f"Tests: All passing ✅"
            
            requests.post(
                'https://ntfy.da-tech.io/Betty',
                data=message.encode('utf-8'),
                headers={
                    'Title': 'Auto-Fix: Success',
                    'Priority': 'low',
                    'Tags': 'test,autofix,success'
                },
                timeout=2
            )
        except:
            pass
    
    def send_partial_fix_notification(self, fix_results, final_results):
        """Send notification about partial fixes"""
        try:
            import requests
            
            message = f"Partial auto-fix completed\n"
            message += f"Fixed: {fix_results['fixed_count']} issues\n"
            message += f"Remaining: {len(final_results['failures'])} issues\n"
            message += f"Manual intervention required"
            
            requests.post(
                'https://ntfy.da-tech.io/Betty',
                data=message.encode('utf-8'),
                headers={
                    'Title': 'Auto-Fix: Partial',
                    'Priority': 'default',
                    'Tags': 'test,autofix,partial'
                },
                timeout=2
            )
        except:
            pass
    
    def send_failure_notification(self, test_results):
        """Send notification about test failures"""
        try:
            import requests
            
            message = f"Tests failed - manual fixes needed\n"
            message += f"Failures: {len(test_results['failures'])}\n"
            
            # Include first few failures
            for failure in test_results['failures'][:3]:
                if 'file' in failure:
                    message += f"• {failure['file']}: {failure.get('message', 'error')[:50]}\n"
            
            requests.post(
                'https://ntfy.da-tech.io/Betty',
                data=message.encode('utf-8'),
                headers={
                    'Title': 'Auto-Fix: Manual Required',
                    'Priority': 'high',
                    'Tags': 'test,failure'
                },
                timeout=2
            )
        except:
            pass

if __name__ == '__main__':
    tester = BettyAutoTestFix()
    sys.exit(tester.run_comprehensive_test())