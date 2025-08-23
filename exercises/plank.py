# exercises/plank.py

import streamlit as st
import cv2
import mediapipe as mp
import numpy as np
import time

def calculate_angle(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    return 360 - angle if angle > 180 else angle

def check_plank_form(hip_angle):
    feedback = []
    if hip_angle < 160:
        feedback.append("Your hips are sagging. Keep your back straight!")
    elif hip_angle > 190:
        feedback.append("Your hips are too high. Keep your body flat!")
    return feedback

def run():
    st.title("🪜 Plank Tracker")

    # Initialize state robustly
    if 'workout_started' not in st.session_state or st.session_state.get('current_exercise') != 'plank':
        st.session_state.workout_started = False
        st.session_state.current_exercise = 'plank'
        st.session_state.start_time = 0
        st.session_state.good_form_time = 0
        st.session_state.feedback_list = []
        st.session_state.start_countdown = False

    # Countdown / Ready screen
    if not st.session_state.workout_started:
        if not st.session_state.get('start_countdown', False):
            st.header("Get Ready!")
            st.write("Lie down and position yourself in a straight line (elbows under shoulders).")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Start Plank"):
                    st.session_state.start_countdown = True
                    st.rerun()
            with col2:
                if st.button("Back to Home"):
                    st.session_state.page = 'home'
                    for key in list(st.session_state.keys()):
                        if key != 'page': del st.session_state[key]
                    st.rerun()
        else:
            cd = st.empty()
            for i in range(3, 0, -1):
                cd.markdown(f"<h1 style='text-align:center;font-size:4em;'>{i}</h1>", unsafe_allow_html=True)
                time.sleep(1)
            cd.markdown("<h1 style='text-align:center;font-size:4em;'>GO!</h1>", unsafe_allow_html=True)
            time.sleep(1)
            st.session_state.workout_started = True
            st.session_state.start_time = time.time()
            st.session_state.last_frame_time = st.session_state.start_time
            del st.session_state['start_countdown']
            st.rerun()

    # Main workout screen
    else:
        if st.button("⏹ End Plank"):
            st.session_state.workout_duration = time.time() - st.session_state.start_time
            st.session_state.good_reps = st.session_state.good_form_time
            st.session_state.counter = st.session_state.workout_duration
            st.session_state.page = 'summary'
            st.session_state.workout_started = False
            st.rerun()

        # Show metrics
        m1, m2 = st.columns(2)
        elapsed_metric = m1.empty()
        good_form_metric = m2.empty()

        FRAME_WINDOW = st.image([])
        mp_drawing, mp_pose = mp.solutions.drawing_utils, mp.solutions.pose
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            st.error("❌ Webcam not available.")
            st.stop()

        with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
            while cap.isOpened() and st.session_state.workout_started:
                ret, frame = cap.read()
                if not ret: break
                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = pose.process(image)
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

                try:
                    lm = results.pose_landmarks.landmark
                    shoulder = [lm[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, lm[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                    hip = [lm[mp_pose.PoseLandmark.LEFT_HIP.value].x, lm[mp_pose.PoseLandmark.LEFT_HIP.value].y]
                    ankle = [lm[mp_pose.PoseLandmark.LEFT_ANKLE.value].x, lm[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]

                    hip_angle = calculate_angle(shoulder, hip, ankle)
                    st.session_state.feedback_list = check_plank_form(hip_angle)
                    good_form = not st.session_state.feedback_list

                    now = time.time()
                    if good_form:
                        st.session_state.good_form_time += now - st.session_state.last_frame_time
                    st.session_state.last_frame_time = now

                except: pass

                # On-Screen Feedback
                y = 100
                if st.session_state.feedback_list:
                    for fb in st.session_state.feedback_list:
                        cv2.putText(image, fb, (15,y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2, cv2.LINE_AA)
                        y += 30
                else:
                    cv2.putText(image, "HOLDING STRONG!", (15,y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2, cv2.LINE_AA)

                if results.pose_landmarks:
                    mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                
                # Update UI
                elapsed = int(time.time() - st.session_state.start_time)
                elapsed_metric.metric("Time Elapsed", f"{elapsed}s")
                good_form_metric.metric("Good Form Hold", f"{int(st.session_state.good_form_time)}s")
                FRAME_WINDOW.image(image, channels="BGR", use_container_width=True)
        cap.release()
