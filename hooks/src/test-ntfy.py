#!/usr/bin/env python3
"""
Test script for Betty NTFY notifications to Andre's server
"""

import requests
import json
from datetime import datetime

# Andre's NTFY server
NTFY_URL = "https://ntfy.da-tech.io"
NTFY_TOPIC = "Betty"

def test_notification(title, message, priority='default', tags=None):
    """Send test notification to Andre's NTFY server"""
    
    url = f"{NTFY_URL}/{NTFY_TOPIC}"
    
    # NTFY expects ASCII in headers, move emojis to message
    if any(ord(c) > 127 for c in title):
        # Move emoji to message body
        message = f"{title}\n\n{message}"
        title = title.encode('ascii', 'ignore').decode('ascii').strip() or 'Betty Notification'
    
    headers = {
        'Title': title,
        'Priority': priority,
    }
    
    if tags:
        headers['Tags'] = ','.join(tags)
    
    # Add click action
    headers['Click'] = 'https://betty.blockonauts.io/dashboard'
    
    print(f"Sending to: {url}")
    print(f"Title: {title}")
    print(f"Message: {message}")
    print(f"Priority: {priority}")
    print(f"Tags: {tags}")
    
    try:
        response = requests.post(
            url,
            data=message.encode('utf-8'),
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            print(f"✅ Notification sent successfully!")
            return True
        else:
            print(f"❌ Failed: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def run_tests():
    """Run test notifications"""
    
    print("=" * 50)
    print("Betty NTFY Test Suite")
    print(f"Server: {NTFY_URL}/{NTFY_TOPIC}")
    print("=" * 50)
    
    tests = [
        {
            'title': '🧪 Betty Test',
            'message': f'Betty NTFY integration test at {datetime.now().strftime("%H:%M:%S")}',
            'priority': 'low',
            'tags': ['test', 'betty']
        },
        {
            'title': '✅ Task Complete',
            'message': 'Betty successfully implemented NTFY notifications!',
            'priority': 'low',
            'tags': ['success', 'betty']
        },
        {
            'title': '⚠️ Warning Example',
            'message': 'This is what a warning would look like',
            'priority': 'default',
            'tags': ['warning', 'betty']
        },
        {
            'title': '🔴 Error Example',
            'message': 'This is what an error notification would look like',
            'priority': 'high',
            'tags': ['error', 'alert', 'betty']
        },
        {
            'title': '🧠 Betty Learned',
            'message': 'Betty captured new error pattern and learned the solution',
            'priority': 'min',
            'tags': ['learning', 'ai', 'betty']
        }
    ]
    
    print("\nSending test notifications...\n")
    
    for i, test in enumerate(tests, 1):
        print(f"\nTest {i}/{len(tests)}:")
        print("-" * 30)
        
        success = test_notification(
            title=test['title'],
            message=test['message'],
            priority=test['priority'],
            tags=test['tags']
        )
        
        if not success:
            print("\n⚠️ Some tests failed. Check your NTFY server configuration.")
            return False
    
    print("\n" + "=" * 50)
    print("✅ All tests completed!")
    print(f"Check your notifications at: {NTFY_URL}/{NTFY_TOPIC}")
    print("=" * 50)
    
    return True

if __name__ == '__main__':
    run_tests()