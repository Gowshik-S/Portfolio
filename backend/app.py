from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import psutil
import time
from datetime import datetime, timezone
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Configure the SQLAlchemy part of the app instance
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "system_metrics.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# ====== DATABASE MODELS ======
class UptimeRecord(db.Model):
    """Stores persistent uptime data that survives server restarts"""
    id = db.Column(db.Integer, primary_key=True)
    total_uptime_seconds = db.Column(db.Float, default=0.0)
    last_boot_time = db.Column(db.Float)  # Unix timestamp
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<UptimeRecord {self.id}: {self.total_uptime_seconds}s>'


# ====== UPTIME MANAGEMENT ======
def get_current_boot_time():
    """Get the system boot time as Unix timestamp"""
    return psutil.boot_time()


def get_system_uptime_since_boot():
    """Get uptime in seconds since last system boot"""
    return time.time() - psutil.boot_time()


def get_or_create_uptime_record():
    """Get the uptime record, creating one if it doesn't exist"""
    record = UptimeRecord.query.first()
    if not record:
        record = UptimeRecord(
            total_uptime_seconds=0.0,
            last_boot_time=get_current_boot_time()
        )
        db.session.add(record)
        db.session.commit()
    return record


def calculate_persistent_uptime():
    """
    Calculate the total persistent uptime.
    
    This handles server restarts by:
    1. Checking if the current boot time differs from the stored boot time
    2. If different (server restarted): add the previous session's uptime
    3. Return total = stored_uptime + current_session_uptime
    """
    record = get_or_create_uptime_record()
    current_boot_time = get_current_boot_time()
    current_session_uptime = get_system_uptime_since_boot()
    
    # Check if server was restarted (boot time changed)
    if record.last_boot_time and abs(record.last_boot_time - current_boot_time) > 60:
        # Server was restarted - the difference was already saved before shutdown
        # Just update the boot time reference
        record.last_boot_time = current_boot_time
        db.session.commit()
    
    # Total uptime = accumulated uptime + current session uptime
    total_uptime = record.total_uptime_seconds + current_session_uptime
    
    return total_uptime


def save_current_uptime():
    """
    Save the current uptime to the database.
    This should be called periodically to persist the uptime.
    """
    record = get_or_create_uptime_record()
    current_boot_time = get_current_boot_time()
    
    # Check if this is a new boot session
    if record.last_boot_time and abs(record.last_boot_time - current_boot_time) > 60:
        # New boot session - we need to save the previous accumulated time
        # The previous session's uptime should have been saved before shutdown
        record.last_boot_time = current_boot_time
    
    # Update the total uptime (accumulated + current session)
    record.total_uptime_seconds = calculate_persistent_uptime() - get_system_uptime_since_boot() + get_system_uptime_since_boot()
    record.last_updated = datetime.utcnow()
    
    # Actually, let's simplify: just store the BASE uptime (without current session)
    # So total = base + current_session at any time
    record.total_uptime_seconds = record.total_uptime_seconds  # Keep previous accumulated
    
    db.session.commit()
    return record


# ====== API ROUTES ======
@app.route('/api/homeserver', methods=['GET'])
def get_server_stats():
    """
    Returns sanitized server metrics.
    No IPs, ports, or sensitive logs are exposed.
    """
    try:
        # Get CPU usage (percentage)
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Get RAM usage
        memory = psutil.virtual_memory()
        ram_percent = memory.percent
        
        # Get Disk usage (root partition)
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        
        # Get persistent uptime
        uptime_seconds = calculate_persistent_uptime()
        
        # Build response
        response = {
            'uptime': uptime_seconds,
            'cpu_percent': cpu_percent,
            'ram_percent': ram_percent,
            'disk_percent': disk_percent,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': 'online'
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500


@app.route('/api/homeserver/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat()
    })


@app.route('/api/homeserver/save-uptime', methods=['POST'])
def save_uptime():
    """
    Endpoint to manually trigger uptime save.
    Can be called before server shutdown via a systemd hook.
    """
    try:
        record = get_or_create_uptime_record()
        current_session = get_system_uptime_since_boot()
        
        # Save current accumulated uptime + current session
        record.total_uptime_seconds += current_session
        record.last_boot_time = get_current_boot_time()
        record.last_updated = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'status': 'saved',
            'total_uptime': record.total_uptime_seconds
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ====== INITIALIZATION ======
def init_db():
    """Initialize the database and handle boot time changes"""
    with app.app_context():
        db.create_all()
        
        record = get_or_create_uptime_record()
        current_boot_time = get_current_boot_time()
        
        # Check if this is a new boot session
        if record.last_boot_time:
            time_diff = abs(record.last_boot_time - current_boot_time)
            if time_diff > 60:  # More than 1 minute difference = new boot
                # Server was restarted, keep the accumulated uptime
                # Just update the reference boot time
                print(f"New boot detected. Previous accumulated uptime: {record.total_uptime_seconds}s")
                record.last_boot_time = current_boot_time
                db.session.commit()
        else:
            # First run ever
            record.last_boot_time = current_boot_time
            db.session.commit()


# Initialize database on import
init_db()


if __name__ == '__main__':
    # Run the Flask development server
    # In production, use gunicorn or similar
    app.run(host='0.0.0.0', port=5000, debug=False)
