"""
Server Monitor Script
This script monitors your main server and automatically triggers the downtime tracker.
Run this on a separate service (like Render, Railway, or your local machine).
"""

import requests
import time
from datetime import datetime

# Configuration
MAIN_SERVER_URL = 'https://stats.gowshik.online/api/homeserver'
DOWNTIME_TRACKER_URL = 'https://your-downtime-tracker.onrender.com/api/downtime'
CHECK_INTERVAL = 30  # Check every 30 seconds

# State tracking
last_status = None


def check_server_status():
    """Check if the main server is online"""
    try:
        response = requests.get(MAIN_SERVER_URL, timeout=10)
        if response.status_code == 200:
            return True
        return False
    except requests.exceptions.RequestException as e:
        print(f"[{datetime.now()}] Server check failed: {e}")
        return False


def trigger_offline():
    """Notify downtime tracker that server is offline"""
    try:
        response = requests.post(f'{DOWNTIME_TRACKER_URL}/trigger-offline', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"[{datetime.now()}] ✗ Server OFFLINE - Downtime tracking started")
            print(f"    Offline since: {data.get('offline_since')}")
        return True
    except Exception as e:
        print(f"[{datetime.now()}] Failed to trigger offline: {e}")
        return False


def trigger_online():
    """Notify downtime tracker that server is back online"""
    try:
        response = requests.post(f'{DOWNTIME_TRACKER_URL}/trigger-online', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"[{datetime.now()}] ✓ Server ONLINE - Downtime tracking stopped")
            print(f"    Downtime duration: {data.get('downtime_duration_seconds', 0):.0f}s")
            print(f"    Total downtime: {data.get('total_downtime_seconds', 0):.0f}s")
        return True
    except Exception as e:
        print(f"[{datetime.now()}] Failed to trigger online: {e}")
        return False


def main():
    """Main monitoring loop"""
    global last_status
    
    print(f"[{datetime.now()}] Starting server monitor...")
    print(f"  Main server: {MAIN_SERVER_URL}")
    print(f"  Downtime tracker: {DOWNTIME_TRACKER_URL}")
    print(f"  Check interval: {CHECK_INTERVAL}s")
    print("-" * 60)
    
    while True:
        try:
            current_status = check_server_status()
            
            # Detect status change
            if last_status is not None and current_status != last_status:
                if not current_status:
                    # Server went offline
                    trigger_offline()
                else:
                    # Server came back online
                    trigger_online()
            
            # Update last status
            last_status = current_status
            
            # Wait before next check
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print(f"\n[{datetime.now()}] Monitor stopped by user")
            break
        except Exception as e:
            print(f"[{datetime.now()}] Unexpected error: {e}")
            time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    main()
