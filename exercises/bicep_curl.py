# exercises/bicep_curl.py

import time
import cv2
import numpy as np
import streamlit as st
import mediapipe as mp
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration, VideoTransformerBase

# --- helpers ---
def calculate_angle(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    return 360 - angle if angle > 180 else angle

def check_bicep_curl_form(landmarks, elbow_angle, stage):
    feedback = []
    mp_pose = mp.solutions.pose
    shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
    elbow    = landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value]
    hip      = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]

    if stage == "up" and elbow_angle > 45:
        feedback.append("Lift higher for a full contraction.")
    if stage == "down" and elbow_angle < 150:
        feedback.append("Lower your arm completely.")
    if abs(shoulder.x - hip.x) > 0.08:
        feedback.append("Avoid swinging your body.")
    if (elbow.x - shoulder.x) > 0.08:
        feedback.append("Keep elbows tucked in.")
    return feedback


# --- live processor (no UI text here; keep overlays minimal) ---
class BicepCurlProcessor(VideoTransformerBase):
    def __init__(self):
        self.counter = 0
        self.stage = None
        self.good_reps = 0
        self.elbow_angle = 0
        self.feedback_list = []

        self.mp_pose = mp.solutions.pose
        # Use default CPU pose; more stable on Streamlit Cloud
        self.pose = self.mp_pose.Pose(
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.drawer = mp.solutions.drawing_utils

    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb)

        try:
            lms = results.pose_landmarks.landmark

            shoulder = [lms[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                        lms[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            elbow    = [lms[self.mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
                        lms[self.mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
            wrist    = [lms[self.mp_pose.PoseLandmark.LEFT_WRIST.value].x,
                        lms[self.mp_pose.PoseLandmark.LEFT_WRIST.value].y]

            self.elbow_angle = calculate_angle(shoulder, elbow, wrist)

            # Rep counting (same logic as before)
            if self.elbow_angle > 160:
                self.stage = "down"
            if self.elbow_angle < 30 and self.stage == "down":
                self.stage = "up"
                self.counter += 1
                if not self.feedback_list:
                    self.good_reps += 1

            # Form feedback (for the UI panel)
            self.feedback_list = check_bicep_curl_form(lms, self.elbow_angle, self.stage)

        except Exception:
            pass

        # Draw only landmarks/lines (no text on video)
        if results.pose_landmarks:
            self.drawer.draw_landmarks(img, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)

        return img


RTC_CONFIG = RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]})

# --- main ---
def run():
    st.title("💪 Live Bicep Curl Tracker")

    # Top metrics – updated live in a loop below
    m1, m2, m3 = st.columns(3)
    reps_ph   = m1.empty()
    stage_ph  = m2.empty()
    good_ph   = m3.empty()

    # Centered video
    center = st.columns([1, 4, 1])[1]
    with center:
        webrtc_ctx = webrtc_streamer(
            key="bicep",
            mode=WebRtcMode.SENDRECV,
            rtc_configuration=RTC_CONFIG,
            media_stream_constraints={"video": True, "audio": False},
            video_processor_factory=BicepCurlProcessor,
        )

    # Analysis panel (separate from video)
    st.markdown("---")
    a1, a2 = st.columns([2, 1])

    with a1:
        st.subheader("Form Feedback (Live)")
        feedback_box = st.empty()

    with a2:
        st.subheader("Elbow Angle")
        angle_ph = st.empty()

    # Live UI updater
    if webrtc_ctx and webrtc_ctx.state.playing:
        while webrtc_ctx.state.playing:
            vp = webrtc_ctx.video_processor
            if vp is None:
                break

            reps_ph.metric("Reps", int(vp.counter))
            stage_ph.metric("Stage", vp.stage if vp.stage else "-")
            good_ph.metric("Good Reps", int(vp.good_reps))

            # Angle + feedback text
            angle_ph.markdown(f"<h3 style='text-align:center'>{int(vp.elbow_angle)}°</h3>", unsafe_allow_html=True)
            if vp.feedback_list:
                feedback_box.write("\n".join([f"• {t}" for t in vp.feedback_list]))
            else:
                feedback_box.success("Good form!")

            time.sleep(0.1)

    # Optional: End Workout button to match your app flow
    st.markdown("---")
    if st.button("⏹ End Workout"):
        st.session_state.page = "summary"
        st.rerun()
