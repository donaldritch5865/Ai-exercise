# exercises/lateral_raises.py

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

def check_lateral_raise_form(shoulder_angle, elbow_angle, stage):
    feedback = []
    if stage == "up" and shoulder_angle < 70:
        feedback.append("Lift your arms higher (to shoulder height).")
    if shoulder_angle > 110:
        feedback.append("Don't lift too high; avoid shrugging.")
    if elbow_angle < 150:
        feedback.append("Keep your arms straighter.")
    return feedback

def run():
    st.set_page_config(layout="wide")
    st.title("💪 Lateral Raise Tracker")

    if 'workout_started' not in st.session_state or st.session_state.get('current_exercise') != 'lateral_raises':
        st.session_state.workout_started = False
        st.session_state.current_exercise = 'lateral_raises'
        st.session_state.counter = 0
        st.session_state.stage = None
        st.session_state.start_time = 0
        st.session_state.good_reps = 0
        st.session_state.feedback_list = []

    # Countdown Screen
    if not st.session_state.workout_started:
        if not st.session_state.get('start_countdown', False):
            st.header("Get Ready!")
            st.write("Stand tall, arms by your sides, ready for lateral raises.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Start Workout"):
                    st.session_state.start_countdown = True
                    st.rerun()
            with col2:
                if st.button("Back to Home"):
                    st.session_state.page = 'home'
                    for key in list(st.session_state.keys()):
                        if key != 'page': del st.session_state[key]
                    st.rerun()
        else:
            countdown = st.empty()
            for i in range(3, 0, -1):
                countdown.markdown(f"<h1 style='text-align:center;font-size:4em;'>{i}</h1>", unsafe_allow_html=True)
                time.sleep(1)
            countdown.markdown("<h1 style='text-align:center;font-size:4em;'>GO!</h1>", unsafe_allow_html=True)
            time.sleep(1)
            st.session_state.workout_started = True
            st.session_state.start_time = time.time()
            del st.session_state['start_countdown']
            st.rerun()
    else:
        col1, col2, col3 = st.columns([1,2,1])
        with col1:
            if st.button("⏹ End Workout"):
                st.session_state.workout_duration = time.time() - st.session_state.start_time
                st.session_state.page = 'summary'
                st.session_state.workout_started = False
                st.rerun()
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Reps", st.session_state.counter)
        m2.metric("Stage", st.session_state.stage if st.session_state.stage else "-")
        m3.metric("Good Reps", st.session_state.good_reps)

        FRAME_WINDOW = st.image([])
        mp_drawing, mp_pose = mp.solutions.drawing_utils, mp.solutions.pose
        cap = cv2.VideoCapture(0)

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
                    elbow = [lm[mp_pose.PoseLandmark.LEFT_ELBOW.value].x, lm[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
                    wrist = [lm[mp_pose.PoseLandmark.LEFT_WRIST.value].x, lm[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
                    hip = [lm[mp_pose.PoseLandmark.LEFT_HIP.value].x, lm[mp_pose.PoseLandmark.LEFT_HIP.value].y]

                    shoulder_angle = calculate_angle(hip, shoulder, elbow)
                    elbow_angle = calculate_angle(shoulder, elbow, wrist)

                    if shoulder_angle < 30: st.session_state.stage = "down"
                    if shoulder_angle > 70 and st.session_state.stage == "down":
                        st.session_state.stage = "up"
                        st.session_state.counter += 1
                        if not st.session_state.feedback_list: st.session_state.good_reps += 1
                    
                    st.session_state.feedback_list = check_lateral_raise_form(shoulder_angle, elbow_angle, st.session_state.stage)
                except: pass

                y = 100
                if st.session_state.feedback_list:
                    for fb in st.session_state.feedback_list:
                        cv2.putText(image, fb, (15, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
                        y += 30
                else:
                    cv2.putText(image, "GOOD FORM", (15,y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

                if results.pose_landmarks:
                    mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                FRAME_WINDOW.image(image, channels="BGR", use_container_width=True)
        cap.release()
