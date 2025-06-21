from flask import Flask, render_template, Response, jsonify, request
from flask_socketio import SocketIO, emit
import cv2
import threading
import time
import base64
from monitoring_system import monitoring_system

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
# Use eventlet for async_mode for better compatibility
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")

# Global variables
is_streaming = False

def generate_frames():
    """Generate video frames for streaming"""
    global is_streaming
    print("Generate frames task started.")
    
    if not monitoring_system.cap or not monitoring_system.cap.isOpened():
        monitoring_system.start_monitoring()
    
    while is_streaming:
        if monitoring_system.cap and monitoring_system.cap.isOpened():
            ret, frame = monitoring_system.cap.read()
            if not ret:
                print("Failed to read frame from camera. Breaking loop.")
                break
                
            # Re-enable processing
            processed_frame = monitoring_system.process_frame(frame)
            
            ret, buffer = cv2.imencode('.jpg', processed_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if not ret:
                continue
                
            frame_data = base64.b64encode(buffer).decode('utf-8')
            
            # Use socketio.emit in a background task-friendly way
            socketio.emit('video_frame', {'frame': frame_data})
            
            # Use socketio.sleep for cooperative yielding
            socketio.sleep(0.033)
        else:
            socketio.sleep(0.1)
    
    print("Generate frames task finished.")
    monitoring_system.stop_monitoring()

def alert_monitor():
    """Monitor for new alerts and send them via WebSocket"""
    last_alert_count = 0
    
    while is_streaming:
        current_alerts = monitoring_system.get_alerts()
        
        if len(current_alerts) > last_alert_count:
            new_alerts = current_alerts[last_alert_count:]
            for alert in new_alerts:
                socketio.emit('new_alert', alert)
            last_alert_count = len(current_alerts)
        
        socketio.sleep(1)
    print("Alert monitor task finished.")

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/start_monitoring')
def start_monitoring():
    """Start the monitoring system"""
    global is_streaming
    
    if not is_streaming:
        is_streaming = True
        # Use socketio's background task manager
        socketio.start_background_task(target=generate_frames)
        socketio.start_background_task(target=alert_monitor)
        return jsonify({'status': 'success', 'message': 'Monitoring started'})
    else:
        return jsonify({'status': 'error', 'message': 'Monitoring already running'})

@app.route('/stop_monitoring')
def stop_monitoring():
    """Stop the monitoring system"""
    global is_streaming
    is_streaming = False
    return jsonify({'status': 'success', 'message': 'Monitoring stopped'})

@app.route('/get_alerts')
def get_alerts():
    """Get current alerts"""
    alerts = monitoring_system.get_alerts()
    return jsonify({'alerts': alerts})

@app.route('/clear_alerts')
def clear_alerts():
    """Clear all alerts"""
    monitoring_system.clear_alerts()
    return jsonify({'status': 'success', 'message': 'Alerts cleared'})

@app.route('/get_stats')
def get_stats():
    """Get violation statistics"""
    stats = monitoring_system.get_violation_stats()
    return jsonify({'stats': stats})

@app.route('/update_threshold', methods=['POST'])
def update_threshold():
    """Update detection thresholds"""
    try:
        data = request.get_json()
        violation_type = data.get('violation_type')
        threshold = data.get('threshold')
        
        if violation_type and threshold is not None:
            threshold = float(threshold)
            if violation_type == 'face_away':
                monitoring_system.face_away_threshold = threshold
            elif violation_type == 'multiple_faces':
                monitoring_system.multiple_faces_threshold = threshold
            elif violation_type == 'phone_usage':
                monitoring_system.phone_usage_threshold = threshold
            elif violation_type == 'no_person':
                monitoring_system.no_person_threshold = threshold
            
            return jsonify({'status': 'success', 'message': f'Threshold updated for {violation_type}'})
        return jsonify({'status': 'error', 'message': 'Invalid data'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    emit('connection_status', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

if __name__ == '__main__':
    print("Starting Exam Monitoring System...")
    print("Access the web interface at: http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000) 