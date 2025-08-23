# exercises/pushups.py

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

def check_pushup_form(elbow_angle, hip_angle, stage):
    feedback = []
    if stage == "down" and elbow_angle > 90:
        feedback.append("Lower your chest further.")
    if hip_angle < 160:
        feedback.append("Keep your back straight (hips sagging).")
    if hip_angle > 190:
        feedback.append("Keep your back straight (hips too high).")
    return feedback

def run():
    st.title("🤸 Push-Up Tracker")

    # Initialize state robustly
    if 'workout_started' not in st.session_state or st.session_state.get('current_exercise') != 'pushups':
        st.session_state.workout_started = False
        st.session_state.current_exercise = 'pushups'
        st.session_state.counter = 0
        st.session_state.stage = "up"
        st.session_state.start_time = 0
        st.session_state.good_reps = 0
        st.session_state.feedback_list = []
        st.session_state.start_countdown = False

    if not st.session_state.workout_started:
        if not st.session_state.get('start_countdown', False):
            st.header("Get Ready!")
            st.write("Make sure your whole body is visible from the side.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Start Push-Ups"):
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
        if st.button("⏹ End Workout"):
            st.session_state.workout_duration = time.time() - st.session_state.start_time
            st.session_state.page, st.session_state.workout_started = 'summary', False
            st.rerun()

        # Show metrics
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
                img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                res = pose.process(img)
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

                try:
                    lm = res.pose_landmarks.landmark
                    shoulder = [lm[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, lm[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                    elbow = [lm[mp_pose.PoseLandmark.LEFT_ELBOW.value].x, lm[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
                    wrist = [lm[mp_pose.PoseLandmark.LEFT_WRIST.value].x, lm[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
                    hip = [lm[mp_pose.PoseLandmark.LEFT_HIP.value].x, lm[mp_pose.PoseLandmark.LEFT_HIP.value].y]
                    knee = [lm[mp_pose.PoseLandmark.LEFT_KNEE.value].x, lm[mp_pose.PoseLandmark.LEFT_KNEE.value].y]

                    elbow_angle = calculate_angle(shoulder, elbow, wrist)
                    hip_angle = calculate_angle(shoulder, hip, knee)

                    # --- Corrected Rep Counting and Feedback Logic ---
                    
                    # Determine current stage based on elbow angle
                    if elbow_angle > 160:
                        current_stage = "up"
                    elif elbow_angle < 90:
                        current_stage = "down"
                    else:
                        current_stage = st.session_state.stage

                    # Check for the specific transition from "up" to "down" to count a rep
                    if current_stage == "down" and st.session_state.stage == "up":
                        st.session_state.counter += 1
                        # Check form at the exact moment the rep is completed
                        if not check_pushup_form(elbow_angle, hip_angle, "down"):
                            st.session_state.good_reps += 1
                    
                    # Update the stage for the next frame
                    st.session_state.stage = current_stage
                    
                    # Get feedback for the current frame to display
                    st.session_state.feedback_list = check_pushup_form(elbow_angle, hip_angle, current_stage)

                except: pass

                # On-Screen Feedback
                y = 100
                if st.session_state.feedback_list:
                    for fb in st.session_state.feedback_list:
                        cv2.putText(img, fb, (15,y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2, cv2.LINE_AA); y+=30
                else:
                    cv2.putText(img, "GOOD FORM", (15,y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2, cv2.LINE_AA)

                if res.pose_landmarks: 
                    mp_drawing.draw_landmarks(img, res.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                
                # Update UI
                reps_metric.metric("Reps", st.session_state.counter)
                stage_metric.metric("Stage", st.session_state.stage if st.session_state.stage else "-")
                good_reps_metric.metric("Good Reps", st.session_state.good_reps)
                FRAME_WINDOW.image(img, channels="BGR", use_container_width=True)
        cap.release()
