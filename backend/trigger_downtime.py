"""
Manual trigger script for downtime tracker
Use this to manually mark your server as offline or online
"""

import requests
import sys

DOWNTIME_TRACKER_URL = 'https://portfolio-blry.onrender.com/api/downtime'


def trigger_offline():
    """Mark server as offline"""
    try:
        response = requests.post(f'{DOWNTIME_TRACKER_URL}/trigger-offline')
        data = response.json()
        print(f"✗ Server marked as OFFLINE")
        print(f"  Status: {data.get('status')}")
        print(f"  Message: {data.get('message')}")
        print(f"  Offline since: {data.get('offline_since')}")
    except Exception as e:
        print(f"Error: {e}")


def trigger_online():
    """Mark server as online"""
    try:
        response = requests.post(f'{DOWNTIME_TRACKER_URL}/trigger-online')
        data = response.json()
        print(f"✓ Server marked as ONLINE")
        print(f"  Status: {data.get('status')}")
        print(f"  Message: {data.get('message')}")
        print(f"  Downtime duration: {data.get('downtime_duration_seconds', 0):.0f}s")
        print(f"  Total downtime: {data.get('total_downtime_seconds', 0):.0f}s")
    except Exception as e:
        print(f"Error: {e}")


def check_status():
    """Check current downtime status"""
    try:
        response = requests.get(f'{DOWNTIME_TRACKER_URL}/status')
        data = response.json()
        print(f"Current Status:")
        print(f"  Is offline: {data.get('is_offline')}")
        print(f"  Current downtime: {data.get('current_downtime_seconds', 0):.0f}s")
        print(f"  Total downtime: {data.get('total_downtime_seconds', 0):.0f}s")
        print(f"  Offline since: {data.get('offline_since')}")
    except Exception as e:
        print(f"Error: {e}")


def reset():
    """Reset downtime tracker"""
    try:
        response = requests.post(f'{DOWNTIME_TRACKER_URL}/reset')
        data = response.json()
        print(f"Downtime tracker reset")
        print(f"  Status: {data.get('status')}")
        print(f"  Message: {data.get('message')}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python trigger_downtime.py offline   - Mark server as offline")
        print("  python trigger_downtime.py online    - Mark server as online")
        print("  python trigger_downtime.py status    - Check current status")
        print("  python trigger_downtime.py reset     - Reset downtime tracker")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == 'offline':
        trigger_offline()
    elif command == 'online':
        trigger_online()
    elif command == 'status':
        check_status()
    elif command == 'reset':
        reset()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
