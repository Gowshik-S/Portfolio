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
    'total_downtime_seconds': 0.0  # Accumulated downtime
}


@app.route('/api/downtime/status', methods=['GET'])
@cross_origin()  # Allow CORS only for this GET endpoint
def get_downtime_status():
    """
    Get current downtime status.
    Returns the current downtime in seconds if offline, or 0 if online.
    """
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
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    else:
        return jsonify({
            'is_offline': False,
            'current_downtime_seconds': 0,
            'total_downtime_seconds': downtime_tracker['total_downtime_seconds'],
            'offline_since': None,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })



@app.route('/api/downtime/trigger-offline', methods=['POST'])
def trigger_offline():
    """
    Trigger when the main server goes offline.
    Call this endpoint when you detect the server is down.
    """
    if not downtime_tracker['is_offline']:
        downtime_tracker['is_offline'] = True
        downtime_tracker['offline_since'] = datetime.now(timezone.utc).isoformat()
        
        return jsonify({
            'status': 'success',
            'message': 'Downtime tracking started',
            'offline_since': downtime_tracker['offline_since']
        })
    else:
        return jsonify({
            'status': 'already_offline',
            'message': 'Server is already marked as offline',
            'offline_since': downtime_tracker['offline_since']
        })


@app.route('/api/downtime/trigger-online', methods=['POST'])
def trigger_online():
    """
    Trigger when the main server comes back online.
    Call this endpoint when you detect the server is back up.
    """
    if downtime_tracker['is_offline'] and downtime_tracker['offline_since']:
        # Calculate the downtime for this outage
        offline_since = datetime.fromisoformat(downtime_tracker['offline_since'])
        downtime_duration = (datetime.now(timezone.utc) - offline_since).total_seconds()
        
        # Add to total downtime
        downtime_tracker['total_downtime_seconds'] += downtime_duration
        
        # Reset offline status
        downtime_tracker['is_offline'] = False
        previous_offline_since = downtime_tracker['offline_since']
        downtime_tracker['offline_since'] = None
        
        return jsonify({
            'status': 'success',
            'message': 'Server is back online',
            'downtime_duration_seconds': downtime_duration,
            'total_downtime_seconds': downtime_tracker['total_downtime_seconds'],
            'was_offline_since': previous_offline_since
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
    """
    downtime_tracker['is_offline'] = False
    downtime_tracker['offline_since'] = None
    downtime_tracker['total_downtime_seconds'] = 0.0
    
    return jsonify({
        'status': 'success',
        'message': 'Downtime tracker has been reset'
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
