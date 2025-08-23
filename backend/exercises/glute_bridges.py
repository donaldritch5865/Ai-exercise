# exercises/glute_bridges.py

import streamlit as st
import cv2
import mediapipe as mp
import numpy as np
import time

# --- Helper Functions (Specific to Glute Bridges) ---

def calculate_angle(a, b, c):
    """Calculates the angle between three points."""
    a, b, c = np.array(a), np.array(b), np.array(c)
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    return 360 - angle if angle > 180 else angle

def check_glute_bridge_form(hip_angle, stage):
    """Checks the form for a glute bridge and returns feedback."""
    feedback = []
    if stage == "up" and hip_angle < 160:
        feedback.append("Lift your hips higher for full extension.")
    return feedback

def run():
    """Main function to run the Glute Bridge tracker page."""
    st.title("🍑 Glute Bridge Tracker")

    # Initialize state robustly
    if 'workout_started' not in st.session_state or st.session_state.get('current_exercise') != 'glute_bridges':
        st.session_state.workout_started = False
        st.session_state.current_exercise = 'glute_bridges'
        st.session_state.counter = 0
        st.session_state.stage = "down"
        st.session_state.start_time = 0
        st.session_state.good_reps = 0
        st.session_state.feedback_list = []
        st.session_state.start_countdown = False

    # --- Ready / Countdown Screen ---
    if not st.session_state.workout_started:
        if not st.session_state.get('start_countdown', False):
            st.header("Get Ready!")
            st.write("Lie down and ensure your body is clearly visible from the side.")

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
            countdown_placeholder = st.empty()
            for i in range(3, 0, -1):
                countdown_placeholder.markdown(
                    f"<h1 style='text-align:center;font-size:4em;'>{i}</h1>",
                    unsafe_allow_html=True
                )
                time.sleep(1)
            countdown_placeholder.markdown(
                "<h1 style='text-align:center;font-size:4em;'>GO!</h1>",
                unsafe_allow_html=True
            )
            time.sleep(1)

            st.session_state.workout_started = True
            st.session_state.start_time = time.time()
            del st.session_state['start_countdown']
            st.rerun()

    # --- Workout Screen ---
    else:
        if st.button("⏹ End Workout"):
            st.session_state.workout_duration = time.time() - st.session_state.start_time
            st.session_state.page = 'summary'
            st.session_state.workout_started = False
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
                if not ret:
                    st.error("❌ Could not read frame from webcam.")
                    break

                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = pose.process(image)
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

                try:
                    landmarks = results.pose_landmarks.landmark
                    shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                    hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
                    knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]

                    hip_angle = calculate_angle(shoulder, hip, knee)
                    
                    st.session_state.feedback_list = check_glute_bridge_form(hip_angle, st.session_state.stage)

                    if hip_angle < 150:
                        st.session_state.stage = "down"
                    if hip_angle > 160 and st.session_state.stage == 'down':
                        st.session_state.stage = "up"
                        st.session_state.counter += 1
                        # Corrected Good Reps Logic
                        if not check_glute_bridge_form(hip_angle, "up"):
                            st.session_state.good_reps += 1

                except:
                    pass

                # On-Screen Feedback
                y_pos = 100
                if st.session_state.feedback_list:
                    for feedback in st.session_state.feedback_list:
                        cv2.putText(image, feedback, (15, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2, cv2.LINE_AA)
                        y_pos += 30
                else:
                    cv2.putText(image, "GOOD FORM", (15, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)

                if results.pose_landmarks:
                    mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

                # Update UI
                reps_metric.metric("Reps", st.session_state.counter)
                stage_metric.metric("Stage", st.session_state.stage if st.session_state.stage else "-")
                good_reps_metric.metric("Good Reps", st.session_state.good_reps)
                FRAME_WINDOW.image(image, channels='BGR', use_container_width=True)

        cap.release()
