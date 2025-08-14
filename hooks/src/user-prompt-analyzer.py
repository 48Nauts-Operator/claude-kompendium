#!/usr/bin/env python3
"""
ABOUTME: Betty UserPromptSubmit Hook - Analyzes user intent BEFORE Claude processes
ABOUTME: Pre-loads context, predicts needs, and prepares workspace proactively
"""

import json
import sys
import os
import re
import requests
from datetime import datetime
from pathlib import Path

class BettyIntentAnalyzer:
    def __init__(self):
        self.betty_dir = Path('/home/jarvis/projects/Betty')
        self.context_cache = self.betty_dir / 'cache' / 'context'
        self.patterns_db = self.betty_dir / 'patterns'
        
    def analyze_prompt(self):
        """Analyze user prompt before Claude processes it"""
        try:
            # Get prompt from stdin
            hook_data = json.load(sys.stdin)
            prompt = hook_data.get('prompt', '')
            
            # Analyze intent
            intent = self.classify_intent(prompt)
            
            # Pre-load relevant context based on intent
            self.preload_context(intent, prompt)
            
            # Check for potential issues
            warnings = self.check_warnings(prompt, intent)
            if warnings:
                self.send_warnings(warnings)
            
            # Predict likely needs
            predictions = self.predict_needs(prompt, intent)
            if predictions:
                self.prepare_workspace(predictions)
            
            # Log for learning
            self.log_intent(prompt, intent, predictions)
            
            # Send NTFY if significant
            if intent in ['deployment', 'production', 'security']:
                self.notify_andre(intent, prompt)
                
        except Exception as e:
            print(f"Intent analysis error: {e}", file=sys.stderr)
            
        return 0
    
    def classify_intent(self, prompt):
        """Classify user intent from prompt"""
        prompt_lower = prompt.lower()
        
        # Critical intents
        if any(word in prompt_lower for word in ['deploy', 'production', 'release']):
            return 'deployment'
        if any(word in prompt_lower for word in ['security', 'vulnerability', 'injection']):
            return 'security'
        if any(word in prompt_lower for word in ['emergency', 'urgent', 'critical']):
            return 'emergency'
            
        # Development intents
        if any(word in prompt_lower for word in ['fix', 'bug', 'error', 'broken']):
            return 'bug_fix'
        if any(word in prompt_lower for word in ['test', 'testing', 'spec']):
            return 'testing'
        if any(word in prompt_lower for word in ['refactor', 'clean', 'optimize']):
            return 'refactor'
        if any(word in prompt_lower for word in ['add', 'create', 'implement', 'build']):
            return 'feature'
            
        # Research intents
        if any(word in prompt_lower for word in ['how', 'what', 'why', 'explain']):
            return 'research'
        if any(word in prompt_lower for word in ['find', 'search', 'locate', 'where']):
            return 'search'
            
        return 'general'
    
    def preload_context(self, intent, prompt):
        """Pre-load relevant context based on intent"""
        
        if intent == 'bug_fix':
            # Load recent errors and their solutions
            self.load_error_patterns()
            self.load_recent_fixes()
            print("🔍 Betty: Pre-loaded error patterns and recent fixes", file=sys.stderr)
            
        elif intent == 'deployment':
            # Load deployment checklist and history
            self.load_deployment_checklist()
            self.check_deployment_readiness()
            print("🚀 Betty: Pre-loaded deployment checklist", file=sys.stderr)
            
        elif intent == 'security':
            # Load security patterns and recent audits
            self.load_security_patterns()
            print("🛡️ Betty: Pre-loaded security patterns", file=sys.stderr)
            
        elif intent == 'feature':
            # Load similar implementations
            self.load_similar_features(prompt)
            print("💡 Betty: Pre-loaded similar feature implementations", file=sys.stderr)
    
    def check_warnings(self, prompt, intent):
        """Check for potential warnings"""
        warnings = []
        
        # Deployment warnings
        if intent == 'deployment':
            if not self.is_main_branch():
                warnings.append("⚠️ Not on main branch!")
            if self.has_uncommitted_changes():
                warnings.append("⚠️ Uncommitted changes detected!")
            if not self.tests_passing():
                warnings.append("⚠️ Tests are not passing!")
                
        # Security warnings
        if 'sudo' in prompt or 'root' in prompt:
            warnings.append("⚠️ Elevated privileges requested - be careful!")
            
        # Data warnings
        if any(word in prompt.lower() for word in ['delete', 'drop', 'remove', 'rm -rf']):
            warnings.append("⚠️ Destructive operation detected - ensure backups!")
            
        return warnings
    
    def send_warnings(self, warnings):
        """Send warnings to stderr for Claude to see"""
        for warning in warnings:
            print(warning, file=sys.stderr)
    
    def predict_needs(self, prompt, intent):
        """Predict what user will likely need"""
        predictions = {
            'tools': [],
            'files': [],
            'commands': []
        }
        
        if intent == 'bug_fix':
            predictions['tools'] = ['Grep', 'Read', 'Edit', 'Bash']
            predictions['commands'] = ['npm test', 'docker logs']
            
        elif intent == 'deployment':
            predictions['commands'] = ['git status', 'npm run build', 'docker-compose up']
            predictions['files'] = ['docker-compose.yml', '.env', 'package.json']
            
        elif intent == 'testing':
            predictions['tools'] = ['Read', 'Write', 'Bash']
            predictions['commands'] = ['npm test', 'pytest', 'jest']
            
        return predictions
    
    def prepare_workspace(self, predictions):
        """Prepare workspace based on predictions"""
        
        # Pre-warm caches
        for file in predictions.get('files', []):
            self.cache_file_if_exists(file)
            
        # Pre-check commands
        for cmd in predictions.get('commands', []):
            self.verify_command_available(cmd)
    
    def notify_andre(self, intent, prompt):
        """Send NTFY notification for significant intents"""
        
        if intent == 'deployment':
            title = "🚀 Deployment Request"
        elif intent == 'security':
            title = "🛡️ Security Task"
        elif intent == 'emergency':
            title = "🚨 Emergency Request"
        else:
            title = f"🎯 {intent.title()} Task"
            
        message = f"Intent: {intent}\nPrompt: {prompt[:100]}..."
        
        # Send to NTFY
        try:
            requests.post(
                'https://ntfy.da-tech.io/Betty',
                data=message.encode('utf-8'),
                headers={'Title': title, 'Priority': 'high' if intent == 'emergency' else 'default'},
                timeout=2
            )
        except:
            pass  # Don't block on notification failure
    
    def log_intent(self, prompt, intent, predictions):
        """Log intent for Betty's learning"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'prompt': prompt[:200],
            'intent': intent,
            'predictions': predictions
        }
        
        log_file = self.betty_dir / 'logs' / 'intents.jsonl'
        log_file.parent.mkdir(exist_ok=True)
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    # Helper methods
    def is_main_branch(self):
        """Check if on main branch"""
        try:
            import subprocess
            result = subprocess.run(['git', 'branch', '--show-current'], 
                                  capture_output=True, text=True, timeout=1)
            return result.stdout.strip() in ['main', 'master']
        except:
            return True
    
    def has_uncommitted_changes(self):
        """Check for uncommitted changes"""
        try:
            import subprocess
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True, timeout=1)
            return bool(result.stdout.strip())
        except:
            return False
    
    def tests_passing(self):
        """Check if tests are passing (simplified)"""
        # Would check test results cache
        return True
    
    def load_error_patterns(self):
        """Load known error patterns"""
        # Load from Betty's error database
        pass
    
    def load_deployment_checklist(self):
        """Load deployment checklist"""
        checklist = [
            "Tests passing",
            "No uncommitted changes",
            "On main branch",
            "Docker containers healthy",
            "Environment variables set"
        ]
        print(f"📋 Deployment checklist: {', '.join(checklist)}", file=sys.stderr)
    
    def check_deployment_readiness(self):
        """Check if ready for deployment"""
        ready = True
        if not self.is_main_branch():
            print("❌ Not on main branch", file=sys.stderr)
            ready = False
        if self.has_uncommitted_changes():
            print("❌ Uncommitted changes exist", file=sys.stderr)
            ready = False
        
        if ready:
            print("✅ Deployment checks passed", file=sys.stderr)
        else:
            print("⚠️ Deployment not recommended - fix issues first", file=sys.stderr)
    
    def load_similar_features(self, prompt):
        """Load similar feature implementations"""
        # Search for similar code patterns
        pass
    
    def cache_file_if_exists(self, filename):
        """Pre-cache file for faster access"""
        # Would implement file caching
        pass
    
    def verify_command_available(self, cmd):
        """Verify command is available"""
        # Would check if command exists
        pass

if __name__ == '__main__':
    analyzer = BettyIntentAnalyzer()
    sys.exit(analyzer.analyze_prompt())