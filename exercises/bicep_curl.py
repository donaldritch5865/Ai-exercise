# exercises/bicep_curl.py

import cv2
import mediapipe as mp
import numpy as np
import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase

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


# --- Video Processor for Live Webcam ---
class BicepCurlProcessor(VideoTransformerBase):
    def __init__(self):
        self.counter = 0
        self.stage = None
        self.good_reps = 0
        self.feedback_list = []

        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose()
        self.mp_drawing = mp.solutions.drawing_utils

    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        results = self.pose.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

        try:
            landmarks = results.pose_landmarks.landmark
            shoulder = [landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                        landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            elbow = [landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
                     landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
            wrist = [landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value].x,
                     landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value].y]

            elbow_angle = calculate_angle(shoulder, elbow, wrist)

            # Rep counting logic
            if elbow_angle > 160:
                self.stage = "down"
            if elbow_angle < 30 and self.stage == "down":
                self.stage = "up"
                self.counter += 1
                if not self.feedback_list:
                    self.good_reps += 1

            # Check form
            self.feedback_list = check_bicep_curl_form(landmarks, elbow_angle, self.stage)

        except:
            pass

        # Draw pose
        if results.pose_landmarks:
            self.mp_drawing.draw_landmarks(img, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)

        # Display metrics
        cv2.putText(img, f"Reps: {self.counter}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(img, f"Stage: {self.stage if self.stage else '-'}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(img, f"Good Reps: {self.good_reps}", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        if self.feedback_list:
            y = 160
            for fb in self.feedback_list:
                cv2.putText(img, fb, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                y += 30
        return img


# --- Main Run Function ---
def run():
    st.title("💪 Live Bicep Curl Tracker")

    webrtc_streamer(
        key="bicep",
        video_processor_factory=BicepCurlProcessor,
        media_stream_constraints={"video": True, "audio": False},
    )
