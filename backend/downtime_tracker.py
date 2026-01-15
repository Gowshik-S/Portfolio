from flask import Flask, jsonify
from flask_cors import CORS, cross_origin
from datetime import datetime, timezone
import os

app = Flask(__name__)

# Don't enable CORS globally - we'll add it selectively
# CORS(app)  # REMOVED

# In-memory storage (for simple deployment)
# For production, consider using Redis or a database
downtime_tracker = {
    'is_offline': False,
    'offline_since': None,  # ISO timestamp when server went offline
    'total_downtime_seconds': 0.0,  # Accumulated downtime
    # Last outage information
    'last_outage_start': None,  # ISO timestamp when last outage started
    'last_outage_end': None,    # ISO timestamp when last outage ended
    'last_outage_duration_seconds': 0.0  # Duration of last completed outage
}


@app.route('/api/downtime/status', methods=['GET'])
@cross_origin()  # Allow CORS only for this GET endpoint
def get_downtime_status():
    """
    Get current downtime status.
    Returns the current downtime in seconds if offline, or 0 if online.
    Also includes last outage information when server is online.
    """
    # Build last outage info (available in both states)
    last_outage_info = {
        'last_outage_start': downtime_tracker['last_outage_start'],
        'last_outage_end': downtime_tracker['last_outage_end'],
        'last_outage_duration_seconds': downtime_tracker['last_outage_duration_seconds']
    }
    
    if downtime_tracker['is_offline'] and downtime_tracker['offline_since']:
        # Calculate current downtime
        offline_since = datetime.fromisoformat(downtime_tracker['offline_since'])
        current_downtime = (datetime.now(timezone.utc) - offline_since).total_seconds()
        total_downtime = downtime_tracker['total_downtime_seconds'] + current_downtime
        
        return jsonify({
            'is_offline': True,
            'current_downtime_seconds': current_downtime,
            'total_downtime_seconds': total_downtime,
            'offline_since': downtime_tracker['offline_since'],
            'timestamp': datetime.now(timezone.utc).isoformat(),
            **last_outage_info
        })
    else:
        return jsonify({
            'is_offline': False,
            'current_downtime_seconds': 0,
            'total_downtime_seconds': downtime_tracker['total_downtime_seconds'],
            'offline_since': None,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            **last_outage_info
        })



@app.route('/api/downtime/trigger-offline', methods=['POST'])
@cross_origin()  # Allow anyone to trigger offline (server is down, can't POST itself)
def trigger_offline():
    """
    Trigger when the main server goes offline.
    Anyone can call this, but it will only start tracking ONCE.
    Once offline, it won't reset until trigger-online is called.
    """
    if not downtime_tracker['is_offline']:
        # First time going offline - start tracking
        downtime_tracker['is_offline'] = True
        downtime_tracker['offline_since'] = datetime.now(timezone.utc).isoformat()
        
        return jsonify({
            'status': 'success',
            'message': 'Downtime tracking started',
            'offline_since': downtime_tracker['offline_since']
        })
    else:
        # Already offline - don't reset the timer
        return jsonify({
            'status': 'already_offline',
            'message': 'Server is already marked as offline. Downtime continues.',
            'offline_since': downtime_tracker['offline_since']
        })



@app.route('/api/downtime/trigger-online', methods=['POST'])
def trigger_online():
    """
    Trigger when the main server comes back online.
    Call this endpoint when you detect the server is back up.
    Saves the outage details for later reference.
    """
    if downtime_tracker['is_offline'] and downtime_tracker['offline_since']:
        # Calculate the downtime for this outage
        offline_since = datetime.fromisoformat(downtime_tracker['offline_since'])
        now = datetime.now(timezone.utc)
        downtime_duration = (now - offline_since).total_seconds()
        
        # Add to total downtime
        downtime_tracker['total_downtime_seconds'] += downtime_duration
        
        # Save last outage information
        downtime_tracker['last_outage_start'] = downtime_tracker['offline_since']
        downtime_tracker['last_outage_end'] = now.isoformat()
        downtime_tracker['last_outage_duration_seconds'] = downtime_duration
        
        # Reset offline status
        downtime_tracker['is_offline'] = False
        previous_offline_since = downtime_tracker['offline_since']
        downtime_tracker['offline_since'] = None
        
        return jsonify({
            'status': 'success',
            'message': 'Server is back online',
            'downtime_duration_seconds': downtime_duration,
            'total_downtime_seconds': downtime_tracker['total_downtime_seconds'],
            'was_offline_since': previous_offline_since,
            'last_outage_start': downtime_tracker['last_outage_start'],
            'last_outage_end': downtime_tracker['last_outage_end']
        })
    else:
        return jsonify({
            'status': 'already_online',
            'message': 'Server is already marked as online'
        })


@app.route('/api/downtime/reset', methods=['POST'])
def reset_downtime():
    """
    Reset all downtime tracking.
    Use this to start fresh or for maintenance.
    Clears both current and last outage information.
    """
    downtime_tracker['is_offline'] = False
    downtime_tracker['offline_since'] = None
    downtime_tracker['total_downtime_seconds'] = 0.0
    # Also reset last outage info
    downtime_tracker['last_outage_start'] = None
    downtime_tracker['last_outage_end'] = None
    downtime_tracker['last_outage_duration_seconds'] = 0.0
    
    return jsonify({
        'status': 'success',
        'message': 'Downtime tracker has been reset (including last outage info)'
    })


@app.route('/health', methods=['GET'])
@cross_origin()  # Allow CORS for health check
def health_check():
    """Health check endpoint for Render"""
    return jsonify({
        'status': 'healthy',
        'service': 'downtime-tracker',
        'timestamp': datetime.now(timezone.utc).isoformat()
    })



if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)
