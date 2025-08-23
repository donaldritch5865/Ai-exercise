# exercises/overhead_press.py

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

def check_overhead_press_form(elbow_angle, shoulder_angle, stage):
    feedback = []
    if stage == "up" and elbow_angle < 160:
        feedback.append("Fully extend arms overhead.")
    if stage == "down" and elbow_angle > 100:
        feedback.append("Lower until elbows ~90°.")
    if shoulder_angle < 160 and stage == "up":
        feedback.append("Keep pressing vertically, not forward.")
    return feedback

def run():
    st.title("💪 Overhead Press Tracker")

    # Initialize session state
    if 'workout_started' not in st.session_state or st.session_state.get('current_exercise') != 'overhead_press':
        st.session_state.workout_started = False
        st.session_state.current_exercise = 'overhead_press'
        st.session_state.counter = 0
        st.session_state.stage = 'down'
        st.session_state.start_time = 0
        st.session_state.good_reps = 0
        st.session_state.feedback_list = []
        st.session_state.start_countdown = False

    # Countdown before workout
    if not st.session_state.workout_started:
        if not st.session_state.get('start_countdown', False):
            st.subheader("Get Ready!")
            st.write("Stand upright with dumbbells/bar, ready for presses.")

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
            cd = st.empty()
            for i in range(3,0,-1):
                cd.markdown(f"<h1 style='text-align:center;font-size:4em'>{i}</h1>", unsafe_allow_html=True)
                time.sleep(1)
            cd.markdown("<h1 style='text-align:center;font-size:4em'>GO!</h1>", unsafe_allow_html=True)
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

        # --- Metrics UI (like other exercises) ---
        col1, col2, col3 = st.columns(3)
        reps_metric = col1.empty()
        stage_metric = col2.empty()
        good_reps_metric = col3.empty()

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
                    elbow = [lm[mp_pose.PoseLandmark.LEFT_ELBOW.value].x, lm[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
                    wrist = [lm[mp_pose.PoseLandmark.LEFT_WRIST.value].x, lm[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
                    hip = [lm[mp_pose.PoseLandmark.LEFT_HIP.value].x, lm[mp_pose.PoseLandmark.LEFT_HIP.value].y]

                    elbow_angle = calculate_angle(shoulder, elbow, wrist)
                    shoulder_angle = calculate_angle(hip, shoulder, elbow)

                    if elbow_angle < 90:
                        st.session_state.stage = "down"
                    if elbow_angle > 160 and st.session_state.stage == "down":
                        st.session_state.stage = "up"
                        st.session_state.counter += 1
                        if not check_overhead_press_form(elbow_angle, shoulder_angle, "up"):
                            st.session_state.good_reps += 1
                    
                    st.session_state.feedback_list = check_overhead_press_form(elbow_angle, shoulder_angle, st.session_state.stage)

                except: pass

                # Feedback on video
                y = 100
                if st.session_state.feedback_list:
                    for fb in st.session_state.feedback_list:
                        cv2.putText(image, fb, (15,y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2, cv2.LINE_AA); y+=30
                else:
                    cv2.putText(image, "GOOD FORM", (15,y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2, cv2.LINE_AA)

                if results.pose_landmarks:
                    mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                
                # Update metrics above
                reps_metric.metric("Reps", st.session_state.counter)
                stage_metric.metric("Stage", st.session_state.stage if st.session_state.stage else "-")
                good_reps_metric.metric("Good Reps", st.session_state.good_reps)

                FRAME_WINDOW.image(image, channels="BGR", use_container_width=True)

        cap.release()
