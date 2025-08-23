from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import cv2
import json
import threading
import time
import importlib.util
import os
import sys
from pathlib import Path

app = Flask(__name__)
CORS(app)

# Global variables for video processing
current_exercise = None
exercise_processor = None
video_capture = None
processing_thread = None
is_processing = False
frame_data = {}

class ExerciseProcessor:
    def __init__(self, exercise_name):
        self.exercise_name = exercise_name
        self.exercise_module = self._load_exercise_module(exercise_name)
        self.reset_state()
    
    def _load_exercise_module(self, exercise_name):
        """Dynamically load exercise module"""
        exercise_path = Path(__file__).parent / "exercises" / f"{exercise_name}.py"
        if not exercise_path.exists():
            raise ValueError(f"Exercise {exercise_name} not found")
        
        spec = importlib.util.spec_from_file_location(exercise_name, exercise_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    
    def reset_state(self):
        """Reset exercise state"""
        self.counter = 0
        self.stage = 'down' if self.exercise_name != 'plank' else None
        self.good_reps = 0
        self.feedback_list = []
        self.start_time = time.time()
        self.good_form_time = 0 if self.exercise_name == 'plank' else None
        self.last_frame_time = time.time() if self.exercise_name == 'plank' else None
    
    def process_frame(self, frame, results):
        """Process frame using exercise-specific logic"""
        try:
            if hasattr(self.exercise_module, 'calculate_angle'):
                calculate_angle = self.exercise_module.calculate_angle
            else:
                # Fallback angle calculation
                import numpy as np
                def calculate_angle(a, b, c):
                    a, b, c = np.array(a), np.array(b), np.array(c)
                    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
                    angle = np.abs(radians*180.0/np.pi)
                    return 360-angle if angle > 180 else angle
            
            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark
                
                # Exercise-specific processing
                if self.exercise_name == 'bicep_curl':
                    self._process_bicep_curl(landmarks, calculate_angle)
                elif self.exercise_name == 'squats':
                    self._process_squats(landmarks, calculate_angle)
                elif self.exercise_name == 'overhead_press':
                    self._process_overhead_press(landmarks, calculate_angle)
                elif self.exercise_name == 'lateral_raises':
                    self._process_lateral_raises(landmarks, calculate_angle)
                elif self.exercise_name == 'lunges':
                    self._process_lunges(landmarks, calculate_angle)
                elif self.exercise_name == 'pullups':
                    self._process_pullups(landmarks, calculate_angle)
                elif self.exercise_name == 'pushups':
                    self._process_pushups(landmarks, calculate_angle)
                elif self.exercise_name == 'glute_bridges':
                    self._process_glute_bridges(landmarks, calculate_angle)
                elif self.exercise_name == 'crunches':
                    self._process_crunches(landmarks, calculate_angle)
                elif self.exercise_name == 'plank':
                    self._process_plank(landmarks, calculate_angle)
                
        except Exception as e:
            print(f"Error processing frame: {e}")
    
    def _process_bicep_curl(self, landmarks, calculate_angle):
        import mediapipe as mp
        mp_pose = mp.solutions.pose
        
        shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
        elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
        wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
        
        elbow_angle = calculate_angle(shoulder, elbow, wrist)
        self.feedback_list = self.exercise_module.check_bicep_curl_form(landmarks, elbow_angle, self.stage)
        
        if elbow_angle > 160:
            self.stage = "down"
        if elbow_angle < 30 and self.stage == 'down':
            self.stage = "up"
            self.counter += 1
            if not self.exercise_module.check_bicep_curl_form(landmarks, elbow_angle, "up"):
                self.good_reps += 1
    
    def _process_squats(self, landmarks, calculate_angle):
        import mediapipe as mp
        mp_pose = mp.solutions.pose
        
        hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
        knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
        ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
        shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
        
        knee_angle = calculate_angle(hip, knee, ankle)
        hip_angle = calculate_angle(shoulder, hip, knee)
        
        self.feedback_list = self.exercise_module.check_squat_form(knee_angle, hip_angle, self.stage)
        
        if knee_angle > 160:
            self.stage = "up"
        if knee_angle < 100 and self.stage == "up":
            self.stage = "down"
            self.counter += 1
            if not self.exercise_module.check_squat_form(knee_angle, hip_angle, "down"):
                self.good_reps += 1
    
    def _process_plank(self, landmarks, calculate_angle):
        import mediapipe as mp
        mp_pose = mp.solutions.pose
        
        shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
        hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
        ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
        
        hip_angle = calculate_angle(shoulder, hip, ankle)
        self.feedback_list = self.exercise_module.check_plank_form(hip_angle)
        
        good_form = not self.feedback_list
        now = time.time()
        if good_form:
            self.good_form_time += now - self.last_frame_time
        self.last_frame_time = now
    
    # Add other exercise processing methods...
    def _process_overhead_press(self, landmarks, calculate_angle):
        import mediapipe as mp
        mp_pose = mp.solutions.pose
        
        shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
        elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
        wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
        hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
        
        elbow_angle = calculate_angle(shoulder, elbow, wrist)
        shoulder_angle = calculate_angle(hip, shoulder, elbow)
        
        self.feedback_list = self.exercise_module.check_overhead_press_form(elbow_angle, shoulder_angle, self.stage)
        
        if elbow_angle < 90:
            self.stage = "down"
        if elbow_angle > 160 and self.stage == "down":
            self.stage = "up"
            self.counter += 1
            if not self.exercise_module.check_overhead_press_form(elbow_angle, shoulder_angle, "up"):
                self.good_reps += 1
    
    def _process_lateral_raises(self, landmarks, calculate_angle):
        import mediapipe as mp
        mp_pose = mp.solutions.pose
        
        shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
        elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
        wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
        hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
        
        shoulder_angle = calculate_angle(hip, shoulder, elbow)
        elbow_angle = calculate_angle(shoulder, elbow, wrist)
        
        self.feedback_list = self.exercise_module.check_lateral_raise_form(shoulder_angle, elbow_angle, self.stage)
        
        if shoulder_angle < 30:
            self.stage = "down"
        if shoulder_angle > 70 and self.stage == "down":
            self.stage = "up"
            self.counter += 1
            if not self.exercise_module.check_lateral_raise_form(shoulder_angle, elbow_angle, "up"):
                self.good_reps += 1
    
    def _process_lunges(self, landmarks, calculate_angle):
        import mediapipe as mp
        mp_pose = mp.solutions.pose
        
        left_hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
        left_knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
        left_ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
        right_hip = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
        right_knee = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y]
        right_ankle = [landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].y]
        
        front_knee_angle = calculate_angle(left_hip, left_knee, left_ankle)
        back_knee_angle = calculate_angle(right_hip, right_knee, right_ankle)
        
        self.feedback_list = self.exercise_module.check_lunge_form(front_knee_angle, back_knee_angle, self.stage)
        
        if front_knee_angle > 160 and back_knee_angle > 160:
            self.stage = "up"
        if front_knee_angle < 100 and self.stage == "up":
            self.stage = "down"
            self.counter += 1
            if not self.exercise_module.check_lunge_form(front_knee_angle, back_knee_angle, "down"):
                self.good_reps += 1
    
    def _process_pullups(self, landmarks, calculate_angle):
        import mediapipe as mp
        mp_pose = mp.solutions.pose
        
        shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
        elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
        wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
        nose = landmarks[mp_pose.PoseLandmark.NOSE.value]
        
        elbow_angle = calculate_angle(shoulder, elbow, wrist)
        self.feedback_list = self.exercise_module.check_pullup_form(landmarks, elbow_angle, self.stage)
        
        if elbow_angle > 160:
            self.stage = "down"
        if nose.y < shoulder[1] and elbow_angle < 100 and self.stage == "down":
            self.stage = "up"
            self.counter += 1
            if not self.exercise_module.check_pullup_form(landmarks, elbow_angle, "up"):
                self.good_reps += 1
    
    def _process_pushups(self, landmarks, calculate_angle):
        import mediapipe as mp
        mp_pose = mp.solutions.pose
        
        shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
        elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
        wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
        hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
        knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
        
        elbow_angle = calculate_angle(shoulder, elbow, wrist)
        hip_angle = calculate_angle(shoulder, hip, knee)
        
        if elbow_angle > 160:
            current_stage = "up"
        elif elbow_angle < 90:
            current_stage = "down"
        else:
            current_stage = self.stage
        
        if current_stage == "down" and self.stage == "up":
            self.counter += 1
            if not self.exercise_module.check_pushup_form(elbow_angle, hip_angle, "down"):
                self.good_reps += 1
        
        self.stage = current_stage
        self.feedback_list = self.exercise_module.check_pushup_form(elbow_angle, hip_angle, current_stage)
    
    def _process_glute_bridges(self, landmarks, calculate_angle):
        import mediapipe as mp
        mp_pose = mp.solutions.pose
        
        shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
        hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
        knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
        
        hip_angle = calculate_angle(shoulder, hip, knee)
        self.feedback_list = self.exercise_module.check_glute_bridge_form(hip_angle, self.stage)
        
        if hip_angle < 150:
            self.stage = "down"
        if hip_angle > 160 and self.stage == 'down':
            self.stage = "up"
            self.counter += 1
            if not self.exercise_module.check_glute_bridge_form(hip_angle, "up"):
                self.good_reps += 1
    
    def _process_crunches(self, landmarks, calculate_angle):
        import mediapipe as mp
        mp_pose = mp.solutions.pose
        
        shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
        hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
        knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
        
        hip_angle = calculate_angle(shoulder, hip, knee)
        self.feedback_list = self.exercise_module.check_crunch_form(hip_angle, self.stage)
        
        if hip_angle > 160:
            self.stage = "down"
        if hip_angle < 150 and self.stage == 'down':
            self.stage = "up"
            self.counter += 1
            if not self.exercise_module.check_crunch_form(hip_angle, "up"):
                self.good_reps += 1
    
    def get_stats(self):
        """Get current exercise statistics"""
        elapsed_time = time.time() - self.start_time
        
        if self.exercise_name == 'plank':
            return {
                'exercise': self.exercise_name,
                'elapsed_time': int(elapsed_time),
                'good_form_time': int(self.good_form_time),
                'feedback': self.feedback_list
            }
        else:
            return {
                'exercise': self.exercise_name,
                'reps': self.counter,
                'good_reps': self.good_reps,
                'stage': self.stage,
                'elapsed_time': int(elapsed_time),
                'feedback': self.feedback_list
            }

def generate_frames():
    """Generate video frames with pose estimation"""
    global exercise_processor, video_capture, is_processing
    
    import mediapipe as mp
    mp_drawing = mp.solutions.drawing_utils
    mp_pose = mp.solutions.pose
    
    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while is_processing and video_capture and video_capture.isOpened():
            ret, frame = video_capture.read()
            if not ret:
                break
            
            # Process frame
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(image)
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            # Apply exercise-specific processing
            if exercise_processor:
                exercise_processor.process_frame(image, results)
                
                # Add feedback to frame
                y_pos = 100
                if exercise_processor.feedback_list:
                    for feedback in exercise_processor.feedback_list:
                        cv2.putText(image, feedback, (15, y_pos), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2, cv2.LINE_AA)
                        y_pos += 30
                else:
                    cv2.putText(image, "GOOD FORM", (15, y_pos), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)
            
            # Draw pose landmarks
            if results.pose_landmarks:
                mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            
            # Encode frame
            ret, buffer = cv2.imencode('.jpg', image)
            if ret:
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/api/exercises', methods=['GET'])
def get_exercises():
    """Get list of available exercises"""
    exercises = [
        {'id': 'bicep_curl', 'name': 'Bicep Curls', 'icon': '💪'},
        {'id': 'squats', 'name': 'Squats', 'icon': '🔑'},
        {'id': 'overhead_press', 'name': 'Overhead Press', 'icon': '🏋️'},
        {'id': 'lateral_raises', 'name': 'Lateral Raises', 'icon': '👉'},
        {'id': 'lunges', 'name': 'Lunges', 'icon': '🦵'},
        {'id': 'pullups', 'name': 'Pull-ups', 'icon': '🏋️'},
        {'id': 'pushups', 'name': 'Push-ups', 'icon': '🤜'},
        {'id': 'glute_bridges', 'name': 'Glute Bridges', 'icon': '🍑'},
        {'id': 'crunches', 'name': 'Crunches', 'icon': '🔥'},
        {'id': 'plank', 'name': 'Plank', 'icon': '🧘'}
    ]
    return jsonify(exercises)

@app.route('/api/start_exercise', methods=['POST'])
def start_exercise():
    """Start exercise tracking"""
    global current_exercise, exercise_processor, video_capture, is_processing
    
    data = request.get_json()
    exercise_name = data.get('exercise')
    
    if not exercise_name:
        return jsonify({'error': 'Exercise name required'}), 400
    
    try:
        # Stop current processing
        stop_exercise()
        
        # Initialize new exercise
        exercise_processor = ExerciseProcessor(exercise_name)
        current_exercise = exercise_name
        
        # Start video capture
        video_capture = cv2.VideoCapture(0)
        if not video_capture.isOpened():
            return jsonify({'error': 'Could not access webcam'}), 500
        
        is_processing = True
        
        return jsonify({'message': f'Started {exercise_name}', 'exercise': exercise_name})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stop_exercise', methods=['POST'])
def stop_exercise():
    """Stop exercise tracking"""
    global current_exercise, exercise_processor, video_capture, is_processing
    
    is_processing = False
    
    if video_capture:
        video_capture.release()
        video_capture = None
    
    stats = None
    if exercise_processor:
        stats = exercise_processor.get_stats()
    
    current_exercise = None
    exercise_processor = None
    
    return jsonify({'message': 'Exercise stopped', 'final_stats': stats})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get current exercise statistics"""
    if exercise_processor:
        return jsonify(exercise_processor.get_stats())
    return jsonify({'error': 'No active exercise'}), 400

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    if not is_processing:
        return jsonify({'error': 'No active exercise'}), 400
    
    return Response(generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'current_exercise': current_exercise})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)