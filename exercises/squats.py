# exercises/squats.py

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

def check_squat_form(knee_angle, hip_angle, stage):
    feedback = []
    if stage == "down" and knee_angle > 100:
        feedback.append("Squat deeper for full range of motion.")
    if hip_angle < 80:
        feedback.append("Keep your chest up and back straight.")
    return feedback

def run():
    st.set_page_config(layout="wide")
    st.title("🏋️ Squat Tracker")

    if 'workout_started' not in st.session_state or st.session_state.get('current_exercise') != 'squats':
        st.session_state.workout_started = False
        st.session_state.current_exercise = 'squats'
        st.session_state.counter, st.session_state.stage = 0, None
        st.session_state.start_time, st.session_state.good_reps = 0, 0
        st.session_state.feedback_list = []

    if not st.session_state.workout_started:
        if not st.session_state.get('start_countdown', False):
            st.header("Get Ready!")
            st.write("Make sure your full body is visible in the camera.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Start Squats"):
                    st.session_state.start_countdown = True
                    st.rerun()
            with col2:
                if st.button("Back to Home"):
                    st.session_state.page = 'home'
                    for k in list(st.session_state.keys()):
                        if k != 'page': del st.session_state[k]
                    st.rerun()
        else:
            cd = st.empty()
            for i in range(3,0,-1):
                cd.markdown(f"<h1 style='text-align:center;font-size:4em;'>{i}</h1>", unsafe_allow_html=True)
                time.sleep(1)
            cd.markdown("<h1 style='text-align:center;font-size:4em;'>GO!</h1>", unsafe_allow_html=True)
            time.sleep(1)
            st.session_state.workout_started, st.session_state.start_time = True, time.time()
            del st.session_state['start_countdown']
            st.rerun()

    else:
        c1, c2, c3 = st.columns([1,2,1])
        with c1:
            if st.button("⏹ End Workout"):
                st.session_state.workout_duration = time.time() - st.session_state.start_time
                st.session_state.page, st.session_state.workout_started = 'summary', False
                st.rerun()

        m1, m2 = st.columns(2)
        
        FRAME_WINDOW = st.image([])
        mp_drawing, mp_pose = mp.solutions.drawing_utils, mp.solutions.pose
        cap = cv2.VideoCapture(0)

        with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
            while cap.isOpened() and st.session_state.workout_started:
                ret, frame = cap.read()
                if not ret: break
                img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                res = pose.process(img)
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

                try:
                    lm = res.pose_landmarks.landmark
                    shoulder = [lm[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, lm[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                    hip = [lm[mp_pose.PoseLandmark.LEFT_HIP.value].x, lm[mp_pose.PoseLandmark.LEFT_HIP.value].y]
                    knee = [lm[mp_pose.PoseLandmark.LEFT_KNEE.value].x, lm[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
                    ankle = [lm[mp_pose.PoseLandmark.LEFT_ANKLE.value].x, lm[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]

                    knee_angle = calculate_angle(hip, knee, ankle)
                    hip_angle = calculate_angle(shoulder, hip, knee)

                    if knee_angle > 160: st.session_state.stage = "up"
                    if knee_angle < 100 and st.session_state.stage == "up":
                        st.session_state.stage = "down"
                        st.session_state.counter += 1
                        if not check_squat_form(knee_angle, hip_angle, "down"):
                            st.session_state.good_reps += 1

                    st.session_state.feedback_list = check_squat_form(knee_angle, hip_angle, st.session_state.stage)
                except: pass

                y = 100
                if st.session_state.feedback_list:
                    for fb in st.session_state.feedback_list:
                        cv2.putText(img, fb, (15,y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2); y+=30
                else:
                    cv2.putText(img, "GOOD FORM", (15,y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

                if res.pose_landmarks: mp_drawing.draw_landmarks(img, res.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                FRAME_WINDOW.image(img, channels="BGR", use_column_width=True)
                
                # Update metrics on the fly
                with m1:
                    st.metric("Reps", st.session_state.counter)
                with m2:
                    st.metric("Good Reps", st.session_state.good_reps)

        cap.release()
