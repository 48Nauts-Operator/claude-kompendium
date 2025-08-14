#!/usr/bin/env python3
"""
ABOUTME: Betty Stop Hook - Analyzes complete session outcomes
ABOUTME: Captures solutions, patterns, and learns from every session
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path
import hashlib

class BettySessionAnalyzer:
    def __init__(self):
        self.betty_dir = Path('/home/jarvis/projects/Betty')
        self.solutions_dir = self.betty_dir / 'solutions'
        self.patterns_dir = self.betty_dir / 'patterns'
        self.metrics_file = self.betty_dir / 'metrics' / 'sessions.json'
        
    def analyze_session(self):
        """Analyze complete session when Claude stops"""
        try:
            # Get session data from stdin
            hook_data = json.load(sys.stdin)
            
            # Extract session info
            session_id = hook_data.get('session_id', '')
            duration = hook_data.get('duration', 0)
            prompt = hook_data.get('original_prompt', '')
            tools_used = hook_data.get('tools_used', [])
            final_state = hook_data.get('final_state', {})
            
            # Determine success
            success = self.determine_success(final_state, tools_used)
            
            # Extract pattern
            pattern = self.extract_pattern(tools_used)
            
            # If successful, capture solution
            if success:
                solution = self.capture_solution(prompt, tools_used, pattern)
                self.store_solution(solution)
                print(f"✅ Betty: Solution captured - Pattern: {pattern}", file=sys.stderr)
            else:
                # Analyze failure
                failure = self.analyze_failure(prompt, tools_used, final_state)
                self.store_failure(failure)
                print(f"📝 Betty: Failure analysis stored", file=sys.stderr)
            
            # Update metrics
            self.update_metrics(success, duration, pattern)
            
            # Send summary notification
            self.send_session_summary(success, duration, pattern)
            
        except Exception as e:
            print(f"Session analysis error: {e}", file=sys.stderr)
            
        return 0
    
    def determine_success(self, final_state, tools_used):
        """Determine if session was successful"""
        
        # Check for error indicators
        if final_state.get('errors', 0) > 0:
            return False
            
        # Check if tests were run and passed
        bash_tools = [t for t in tools_used if t.get('name') == 'Bash']
        for tool in bash_tools:
            output = tool.get('output', '')
            if 'test' in tool.get('command', '').lower():
                if 'failed' in output.lower() or 'error' in output.lower():
                    return False
                    
        # Check for completion indicators
        if any('complete' in str(t).lower() for t in tools_used):
            return True
            
        # Default to success if no errors
        return final_state.get('errors', 0) == 0
    
    def extract_pattern(self, tools_used):
        """Extract workflow pattern from tools"""
        
        # Create tool sequence
        sequence = []
        for tool in tools_used:
            tool_name = tool.get('name', '')
            if tool_name:
                sequence.append(tool_name)
        
        # Simplify sequence
        pattern = '->'.join(sequence[:10])  # First 10 tools
        
        # Match against known patterns
        known_patterns = {
            'Read->Edit->Bash': 'modify_and_test',
            'Grep->Read->Edit': 'search_and_fix',
            'Write->Bash': 'create_and_run',
            'Bash->Read->Edit->Bash': 'debug_cycle',
            'MultiEdit->Bash': 'bulk_change_and_test'
        }
        
        for known, name in known_patterns.items():
            if known in pattern:
                return name
                
        # Generate hash for unknown pattern
        return f"pattern_{hashlib.md5(pattern.encode()).hexdigest()[:8]}"
    
    def capture_solution(self, prompt, tools_used, pattern):
        """Capture successful solution"""
        
        solution = {
            'timestamp': datetime.now().isoformat(),
            'problem': prompt[:500],
            'pattern': pattern,
            'tool_sequence': [
                {
                    'name': t.get('name'),
                    'key_params': self.extract_key_params(t)
                }
                for t in tools_used[:20]  # First 20 tools
            ],
            'file_changes': self.extract_file_changes(tools_used),
            'commands_run': self.extract_commands(tools_used),
            'success_indicators': self.extract_success_indicators(tools_used)
        }
        
        return solution
    
    def analyze_failure(self, prompt, tools_used, final_state):
        """Analyze failed session"""
        
        failure = {
            'timestamp': datetime.now().isoformat(),
            'problem': prompt[:500],
            'error_points': self.identify_error_points(tools_used),
            'last_successful_step': self.find_last_success(tools_used),
            'potential_causes': self.identify_failure_causes(tools_used, final_state),
            'recovery_suggestions': self.suggest_recovery(tools_used)
        }
        
        return failure
    
    def extract_key_params(self, tool):
        """Extract key parameters from tool"""
        params = tool.get('params', {})
        
        # Only keep important params
        if tool.get('name') == 'Bash':
            return {'command': params.get('command', '')[:100]}
        elif tool.get('name') in ['Edit', 'Write']:
            return {'file': params.get('file_path', '')}
        elif tool.get('name') == 'Grep':
            return {'pattern': params.get('pattern', '')[:50]}
            
        return {}
    
    def extract_file_changes(self, tools_used):
        """Extract files that were changed"""
        changed_files = set()
        
        for tool in tools_used:
            if tool.get('name') in ['Edit', 'MultiEdit', 'Write']:
                file_path = tool.get('params', {}).get('file_path', '')
                if file_path:
                    changed_files.add(file_path)
                    
        return list(changed_files)[:20]  # Max 20 files
    
    def extract_commands(self, tools_used):
        """Extract commands that were run"""
        commands = []
        
        for tool in tools_used:
            if tool.get('name') == 'Bash':
                cmd = tool.get('params', {}).get('command', '')
                if cmd and cmd not in commands:
                    commands.append(cmd[:100])
                    
        return commands[:10]  # Max 10 commands
    
    def extract_success_indicators(self, tools_used):
        """Extract what indicated success"""
        indicators = []
        
        for tool in tools_used:
            output = str(tool.get('output', ''))
            if 'success' in output.lower() or 'complete' in output.lower():
                indicators.append(f"{tool.get('name')}: success/complete found")
            if 'pass' in output.lower() and 'test' in output.lower():
                indicators.append(f"{tool.get('name')}: tests passing")
                
        return indicators[:5]
    
    def identify_error_points(self, tools_used):
        """Identify where errors occurred"""
        error_points = []
        
        for i, tool in enumerate(tools_used):
            if tool.get('error') or 'error' in str(tool.get('output', '')).lower():
                error_points.append({
                    'step': i,
                    'tool': tool.get('name'),
                    'error': str(tool.get('error', ''))[:200]
                })
                
        return error_points[:5]
    
    def find_last_success(self, tools_used):
        """Find last successful operation"""
        for i in range(len(tools_used) - 1, -1, -1):
            tool = tools_used[i]
            if not tool.get('error') and tool.get('output'):
                return {
                    'step': i,
                    'tool': tool.get('name'),
                    'operation': str(tool.get('params', {}))[:100]
                }
        return None
    
    def identify_failure_causes(self, tools_used, final_state):
        """Identify potential failure causes"""
        causes = []
        
        # Check for common failure patterns
        if any('permission denied' in str(t).lower() for t in tools_used):
            causes.append('Permission issues')
        if any('not found' in str(t).lower() for t in tools_used):
            causes.append('Missing files or commands')
        if any('syntax error' in str(t).lower() for t in tools_used):
            causes.append('Syntax errors in code')
            
        return causes
    
    def suggest_recovery(self, tools_used):
        """Suggest recovery actions"""
        suggestions = []
        
        # Based on failure patterns
        if any('permission' in str(t).lower() for t in tools_used):
            suggestions.append('Check file permissions')
        if any('docker' in str(t).lower() for t in tools_used):
            suggestions.append('Verify Docker is running')
            
        return suggestions
    
    def store_solution(self, solution):
        """Store successful solution"""
        self.solutions_dir.mkdir(parents=True, exist_ok=True)
        
        # Create filename from pattern
        filename = f"{solution['pattern']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(self.solutions_dir / filename, 'w') as f:
            json.dump(solution, f, indent=2)
    
    def store_failure(self, failure):
        """Store failure analysis"""
        failures_dir = self.betty_dir / 'failures'
        failures_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"failure_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(failures_dir / filename, 'w') as f:
            json.dump(failure, f, indent=2)
    
    def update_metrics(self, success, duration, pattern):
        """Update session metrics"""
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing metrics
        metrics = {}
        if self.metrics_file.exists():
            with open(self.metrics_file) as f:
                metrics = json.load(f)
        
        # Update metrics
        if 'patterns' not in metrics:
            metrics['patterns'] = {}
        if pattern not in metrics['patterns']:
            metrics['patterns'][pattern] = {'count': 0, 'success': 0, 'total_duration': 0}
            
        metrics['patterns'][pattern]['count'] += 1
        if success:
            metrics['patterns'][pattern]['success'] += 1
        metrics['patterns'][pattern]['total_duration'] += duration
        
        # Save metrics
        with open(self.metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)
    
    def send_session_summary(self, success, duration, pattern):
        """Send session summary via NTFY"""
        try:
            import requests
            
            status = "✅ Success" if success else "❌ Failed"
            duration_min = duration / 60000  # Convert to minutes
            
            message = f"Pattern: {pattern}\nDuration: {duration_min:.1f} min"
            
            requests.post(
                'https://ntfy.da-tech.io/Betty',
                data=message.encode('utf-8'),
                headers={
                    'Title': f'Session Complete: {status}',
                    'Priority': 'low' if success else 'default',
                    'Tags': 'session,complete'
                },
                timeout=2
            )
        except:
            pass

if __name__ == '__main__':
    analyzer = BettySessionAnalyzer()
    sys.exit(analyzer.analyze_session())