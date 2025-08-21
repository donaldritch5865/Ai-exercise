# exercises/bicep_curl.py

import streamlit as st
import cv2
import mediapipe as mp
import numpy as np
import time

# --- Helper Functions ---
def calculate_angle(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians*180.0/np.pi)
    return 360-angle if angle > 180 else angle

def check_bicep_curl_form(landmarks, elbow_angle, stage):
    feedback = []
    mp_pose = mp.solutions.pose

    shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
    elbow = landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value]
    hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]

    if stage == "up" and elbow_angle > 45:
        feedback.append("Lift higher for a full contraction!")
    if stage == "down" and elbow_angle < 150:
        feedback.append("Lower your arm completely!")
    if abs(shoulder.x - hip.x) > 0.08:
        feedback.append("Avoid swinging your body.")
    if (elbow.x - shoulder.x) > 0.08:
        feedback.append("Keep elbows tucked in.")

    return feedback

# --- Main Workout Function ---
def run():
    st.title("💪 Bicep Curl Tracker")

    if 'workout_started' not in st.session_state:
        st.session_state.update({
            'workout_started': False, 'countdown_finished': False,
            'counter': 0, 'stage': None, 'start_time': 0,
            'good_reps': 0, 'feedback_list': []
        })

    if not st.session_state.workout_started:
        if not st.session_state.get('start_countdown', False):
            st.subheader("Get Ready!")
            st.write("Stand straight, ensure your upper body is clearly visible in the camera.")

            col1, col2 = st.columns(2)
            if col1.button("▶ Start Workout"):
                st.session_state.start_countdown = True
                st.rerun()
            if col2.button("🏠 Back to Home"):
                st.session_state.page = 'home'
                for key in list(st.session_state.keys()):
                    if key != 'page': del st.session_state[key]
                st.rerun()
        else:
            countdown_placeholder = st.empty()
            for i in range(3, 0, -1):
                countdown_placeholder.markdown(f"<h1 style='text-align:center;font-size:4em'>{i}</h1>", unsafe_allow_html=True)
                time.sleep(1)
            countdown_placeholder.markdown("<h1 style='text-align:center;font-size:4em'>GO!</h1>", unsafe_allow_html=True)
            time.sleep(1)

            st.session_state.workout_started = True
            st.session_state.start_time = time.time()
            del st.session_state['start_countdown']
            st.rerun()

    else:
        if st.button("⏹ End Workout"):
            st.session_state.workout_duration = time.time() - st.session_state.start_time
            st.session_state.page = 'summary'
            st.session_state.workout_started = False
            st.rerun()

        # Display Metrics at Top
        col1, col2, col3 = st.columns(3)
        col1.metric("Reps", st.session_state.counter)
        col2.metric("Stage", st.session_state.stage if st.session_state.stage else "-")
        col3.metric("Good Reps", st.session_state.good_reps)

        # Larger Camera Feed (centered, ~80% width)
        col_center = st.columns([1,5,1])[1]
        FRAME_WINDOW = col_center.image([], channels="BGR", use_container_width=True)

        mp_drawing, mp_pose = mp.solutions.drawing_utils, mp.solutions.pose
        cap = cv2.VideoCapture(0)

        with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
            while cap.isOpened() and st.session_state.workout_started:
                ret, frame = cap.read()
                if not ret:
                    st.error("❌ Could not access webcam.")
                    break

                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = pose.process(image)
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

                try:
                    landmarks = results.pose_landmarks.landmark
                    shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                                landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                    elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
                             landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
                    wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,
                             landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]

                    elbow_angle = calculate_angle(shoulder, elbow, wrist)

                    if elbow_angle > 160:
                        st.session_state.stage = "down"
                    if elbow_angle < 30 and st.session_state.stage == 'down':
                        st.session_state.stage = "up"
                        st.session_state.counter += 1
                        if not st.session_state.feedback_list:
                            st.session_state.good_reps += 1

                    st.session_state.feedback_list = check_bicep_curl_form(landmarks, elbow_angle, st.session_state.stage)
                except:
                    pass

                if results.pose_landmarks:
                    mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

                FRAME_WINDOW.image(image, channels='BGR', use_container_width=True)

        cap.release()
