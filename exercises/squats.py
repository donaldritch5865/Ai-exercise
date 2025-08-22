# exercises/squats.py

import time
import cv2
import numpy as np
import streamlit as st
import mediapipe as mp
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration, VideoTransformerBase

# --- helper functions ---
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

# --- processor ---
class SquatProcessor(VideoTransformerBase):
    def __init__(self):
        self.counter = 0
        self.stage = None
        self.good_reps = 0
        self.knee_angle = 0
        self.hip_angle = 0
        self.feedback_list = []

        self.mp_pose = mp.solutions.pose
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
        res = self.pose.process(rgb)

        try:
            lm = res.pose_landmarks.landmark

            shoulder = [lm[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                        lm[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            hip = [lm[self.mp_pose.PoseLandmark.LEFT_HIP.value].x,
                   lm[self.mp_pose.PoseLandmark.LEFT_HIP.value].y]
            knee = [lm[self.mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                    lm[self.mp_pose.PoseLandmark.LEFT_KNEE.value].y]
            ankle = [lm[self.mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
                     lm[self.mp_pose.PoseLandmark.LEFT_ANKLE.value].y]

            self.knee_angle = calculate_angle(hip, knee, ankle)
            self.hip_angle = calculate_angle(shoulder, hip, knee)

            if self.knee_angle > 160:
                self.stage = "up"
            if self.knee_angle < 100 and self.stage == "up":
                self.stage = "down"
                self.counter += 1
                if not check_squat_form(self.knee_angle, self.hip_angle, "down"):
                    self.good_reps += 1

            self.feedback_list = check_squat_form(self.knee_angle, self.hip_angle, self.stage)

        except Exception:
            pass

        if res.pose_landmarks:
            self.drawer.draw_landmarks(img, res.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)

        return img


RTC_CONFIG = RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]})

# --- main run ---
def run():
    st.title("🏋️ Live Squat Tracker")

    # top metrics
    m1, m2, m3 = st.columns(3)
    reps_ph = m1.empty()
    stage_ph = m2.empty()
    good_ph = m3.empty()

    # centered video
    center = st.columns([1, 4, 1])[1]
    with center:
        webrtc_ctx = webrtc_streamer(
            key="squats",
            mode=WebRtcMode.SENDRECV,
            rtc_configuration=RTC_CONFIG,
            media_stream_constraints={"video": True, "audio": False},
            video_processor_factory=SquatProcessor,
        )

    # feedback panel
    st.markdown("---")
    a1, a2 = st.columns([2, 1])
    with a1:
        st.subheader("Form Feedback (Live)")
        feedback_box = st.empty()
    with a2:
        st.subheader("Knee / Hip Angles")
        angle_ph = st.empty()

    if webrtc_ctx and webrtc_ctx.state.playing:
        while webrtc_ctx.state.playing:
            vp = webrtc_ctx.video_processor
            if vp is None:
                break

            reps_ph.metric("Reps", int(vp.counter))
            stage_ph.metric("Stage", vp.stage if vp.stage else "-")
            good_ph.metric("Good Reps", int(vp.good_reps))

            angle_ph.write(f"Knee: {int(vp.knee_angle)}°\nHip: {int(vp.hip_angle)}°")

            if vp.feedback_list:
                feedback_box.write("\n".join([f"• {fb}" for fb in vp.feedback_list]))
            else:
                feedback_box.success("Good form!")

            time.sleep(0.1)

    st.markdown("---")
    if st.button("⏹ End Workout"):
        st.session_state.page = "summary"
        st.rerun()
