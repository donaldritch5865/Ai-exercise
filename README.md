# AI Fitness Trainer - Full Stack Application

A modern full-stack web application for AI-powered pose estimation and fitness tracking. This application uses computer vision to analyze exercise form in real-time and provide feedback to users.

## Features

- **Real-time Pose Estimation**: Uses MediaPipe for accurate pose detection
- **10 Exercise Types**: Bicep curls, squats, push-ups, pull-ups, planks, and more
- **Form Analysis**: Real-time feedback on exercise form and technique
- **Performance Tracking**: Rep counting, form accuracy, and workout statistics
- **Modern UI**: Responsive design with smooth animations and transitions
- **Video Streaming**: Live webcam feed processing with pose overlay

## Architecture

### Backend (Flask + Python 3.10)
- **Flask API**: RESTful endpoints for exercise management
- **MediaPipe**: Pose estimation and landmark detection
- **OpenCV**: Video processing and streaming
- **Dynamic Module Loading**: Automatically imports exercise logic from `/exercises` directory

### Frontend (HTML/CSS/JavaScript)
- **Vanilla JavaScript**: No framework dependencies for maximum performance
- **Responsive Design**: Works on desktop and mobile devices
- **Real-time Updates**: Live statistics and feedback display
- **Modern UI**: Clean, professional interface with smooth animations

## Quick Start

### Using Docker Compose (Recommended)

1. **Clone and navigate to the project**:
   ```bash
   git clone <repository-url>
   cd ai-fitness-trainer
   ```

2. **Start the application**:
   ```bash
   docker-compose up --build
   ```

3. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000

### Manual Setup

#### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create virtual environment** (Python 3.10 required):
   ```bash
   python3.10 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Flask server**:
   ```bash
   python app.py
   ```

#### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Serve the files** (using Python's built-in server):
   ```bash
   python -m http.server 3000
   ```

   Or use any static file server like `live-server`, `nginx`, or `apache`.

## API Endpoints

### Exercise Management
- `GET /api/exercises` - Get list of available exercises
- `POST /api/start_exercise` - Start exercise tracking
- `POST /api/stop_exercise` - Stop exercise and get final stats
- `GET /api/stats` - Get current exercise statistics

### Video Streaming
- `GET /video_feed` - Live video stream with pose estimation

### Health Check
- `GET /api/health` - Application health status

## Exercise Types

The application supports 10 different exercises:

1. **Bicep Curls** 💪 - Arm strength training
2. **Squats** 🔑 - Lower body compound movement
3. **Overhead Press** 🏋️ - Shoulder and arm strength
4. **Lateral Raises** 👉 - Shoulder isolation
5. **Lunges** 🦵 - Lower body unilateral training
6. **Pull-ups** 🏋️ - Upper body pulling movement
7. **Push-ups** 🤜 - Upper body pushing movement
8. **Glute Bridges** 🍑 - Hip and glute activation
9. **Crunches** 🔥 - Core strengthening
10. **Plank** 🧘 - Core stability and endurance

## Project Structure

```
ai-fitness-trainer/
├── backend/
│   ├── app.py                 # Main Flask application
│   ├── requirements.txt       # Python dependencies
│   ├── Dockerfile            # Backend container config
│   └── exercises/            # Exercise logic modules
│       ├── bicep_curl.py
│       ├── squats.py
│       └── ...
├── frontend/
│   ├── index.html            # Main HTML file
│   ├── styles.css            # Styling and responsive design
│   └── script.js             # Frontend application logic
├── docker-compose.yml        # Multi-container setup
└── README.md                # This file
```

## Development

### Adding New Exercises

1. **Create exercise module** in `backend/exercises/new_exercise.py`:
   ```python
   def calculate_angle(a, b, c):
       # Angle calculation logic
       pass
   
   def check_exercise_form(landmarks, angle, stage):
       # Form checking logic
       return feedback_list
   ```

2. **Add exercise to the list** in `backend/app.py`:
   ```python
   exercises = [
       # ... existing exercises
       {'id': 'new_exercise', 'name': 'New Exercise', 'icon': '🏃'},
   ]
   ```

3. **Implement processing logic** in the `ExerciseProcessor` class.

### Customizing the UI

- **Styles**: Modify `frontend/styles.css` for visual changes
- **Layout**: Update `frontend/index.html` for structural changes
- **Behavior**: Edit `frontend/script.js` for functionality changes

## Requirements

### System Requirements
- **Python 3.10** (for MediaPipe compatibility)
- **Webcam** (for video input)
- **Modern web browser** (Chrome, Firefox, Safari, Edge)

### Hardware Requirements
- **CPU**: Multi-core processor recommended for real-time processing
- **RAM**: 4GB minimum, 8GB recommended
- **Webcam**: 720p or higher resolution recommended

## Troubleshooting

### Common Issues

1. **Webcam not accessible**:
   - Ensure webcam permissions are granted
   - Check if other applications are using the webcam
   - Verify webcam is properly connected

2. **MediaPipe installation issues**:
   - Ensure Python 3.10 is being used
   - Try installing with `--no-cache-dir` flag
   - Check system dependencies are installed

3. **CORS errors**:
   - Ensure backend is running on port 5000
   - Check Flask-CORS is properly configured
   - Verify frontend is accessing correct API URLs

4. **Performance issues**:
   - Reduce video resolution if needed
   - Close other resource-intensive applications
   - Consider using a more powerful machine for real-time processing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- **MediaPipe** - Google's framework for building perception pipelines
- **OpenCV** - Computer vision library
- **Flask** - Python web framework
- Original Streamlit implementation for exercise logic reference