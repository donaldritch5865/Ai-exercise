# app.py

import streamlit as st
from exercises import bicep_curl, squats, overhead_press, lateral_raises, lunges, pullups, pushups, glute_bridges, crunches, plank

# ---------------- CSS ----------------
def load_css():
    st.markdown("""
        <style>
            /* Main container */
            .main .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
                max-width: 1100px;
                margin: auto;
            }

            /* Headings */
            h1 {
                text-align: center;
                font-size: 3rem;
                margin-bottom: 0.2rem;
            }
            .subheading {
                text-align: center;
                font-size: 1.2rem;
                color: #aaa;
                margin-bottom: 2.5rem;
                display: block;
            }

            /* Workout Card Button */
            .stButton>button {
                background: linear-gradient(160deg, #2d2d44, #1c1c2c);
                border-radius: 15px;
                padding: 1.5rem;
                text-align: center;
                transition: all 0.25s ease-in-out;
                border: 1px solid #2e2e40;
                cursor: pointer;
                height: 120px;
                width: 100%;
                font-size: 1rem;
                font-weight: 600;
                color: white;
                letter-spacing: 0.3px;
            }
            .stButton>button:hover {
                transform: translateY(-6px);
                box-shadow: 0px 8px 20px rgba(0,0,0,0.35);
                border: 1px solid #00c6ff;
                background: linear-gradient(160deg, #3b3b5a, #222233);
            }

            /* Footer */
            .footer {
                margin-top: 3rem;
                text-align: center;
                font-size: 0.9rem;
                color: #666;
            }
        </style>
    """, unsafe_allow_html=True)

# ---------------- Summary Page ----------------
def show_summary():
    st.title("Workout Summary 🎉")

    total_reps = st.session_state.get('counter', 0)
    duration_seconds = st.session_state.get('workout_duration', 0)
    good_reps = st.session_state.get('good_reps', 0)

    if st.session_state.get('current_exercise') == 'plank':
        st.header("Plank Performance")
        st.metric("Total Hold Time", f"{int(duration_seconds)}s")
        form_ratio = (good_reps / duration_seconds) * 100 if duration_seconds > 0 else 100
        st.subheader("Form Consistency")
        st.progress(int(form_ratio))
        st.metric("Good Form Ratio", f"{form_ratio:.1f}%")
    else:
        if total_reps > 0:
            form_ratio = (good_reps / total_reps) * 100
            duration_minutes = duration_seconds / 60
            pace = total_reps / duration_minutes if duration_minutes > 0 else 0
        else:
            form_ratio = 100
            pace = 0

        st.header("Your Performance Metrics")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Reps", f"{total_reps}")
        col2.metric("Workout Duration", f"{int(duration_seconds)}s")
        col3.metric("Pace (Reps/Min)", f"{pace:.1f}")

        st.subheader("Form Analysis")
        st.progress(int(form_ratio))
        st.metric("Good Form Ratio", f"{form_ratio:.1f}%")

    if form_ratio >= 90:
        st.success("Excellent form! You maintained great technique throughout the workout.")
    elif form_ratio >= 70:
        st.warning("Good job! There are some minor issues to work on, but your form was mostly solid.")
    else:
        st.error("Let's focus on form. Try to slow down and follow the feedback to improve your technique.")

    if st.button("Back to Home"):
        for key in list(st.session_state.keys()):
            if key not in ['page']:
                del st.session_state[key]
        st.session_state.page = 'home'
        st.rerun()

# ---------------- Main ----------------
def main():
    load_css()

    if 'page' not in st.session_state:
        st.session_state.page = 'home'

    if st.session_state.page == 'home':
        st.markdown("<h1>AI Fitness Trainer 💪</h1>", unsafe_allow_html=True)
        st.markdown("<p class='subheading'>Track · Improve · Transform</p>", unsafe_allow_html=True)

        # --- Exercise Grid ---
        cols = st.columns(5)
        buttons = [
            ("💪 Bicep Curls", "bicep_curl"),
            ("🔑 Squats", "squats"),
            ("🏋️ Overhead Press", "overhead_press"),
            ("👉 Lateral Raises", "lateral_raises"),
            ("🦵 Lunges", "lunges"),
            ("🏋️ Pullups", "pullups"),
            ("🤜 Push-ups", "pushups"),
            ("🍑 Glute Bridges", "glute_bridges"),
            ("🔥 Crunches", "crunches"),
            ("🧘 Plank", "plank")
        ]

        for i, (label, page) in enumerate(buttons):
            with cols[i % 5]:
                if st.button(label, key=page):
                    st.session_state.page = page
                    st.rerun()

        # Footer
        st.markdown("<div class='footer'>AI Fitness Assistant</div>", unsafe_allow_html=True)

    elif st.session_state.page == 'bicep_curl':
        bicep_curl.run()
    elif st.session_state.page == 'squats':
        squats.run()
    elif st.session_state.page == 'overhead_press':
        overhead_press.run()
    elif st.session_state.page == 'lateral_raises':
        lateral_raises.run()
    elif st.session_state.page == 'lunges':
        lunges.run()
    elif st.session_state.page == 'pullups':
        pullups.run()
    elif st.session_state.page == 'pushups':
        pushups.run()
    elif st.session_state.page == 'glute_bridges':
        glute_bridges.run()
    elif st.session_state.page == 'crunches':
        crunches.run()
    elif st.session_state.page == 'plank':
        plank.run()
    elif st.session_state.page == 'summary':
        show_summary()

if __name__ == "__main__":
    main()
