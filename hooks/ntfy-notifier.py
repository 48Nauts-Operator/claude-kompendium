#!/usr/bin/env python3
"""
ABOUTME: Betty NTFY Notification Hook - Sends Claude Code notifications to Andre via NTFY
ABOUTME: Filters and forwards important events to ntfy.sh for real-time monitoring
"""

import json
import sys
import requests
from datetime import datetime
import os

# NTFY Configuration - Andre's personal server
NTFY_URL = "https://ntfy.da-tech.io"
NTFY_TOPIC = os.environ.get('BETTY_NTFY_TOPIC', 'Betty')  # Andre's Betty topic
NTFY_PRIORITY = {
    'error': 'high',
    'warning': 'default', 
    'success': 'low',
    'info': 'min'
}

# Notification filtering - what to send to Andre
NOTIFY_PATTERNS = {
    'errors': True,           # Always notify on errors
    'completions': True,      # Task completions
    'warnings': True,         # Security or other warnings
    'long_running': True,     # Operations taking > 30s
    'test_failures': True,    # Test failures
    'deployments': True,      # Deployment operations
    'security_events': True   # Security-related events
}

def send_ntfy_notification(title, message, priority='default', tags=None):
    """Send notification to NTFY"""
    
    # Construct NTFY URL
    url = f"{NTFY_URL}/{NTFY_TOPIC}"
    
    # NTFY expects ASCII in headers, move emojis to message
    if any(ord(c) > 127 for c in title):
        # Move emoji to message body
        message = f"{title}\n\n{message}"
        title = title.encode('ascii', 'ignore').decode('ascii').strip() or 'Betty Notification'
    
    # Prepare headers
    headers = {
        'Title': title,
        'Priority': priority,
    }
    
    # Add tags if provided
    if tags:
        headers['Tags'] = ','.join(tags)
    
    # Add click action to open Betty dashboard
    headers['Click'] = 'https://betty.blockonauts.io/dashboard'
    
    try:
        response = requests.post(
            url,
            data=message.encode('utf-8'),
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            return True
        else:
            print(f"Failed to send NTFY: {response.status_code}", file=sys.stderr)
            return False
            
    except Exception as e:
        print(f"NTFY error: {e}", file=sys.stderr)
        return False

def process_notification():
    """Process Claude Code notification and forward to NTFY if relevant"""
    
    try:
        # Read hook data from stdin
        hook_data = json.load(sys.stdin)
        
        # Extract notification details
        notification_type = hook_data.get('type', 'info')
        message = hook_data.get('message', '')
        context = hook_data.get('context', {})
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # Determine if we should notify Andre
        should_notify, reason = should_send_notification(notification_type, message, context)
        
        if should_notify:
            # Prepare notification
            title = format_title(notification_type, reason)
            formatted_message = format_message(message, context, timestamp)
            priority = determine_priority(notification_type, message)
            tags = determine_tags(notification_type, reason)
            
            # Send to NTFY
            success = send_ntfy_notification(
                title=title,
                message=formatted_message,
                priority=priority,
                tags=tags
            )
            
            if success:
                log_notification(notification_type, message, reason)
        
        # Log all notifications for Betty's learning
        log_for_betty(hook_data)
        
    except Exception as e:
        # Emergency notification for hook failure
        send_ntfy_notification(
            title="⚠️ Betty Hook Error",
            message=f"Notification hook failed: {str(e)}",
            priority='high',
            tags=['warning', 'betty']
        )
        return 1
    
    return 0

def should_send_notification(notification_type, message, context):
    """Determine if notification should be sent to Andre"""
    
    message_lower = message.lower()
    
    # High priority - always notify
    if notification_type == 'error':
        return True, 'error'
    
    if 'error' in message_lower or 'failed' in message_lower:
        return True, 'error_detected'
    
    if 'warning' in message_lower or 'warn' in message_lower:
        return True, 'warning'
    
    # Task completions
    if 'completed' in message_lower or 'finished' in message_lower or 'done' in message_lower:
        if context.get('duration', 0) > 30000:  # Long running task
            return True, 'long_task_complete'
        return True, 'task_complete'
    
    # Test failures
    if 'test' in message_lower and ('fail' in message_lower or 'error' in message_lower):
        return True, 'test_failure'
    
    # Deployment events
    if 'deploy' in message_lower or 'production' in message_lower:
        return True, 'deployment'
    
    # Security events
    if 'security' in message_lower or 'injection' in message_lower or 'blocked' in message_lower:
        return True, 'security'
    
    # Betty-specific events
    if 'betty' in message_lower:
        if 'learned' in message_lower or 'captured' in message_lower:
            return True, 'betty_learning'
    
    # Docker events
    if 'docker' in message_lower or 'container' in message_lower:
        if 'stopped' in message_lower or 'crashed' in message_lower:
            return True, 'docker_issue'
    
    # Default: don't spam Andre with everything
    return False, None

def format_title(notification_type, reason):
    """Format notification title"""
    
    titles = {
        'error': '🔴 Error',
        'error_detected': '⚠️ Error Detected',
        'warning': '⚡ Warning',
        'task_complete': '✅ Task Complete',
        'long_task_complete': '⏱️ Long Task Complete',
        'test_failure': '🧪 Tests Failed',
        'deployment': '🚀 Deployment Event',
        'security': '🛡️ Security Alert',
        'betty_learning': '🧠 Betty Learned',
        'docker_issue': '🐳 Docker Issue'
    }
    
    return titles.get(reason, f'📢 {notification_type.title()}')

def format_message(message, context, timestamp):
    """Format notification message"""
    
    # Truncate long messages
    if len(message) > 500:
        message = message[:497] + '...'
    
    # Add context if available
    formatted = f"[{timestamp}] {message}"
    
    if context.get('tool'):
        formatted += f"\nTool: {context['tool']}"
    
    if context.get('file'):
        formatted += f"\nFile: {context['file']}"
    
    if context.get('duration'):
        duration_s = context['duration'] / 1000
        formatted += f"\nDuration: {duration_s:.1f}s"
    
    return formatted

def determine_priority(notification_type, message):
    """Determine NTFY priority"""
    
    message_lower = message.lower()
    
    if notification_type == 'error' or 'failed' in message_lower:
        return 'high'
    
    if notification_type == 'warning' or 'security' in message_lower:
        return 'default'
    
    if 'completed' in message_lower or 'success' in message_lower:
        return 'low'
    
    return 'min'

def determine_tags(notification_type, reason):
    """Determine notification tags"""
    
    tags = ['betty']
    
    tag_map = {
        'error': ['error', 'alert'],
        'warning': ['warning'],
        'task_complete': ['success'],
        'test_failure': ['test', 'failure'],
        'deployment': ['deploy'],
        'security': ['security', 'alert'],
        'betty_learning': ['learning', 'ai'],
        'docker_issue': ['docker', 'infra']
    }
    
    if reason in tag_map:
        tags.extend(tag_map[reason])
    
    return tags[:4]  # NTFY supports max 4 tags

def log_notification(notification_type, message, reason):
    """Log sent notifications"""
    
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'type': notification_type,
        'reason': reason,
        'message': message[:100],  # First 100 chars
        'sent_to_ntfy': True
    }
    
    log_file = '/home/jarvis/projects/Betty/logs/ntfy-notifications.jsonl'
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')

def log_for_betty(hook_data):
    """Log all notifications for Betty's learning"""
    
    log_file = '/home/jarvis/projects/Betty/capture/notifications.jsonl'
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    with open(log_file, 'a') as f:
        f.write(json.dumps({
            'timestamp': datetime.now().isoformat(),
            **hook_data
        }) + '\n')

if __name__ == '__main__':
    sys.exit(process_notification())