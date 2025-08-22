# exercises/squats.py

import streamlit as st
import cv2
import mediapipe as mp
import numpy as np
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase, RTCConfiguration

# --- MediaPipe and Drawing Setup ---
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# --- Helper Functions ---
def calculate_angle(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    return 360 - angle if angle > 180 else angle

def check_squat_form(knee_angle, hip_angle, stage):
    feedback = []
    if stage == "down" and knee_angle > 100:
        feedback.append("Squat deeper for full range of motion.")
    if hip_angle < 80:
        feedback.append("Keep your chest up and back straight.")
    return feedback

# --- Video Transformer Class ---
class SquatTransformer(VideoTransformerBase):
    def __init__(self):
        st.session_state.counter = 0
        st.session_state.stage = "up"
        st.session_state.feedback_list = []
        st.session_state.good_reps = 0

    def transform(self, frame):
        image = frame.to_ndarray(format="bgr24")

        # Process the frame
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = pose.process(image_rgb)
        
        is_good_form = False
        try:
            landmarks = results.pose_landmarks.landmark
            shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
            knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
            ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]

            knee_angle = calculate_angle(hip, knee, ankle)
            hip_angle = calculate_angle(shoulder, hip, knee)

            if knee_angle > 160:
                st.session_state.stage = "up"
            if knee_angle < 100 and st.session_state.stage == "up":
                st.session_state.stage = "down"
                st.session_state.counter += 1
                if not check_squat_form(knee_angle, hip_angle, "down"):
                    st.session_state.good_reps += 1
            
            st.session_state.feedback_list = check_squat_form(knee_angle, hip_angle, st.session_state.stage)
            is_good_form = not st.session_state.feedback_list
        except:
            pass

        # On-Screen Display
        y_pos = 100
        if not is_good_form:
            for feedback in st.session_state.feedback_list:
                cv2.putText(image, feedback, (15, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                y_pos += 30
        else:
            cv2.putText(image, "GOOD FORM", (15, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        if results.pose_landmarks:
            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        return image

# --- Main App Logic ---
def run():
    st.set_page_config(layout="wide")
    st.title("🏋️ Squat Tracker")

    if 'workout_started' not in st.session_state or st.session_state.get('current_exercise') != 'squats':
        st.session_state.workout_started = False
        st.session_state.current_exercise = 'squats'
    
    if not st.session_state.workout_started:
        st.header("Get Ready!")
        st.write("Make sure your full body is visible in the camera.")
        if st.button("Start Squats"):
            st.session_state.workout_started = True
            st.rerun()
    else:
        st.write("Your webcam feed is below.")
        webrtc_streamer(
            key="squats_stream",
            video_transformer_factory=SquatTransformer,
            rtc_configuration=RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]})
        )
