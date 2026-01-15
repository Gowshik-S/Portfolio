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
    # accumulated_uptime stores the sum of all PREVIOUS sessions (not including current)
    accumulated_uptime_seconds = db.Column(db.Float, default=0.0)
    # last_session_uptime stores the uptime we last recorded for the current/previous session
    last_session_uptime = db.Column(db.Float, default=0.0)
    last_boot_time = db.Column(db.Float)  # Unix timestamp
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<UptimeRecord {self.id}: accumulated={self.accumulated_uptime_seconds}s>'


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
            accumulated_uptime_seconds=0.0,
            last_session_uptime=0.0,
            last_boot_time=get_current_boot_time()
        )
        db.session.add(record)
        db.session.commit()
    return record


def handle_boot_detection():
    """
    Check if a reboot occurred and update accumulated uptime accordingly.
    This should be called at startup.
    """
    record = get_or_create_uptime_record()
    current_boot_time = get_current_boot_time()
    
    # Check if server was restarted (boot time changed)
    if record.last_boot_time and abs(record.last_boot_time - current_boot_time) > 60:
        # Server was restarted!
        # Add the last saved session uptime to accumulated total
        record.accumulated_uptime_seconds += record.last_session_uptime
        record.last_session_uptime = 0.0  # Reset for new session
        record.last_boot_time = current_boot_time
        record.last_updated = datetime.utcnow()
        db.session.commit()
        print(f"New boot detected. Accumulated uptime updated to: {record.accumulated_uptime_seconds}s")
    
    return record


def calculate_persistent_uptime():
    """
    Calculate the total persistent uptime.
    Total = accumulated from previous sessions + current session uptime
    """
    record = get_or_create_uptime_record()
    current_session_uptime = get_system_uptime_since_boot()
    
    # Total uptime = accumulated (all previous sessions) + current session
    total_uptime = record.accumulated_uptime_seconds + current_session_uptime
    
    return total_uptime


def save_current_session_uptime():
    """
    Save the current session uptime to the database.
    This should be called periodically to ensure we don't lose data on unexpected shutdown.
    The last_session_uptime is added to accumulated when a reboot is detected.
    """
    record = get_or_create_uptime_record()
    current_session_uptime = get_system_uptime_since_boot()
    
    # Update the last session uptime (will be added to accumulated on next reboot)
    record.last_session_uptime = current_session_uptime
    record.last_updated = datetime.utcnow()
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
        
        # Get uptime values
        current_uptime = get_system_uptime_since_boot()
        total_uptime = calculate_persistent_uptime()
        
        # Save the current session uptime periodically (on each API call)
        save_current_session_uptime()
        
        # Get the record for any additional info
        record = get_or_create_uptime_record()
        # Downtime is tracked separately via the downtime tracker service
        downtime = 0.0
        
        # Build response
        response = {
            'uptime': total_uptime,  # For backward compatibility
            'current_uptime': current_uptime,
            'total_uptime': total_uptime,
            'downtime': downtime,
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
        record = save_current_session_uptime()
        total_uptime = calculate_persistent_uptime()
        
        return jsonify({
            'status': 'saved',
            'current_session_uptime': record.last_session_uptime,
            'accumulated_uptime': record.accumulated_uptime_seconds,
            'total_uptime': total_uptime
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ====== DATABASE MIGRATION ======
def migrate_database():
    """
    Handle migration from old schema to new schema.
    Old schema had: total_uptime_seconds
    New schema has: accumulated_uptime_seconds, last_session_uptime
    """
    with app.app_context():
        try:
            # Check if we need to migrate by checking for old column
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('uptime_record')]
            
            if 'total_uptime_seconds' in columns and 'accumulated_uptime_seconds' not in columns:
                # Old schema detected - need to migrate
                print("Migrating database from old schema to new schema...")
                
                # Add new columns
                with db.engine.connect() as conn:
                    conn.execute(text('ALTER TABLE uptime_record ADD COLUMN accumulated_uptime_seconds FLOAT DEFAULT 0.0'))
                    conn.execute(text('ALTER TABLE uptime_record ADD COLUMN last_session_uptime FLOAT DEFAULT 0.0'))
                    # Copy old total_uptime_seconds to accumulated_uptime_seconds
                    conn.execute(text('UPDATE uptime_record SET accumulated_uptime_seconds = total_uptime_seconds'))
                    conn.commit()
                
                print("Database migration completed!")
            elif 'accumulated_uptime_seconds' not in columns:
                # Fresh database, columns will be created by create_all()
                pass
        except Exception as e:
            print(f"Migration check error (may be normal for new DB): {e}")


# ====== INITIALIZATION ======
def init_db():
    """Initialize the database and handle boot time changes"""
    with app.app_context():
        # First, try to migrate if needed
        migrate_database()
        
        # Create tables (will create new columns if missing)
        db.create_all()
        
        # Handle boot detection - this will add previous session uptime to accumulated
        # if a reboot is detected
        handle_boot_detection()
        
        record = get_or_create_uptime_record()
        print(f"Uptime tracker initialized. Accumulated: {record.accumulated_uptime_seconds}s, Last session: {record.last_session_uptime}s")


# Initialize database on import
init_db()


if __name__ == '__main__':
    # Run the Flask development server
    # In production, use gunicorn or similar
    app.run(host='0.0.0.0', port=8487, debug=False)
