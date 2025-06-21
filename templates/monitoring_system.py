import cv2
import mediapipe as mp
import numpy as np
import time
import threading
from datetime import datetime
import json
from flask import Flask, render_template, Response, jsonify
from flask_socketio import SocketIO, emit
import base64

class CheatingDetectionSystem:
    def __init__(self):
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_hands = mp.solutions.hands
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Initialize MediaPipe models
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=1, min_detection_confidence=0.5
        )
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1, min_detection_confidence=0.5, min_tracking_confidence=0.5
        )
        self.hands = self.mp_hands.Hands(
            max_num_hands=2, min_detection_confidence=0.7, min_tracking_confidence=0.5
        )
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5, min_tracking_confidence=0.5
        )
        
        # Detection thresholds and counters
        self.face_away_threshold = 2.0  # seconds
        self.multiple_faces_threshold = 3.0  # seconds
        self.phone_usage_threshold = 2.0  # seconds
        self.no_person_threshold = 3.0  # seconds
        
        # Violation tracking
        self.violations = {
            'face_away': {'count': 0, 'last_time': 0, 'active': False},
            'multiple_faces': {'count': 0, 'last_time': 0, 'active': False},
            'phone_usage': {'count': 0, 'last_time': 0, 'active': False},
            'no_person': {'count': 0, 'last_time': 0, 'active': False},
            'looking_down': {'count': 0, 'last_time': 0, 'active': False}
        }
        
        # Alert system
        self.alerts = []
        self.is_monitoring = False
        self.cap = None
        
    def start_monitoring(self, camera_index=0):
        """Start the monitoring system"""
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            raise ValueError("Could not open camera")
        
        self.is_monitoring = True
        print("Monitoring started...")
        
    def stop_monitoring(self):
        """Stop the monitoring system"""
        self.is_monitoring = False
        if self.cap:
            self.cap.release()
        print("Monitoring stopped.")
        
    def detect_face_away(self, frame, face_results):
        """Detect if person is looking away from screen"""
        if not face_results.multi_face_landmarks:
            return True
            
        for face_landmarks in face_results.multi_face_landmarks:
            # Get nose tip position
            nose_tip = face_landmarks.landmark[1]  # Nose tip
            h, w, _ = frame.shape
            
            # Calculate face orientation based on nose position
            nose_x = nose_tip.x * w
            center_x = w / 2
            
            # If nose is too far from center, person might be looking away
            if abs(nose_x - center_x) > w * 0.3:
                return True
        return False
    
    def detect_multiple_faces(self, frame, face_results):
        """Detect multiple faces in frame"""
        if face_results.multi_face_landmarks:
            return len(face_results.multi_face_landmarks) > 1
        return False
    
    def detect_phone_usage(self, frame, hands_results):
        """Detect potential phone usage based on hand positions"""
        if not hands_results.multi_hand_landmarks:
            return False
            
        for hand_landmarks in hands_results.multi_hand_landmarks:
            # Check if hands are in typical phone-holding position
            wrist = hand_landmarks.landmark[0]
            thumb_tip = hand_landmarks.landmark[4]
            index_tip = hand_landmarks.landmark[8]
            
            h, w, _ = frame.shape
            
            # Convert to pixel coordinates
            wrist_y = wrist.y * h
            thumb_y = thumb_tip.y * h
            index_y = index_tip.y * h
            
            # Check if hands are in lower part of frame (typical phone position)
            if wrist_y > h * 0.7 and thumb_y > h * 0.7 and index_y > h * 0.7:
                return True
        return False
    
    def detect_looking_down(self, frame, face_results):
        """Detect if person is looking down (possibly at phone/notes)"""
        if not face_results.multi_face_landmarks:
            return False
            
        for face_landmarks in face_results.multi_face_landmarks:
            # Get key facial landmarks
            nose_tip = face_landmarks.landmark[1]
            left_eye = face_landmarks.landmark[33]
            right_eye = face_landmarks.landmark[263]
            
            h, w, _ = frame.shape
            
            # Calculate head tilt
            eye_center_y = (left_eye.y + right_eye.y) / 2 * h
            nose_y = nose_tip.y * h
            
            # If eyes are significantly lower than nose, person might be looking down
            if nose_y < eye_center_y - h * 0.05:
                return True
        return False
    
    def detect_no_person(self, frame, face_results):
        """Detect if no person is visible"""
        return not face_results.multi_face_landmarks
    
    def add_violation(self, violation_type, frame):
        """Add a violation to the tracking system"""
        current_time = time.time()
        violation = self.violations[violation_type]
        
        if not violation['active']:
            violation['active'] = True
            violation['last_time'] = current_time
        elif current_time - violation['last_time'] > self.get_threshold(violation_type):
            violation['count'] += 1
            violation['last_time'] = current_time
            
            # Create alert
            alert = {
                'type': violation_type,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'count': violation['count'],
                'message': self.get_violation_message(violation_type)
            }
            self.alerts.append(alert)
            print(f"ALERT: {alert['message']}")
            
    def get_threshold(self, violation_type):
        """Get threshold for violation type"""
        thresholds = {
            'face_away': self.face_away_threshold,
            'multiple_faces': self.multiple_faces_threshold,
            'phone_usage': self.phone_usage_threshold,
            'no_person': self.no_person_threshold,
            'looking_down': self.face_away_threshold
        }
        return thresholds.get(violation_type, 2.0)
    
    def get_violation_message(self, violation_type):
        """Get human-readable message for violation type"""
        messages = {
            'face_away': 'Student is looking away from screen',
            'multiple_faces': 'Multiple people detected in frame',
            'phone_usage': 'Potential phone usage detected',
            'no_person': 'No person detected in frame',
            'looking_down': 'Student appears to be looking down'
        }
        return messages.get(violation_type, 'Unknown violation')
    
    def reset_violation(self, violation_type):
        """Reset violation tracking"""
        if violation_type in self.violations:
            self.violations[violation_type]['active'] = False
    
    def process_frame(self, frame):
        """Process a single frame for cheating detection"""
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Run detections
        face_results = self.face_mesh.process(rgb_frame)
        hands_results = self.hands.process(rgb_frame)
        pose_results = self.pose.process(rgb_frame)
        
        # Check for violations
        if self.detect_face_away(frame, face_results):
            self.add_violation('face_away', frame)
        else:
            self.reset_violation('face_away')
            
        if self.detect_multiple_faces(frame, face_results):
            self.add_violation('multiple_faces', frame)
        else:
            self.reset_violation('multiple_faces')
            
        if self.detect_phone_usage(frame, hands_results):
            self.add_violation('phone_usage', frame)
        else:
            self.reset_violation('phone_usage')
            
        if self.detect_looking_down(frame, face_results):
            self.add_violation('looking_down', frame)
        else:
            self.reset_violation('looking_down')
            
        if self.detect_no_person(frame, face_results):
            self.add_violation('no_person', frame)
        else:
            self.reset_violation('no_person')
        
        # Draw detection results on frame
        annotated_frame = self.draw_detections(frame, face_results, hands_results, pose_results)
        
        return annotated_frame
    
    def draw_detections(self, frame, face_results, hands_results, pose_results):
        """Draw detection results on frame"""
        annotated_frame = frame.copy()
        
        # Draw face mesh
        if face_results.multi_face_landmarks:
            for face_landmarks in face_results.multi_face_landmarks:
                self.mp_drawing.draw_landmarks(
                    annotated_frame, face_landmarks, self.mp_face_mesh.FACEMESH_TESSELATION,
                    landmark_drawing_spec=None, connection_drawing_spec=self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=1)
                )
        
        # Draw hand landmarks
        if hands_results.multi_hand_landmarks:
            for hand_landmarks in hands_results.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    annotated_frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2, circle_radius=2),
                    self.mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2)
                )
        
        # Draw pose landmarks
        if pose_results.pose_landmarks:
            self.mp_drawing.draw_landmarks(
                annotated_frame, pose_results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS,
                self.mp_drawing.DrawingSpec(color=(0, 255, 255), thickness=2, circle_radius=2),
                self.mp_drawing.DrawingSpec(color=(255, 255, 0), thickness=2)
            )
        
        # Draw violation status
        self.draw_violation_status(annotated_frame)
        
        return annotated_frame
    
    def draw_violation_status(self, frame):
        """Draw current violation status on frame"""
        h, w, _ = frame.shape
        y_offset = 30
        
        for violation_type, data in self.violations.items():
            if data['active']:
                color = (0, 0, 255)  # Red for active violations
                text = f"{violation_type.upper()}: ACTIVE"
            else:
                color = (0, 255, 0)  # Green for no violations
                text = f"{violation_type.upper()}: OK"
            
            cv2.putText(frame, text, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            y_offset += 25
    
    def get_alerts(self):
        """Get current alerts"""
        return self.alerts.copy()
    
    def clear_alerts(self):
        """Clear all alerts"""
        self.alerts.clear()
    
    def get_violation_stats(self):
        """Get violation statistics"""
        stats = {}
        for violation_type, data in self.violations.items():
            stats[violation_type] = {
                'count': data['count'],
                'active': data['active']
            }
        return stats

# Global instance
monitoring_system = CheatingDetectionSystem() 