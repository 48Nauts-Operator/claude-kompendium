#!/usr/bin/env python3
"""
ABOUTME: Betty PreToolUse Guardian - Protects against dangerous operations
ABOUTME: Can BLOCK tool execution, warn about risks, and suggest alternatives
"""

import json
import sys
import re
import os
from datetime import datetime
from pathlib import Path

class BettyGuardian:
    def __init__(self):
        self.betty_dir = Path('/home/jarvis/projects/Betty')
        self.blocked_log = self.betty_dir / 'security' / 'blocked-operations.jsonl'
        self.failure_history = self.load_failure_history()
        
        # Critical files that should never be modified
        self.protected_files = [
            '/etc/passwd',
            '/etc/shadow', 
            '/etc/sudoers',
            '/.ssh/authorized_keys',
            '/boot/',
            '/sys/',
            '/proc/'
        ]
        
        # Dangerous command patterns
        self.dangerous_patterns = [
            r'rm\s+-rf\s+/',           # rm -rf from root
            r'rm\s+-rf\s+\*',          # rm -rf *
            r':\(\)\{\s*:\|\s*:&\s*\}', # Fork bomb
            r'>\s*/dev/sda',           # Overwriting disk
            r'dd\s+if=/dev/zero',      # Disk wipe
            r'chmod\s+777\s+/',        # Overly permissive root
            r'kill\s+-9\s+-1',         # Kill all processes
        ]
        
    def guard_tool_use(self):
        """Main guardian logic - can block operations"""
        try:
            # Get tool data from stdin
            hook_data = json.load(sys.stdin)
            tool_name = hook_data.get('tool_name', '')
            tool_input = hook_data.get('tool_input', {})
            
            # Check based on tool type
            if tool_name == 'Bash':
                return self.guard_bash_command(tool_input)
            elif tool_name in ['Edit', 'MultiEdit', 'Write']:
                return self.guard_file_operation(tool_name, tool_input)
            elif tool_name == 'KillBash':
                return self.guard_kill_operation(tool_input)
                
            # Check general patterns
            return self.check_general_safety(tool_name, tool_input)
            
        except Exception as e:
            print(f"Guardian error: {e}", file=sys.stderr)
            return 0  # Don't block on guardian failure
    
    def guard_bash_command(self, tool_input):
        """Guard Bash commands"""
        command = tool_input.get('command', '')
        
        # Check for dangerous patterns
        for pattern in self.dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                self.block_operation('bash', command, f"Dangerous pattern: {pattern}")
                print(f"⛔ BLOCKED: Dangerous command pattern detected", file=sys.stderr)
                print(f"   Pattern: {pattern}", file=sys.stderr)
                print(f"   Command: {command[:100]}...", file=sys.stderr)
                return 1  # BLOCK
        
        # Check for sudo without need
        if 'sudo' in command and not self.needs_sudo(command):
            print(f"⚠️ Warning: sudo may not be needed for this command", file=sys.stderr)
        
        # Check failure history
        if self.has_failed_recently(command):
            print(f"⚠️ Warning: This command failed 3+ times recently", file=sys.stderr)
            print(f"   Consider alternative approach", file=sys.stderr)
        
        # Check for production operations
        if any(word in command for word in ['production', 'prod', 'live']):
            print(f"🚨 PRODUCTION OPERATION DETECTED", file=sys.stderr)
            print(f"   Double-check before proceeding!", file=sys.stderr)
            # Could block if not in deployment mode
        
        # Check for large file operations
        if 'find' in command and '/' == command.split()[-1]:
            print(f"⚠️ Warning: Find from root will be slow", file=sys.stderr)
            print(f"   Consider more specific path", file=sys.stderr)
        
        return 0  # Allow
    
    def guard_file_operation(self, tool_name, tool_input):
        """Guard file operations"""
        file_path = tool_input.get('file_path', '')
        
        # Check protected files
        for protected in self.protected_files:
            if file_path.startswith(protected):
                self.block_operation(tool_name, file_path, f"Protected file: {protected}")
                print(f"⛔ BLOCKED: Cannot modify protected file", file=sys.stderr)
                print(f"   File: {file_path}", file=sys.stderr)
                return 1  # BLOCK
        
        # Check for sensitive files
        if any(pattern in file_path for pattern in ['.env', 'secrets', 'password', 'key', 'token']):
            print(f"⚠️ Warning: Modifying sensitive file", file=sys.stderr)
            print(f"   File: {file_path}", file=sys.stderr)
            print(f"   Ensure no secrets are exposed", file=sys.stderr)
        
        # Check for large files
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            if size > 10 * 1024 * 1024:  # 10MB
                print(f"⚠️ Warning: Large file ({size // 1024 // 1024}MB)", file=sys.stderr)
                print(f"   Consider using specialized tools", file=sys.stderr)
        
        # Check for binary files
        if self.is_binary_file(file_path):
            print(f"⚠️ Warning: Appears to be binary file", file=sys.stderr)
            print(f"   Text operations may corrupt it", file=sys.stderr)
        
        return 0  # Allow
    
    def guard_kill_operation(self, tool_input):
        """Guard process kill operations"""
        shell_id = tool_input.get('shell_id', '')
        
        # Check if it's a critical process
        if shell_id in ['betty-proxy', 'memory-api', 'frontend']:
            print(f"⚠️ Warning: Killing critical Betty component", file=sys.stderr)
            print(f"   This may disrupt Betty's operations", file=sys.stderr)
        
        return 0  # Allow but warn
    
    def check_general_safety(self, tool_name, tool_input):
        """General safety checks"""
        
        # Check for patterns that suggest mistakes
        input_str = json.dumps(tool_input)
        
        # Check for localhost in production
        if 'localhost' in input_str or '127.0.0.1' in input_str:
            cwd = os.getcwd()
            if 'production' in cwd or 'live' in cwd:
                print(f"⚠️ Warning: localhost reference in production context", file=sys.stderr)
        
        # Check for hardcoded credentials
        if re.search(r'(password|token|key|secret)\s*=\s*["\'][^"\']+["\']', input_str, re.IGNORECASE):
            print(f"⚠️ Warning: Possible hardcoded credentials detected", file=sys.stderr)
            print(f"   Consider using environment variables", file=sys.stderr)
        
        return 0  # Allow
    
    def has_failed_recently(self, command):
        """Check if command has failed recently"""
        cmd_key = command.split()[0] if command else ''
        return self.failure_history.get(cmd_key, 0) >= 3
    
    def load_failure_history(self):
        """Load history of failed commands"""
        history = {}
        try:
            log_file = self.betty_dir / 'logs' / 'command-failures.json'
            if log_file.exists():
                with open(log_file) as f:
                    history = json.load(f)
        except:
            pass
        return history
    
    def needs_sudo(self, command):
        """Check if command actually needs sudo"""
        # Commands that typically need sudo
        sudo_commands = ['apt', 'systemctl', 'service', 'docker', 'mount']
        return any(cmd in command for cmd in sudo_commands)
    
    def is_binary_file(self, file_path):
        """Check if file is binary"""
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                return b'\0' in chunk
        except:
            return False
    
    def block_operation(self, tool, operation, reason):
        """Log blocked operation"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'tool': tool,
            'operation': operation[:200],
            'reason': reason,
            'action': 'blocked'
        }
        
        self.blocked_log.parent.mkdir(parents=True, exist_ok=True)
        with open(self.blocked_log, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        # Send NTFY alert
        self.send_security_alert(tool, reason)
    
    def send_security_alert(self, tool, reason):
        """Send security alert via NTFY"""
        try:
            import requests
            requests.post(
                'https://ntfy.da-tech.io/Betty',
                data=f"Security: Blocked {tool} operation\nReason: {reason}".encode('utf-8'),
                headers={'Title': 'Security Alert', 'Priority': 'high', 'Tags': 'security,alert'},
                timeout=2
            )
        except:
            pass

if __name__ == '__main__':
    guardian = BettyGuardian()
    sys.exit(guardian.guard_tool_use())