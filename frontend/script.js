class FitnessApp {
    constructor() {
        this.apiBaseUrl = 'http://localhost:5000/api';
        this.videoFeedUrl = 'http://localhost:5000/video_feed';
        this.currentExercise = null;
        this.statsInterval = null;
        this.isWorkoutActive = false;
        
        this.initializeElements();
        this.bindEvents();
        this.loadExercises();
    }
    
    initializeElements() {
        // Screens
        this.exerciseSelectionScreen = document.getElementById('exercise-selection');
        this.workoutScreen = document.getElementById('workout-screen');
        this.summaryScreen = document.getElementById('summary-screen');
        this.loadingScreen = document.getElementById('loading-screen');
        
        // Exercise selection
        this.exercisesGrid = document.getElementById('exercises-grid');
        
        // Workout elements
        this.currentExerciseTitle = document.getElementById('current-exercise-title');
        this.videoFeed = document.getElementById('video-feed');
        this.countdown = document.getElementById('countdown');
        this.stopWorkoutBtn = document.getElementById('stop-workout-btn');
        
        // Stats elements
        this.repsCount = document.getElementById('reps-count');
        this.goodRepsCount = document.getElementById('good-reps-count');
        this.stageDisplay = document.getElementById('stage-display');
        this.timeElapsed = document.getElementById('time-elapsed');
        this.feedbackList = document.getElementById('feedback-list');
        
        // Summary elements
        this.summaryStats = document.getElementById('summary-stats');
        this.backToHomeBtn = document.getElementById('back-to-home-btn');
    }
    
    bindEvents() {
        this.stopWorkoutBtn.addEventListener('click', () => this.stopWorkout());
        this.backToHomeBtn.addEventListener('click', () => this.goHome());
    }
    
    async loadExercises() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/exercises`);
            const exercises = await response.json();
            this.renderExercises(exercises);
        } catch (error) {
            console.error('Failed to load exercises:', error);
            this.showError('Failed to load exercises. Please refresh the page.');
        }
    }
    
    renderExercises(exercises) {
        this.exercisesGrid.innerHTML = '';
        
        exercises.forEach(exercise => {
            const exerciseCard = document.createElement('div');
            exerciseCard.className = 'exercise-card';
            exerciseCard.innerHTML = `
                <span class="exercise-icon">${exercise.icon}</span>
                <div class="exercise-name">${exercise.name}</div>
            `;
            
            exerciseCard.addEventListener('click', () => this.selectExercise(exercise));
            this.exercisesGrid.appendChild(exerciseCard);
        });
    }
    
    async selectExercise(exercise) {
        this.currentExercise = exercise;
        this.showScreen('loading');
        
        try {
            // Start countdown
            await this.showCountdown();
            
            // Start exercise
            const response = await fetch(`${this.apiBaseUrl}/start_exercise`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ exercise: exercise.id })
            });
            
            if (!response.ok) {
                throw new Error('Failed to start exercise');
            }
            
            this.startWorkout();
            
        } catch (error) {
            console.error('Failed to start exercise:', error);
            this.showError('Failed to start exercise. Please try again.');
            this.goHome();
        }
    }
    
    async showCountdown() {
        return new Promise((resolve) => {
            this.showScreen('workout');
            this.currentExerciseTitle.textContent = this.currentExercise.name;
            this.countdown.classList.remove('hidden');
            
            let count = 3;
            this.countdown.textContent = count;
            
            const countdownInterval = setInterval(() => {
                count--;
                if (count > 0) {
                    this.countdown.textContent = count;
                } else if (count === 0) {
                    this.countdown.textContent = 'GO!';
                } else {
                    this.countdown.classList.add('hidden');
                    clearInterval(countdownInterval);
                    resolve();
                }
            }, 1000);
        });
    }
    
    startWorkout() {
        this.isWorkoutActive = true;
        
        // Start video feed
        this.videoFeed.src = this.videoFeedUrl + '?t=' + Date.now();
        
        // Start stats polling
        this.statsInterval = setInterval(() => this.updateStats(), 1000);
        
        // Initial stats update
        this.updateStats();
    }
    
    async updateStats() {
        if (!this.isWorkoutActive) return;
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/stats`);
            if (response.ok) {
                const stats = await response.json();
                this.renderStats(stats);
            }
        } catch (error) {
            console.error('Failed to update stats:', error);
        }
    }
    
    renderStats(stats) {
        if (stats.exercise === 'plank') {
            // Plank-specific stats
            this.repsCount.textContent = '-';
            this.goodRepsCount.textContent = '-';
            this.stageDisplay.textContent = 'Holding';
            this.timeElapsed.textContent = `${stats.elapsed_time}s`;
            
            // Update a different stat card for plank
            const statCards = document.querySelectorAll('.stat-card');
            if (statCards[1]) {
                statCards[1].querySelector('.stat-value').textContent = `${stats.good_form_time}s`;
                statCards[1].querySelector('.stat-label').textContent = 'Good Form';
            }
        } else {
            // Regular exercise stats
            this.repsCount.textContent = stats.reps || 0;
            this.goodRepsCount.textContent = stats.good_reps || 0;
            this.stageDisplay.textContent = stats.stage || '-';
            this.timeElapsed.textContent = `${stats.elapsed_time}s`;
        }
        
        // Update feedback
        this.renderFeedback(stats.feedback || []);
    }
    
    renderFeedback(feedback) {
        this.feedbackList.innerHTML = '';
        
        if (feedback.length === 0) {
            const goodFeedback = document.createElement('div');
            goodFeedback.className = 'feedback-item good';
            goodFeedback.textContent = 'GOOD FORM';
            this.feedbackList.appendChild(goodFeedback);
        } else {
            feedback.forEach(item => {
                const feedbackItem = document.createElement('div');
                feedbackItem.className = 'feedback-item warning';
                feedbackItem.textContent = item;
                this.feedbackList.appendChild(feedbackItem);
            });
        }
    }
    
    async stopWorkout() {
        this.isWorkoutActive = false;
        
        // Clear intervals
        if (this.statsInterval) {
            clearInterval(this.statsInterval);
            this.statsInterval = null;
        }
        
        // Stop video feed
        this.videoFeed.src = '';
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/stop_exercise`, {
                method: 'POST'
            });
            
            if (response.ok) {
                const result = await response.json();
                this.showSummary(result.final_stats);
            } else {
                throw new Error('Failed to stop exercise');
            }
        } catch (error) {
            console.error('Failed to stop exercise:', error);
            this.goHome();
        }
    }
    
    showSummary(stats) {
        this.showScreen('summary');
        
        if (!stats) {
            this.summaryStats.innerHTML = '<p>No workout data available.</p>';
            return;
        }
        
        let summaryHTML = '';
        
        if (stats.exercise === 'plank') {
            const formRatio = stats.good_form_time > 0 ? 
                (stats.good_form_time / stats.elapsed_time * 100).toFixed(1) : 0;
            
            summaryHTML = `
                <div class="summary-stat">
                    <span class="summary-stat-label">Total Hold Time</span>
                    <span class="summary-stat-value">${stats.elapsed_time}s</span>
                </div>
                <div class="summary-stat">
                    <span class="summary-stat-label">Good Form Time</span>
                    <span class="summary-stat-value">${stats.good_form_time}s</span>
                </div>
                <div class="summary-stat">
                    <span class="summary-stat-label">Form Consistency</span>
                    <span class="summary-stat-value">${formRatio}%</span>
                </div>
            `;
        } else {
            const formRatio = stats.reps > 0 ? 
                (stats.good_reps / stats.reps * 100).toFixed(1) : 100;
            const pace = stats.elapsed_time > 0 ? 
                (stats.reps / (stats.elapsed_time / 60)).toFixed(1) : 0;
            
            summaryHTML = `
                <div class="summary-stat">
                    <span class="summary-stat-label">Total Reps</span>
                    <span class="summary-stat-value">${stats.reps}</span>
                </div>
                <div class="summary-stat">
                    <span class="summary-stat-label">Good Reps</span>
                    <span class="summary-stat-value">${stats.good_reps}</span>
                </div>
                <div class="summary-stat">
                    <span class="summary-stat-label">Workout Duration</span>
                    <span class="summary-stat-value">${stats.elapsed_time}s</span>
                </div>
                <div class="summary-stat">
                    <span class="summary-stat-label">Form Accuracy</span>
                    <span class="summary-stat-value">${formRatio}%</span>
                </div>
                <div class="summary-stat">
                    <span class="summary-stat-label">Pace (Reps/Min)</span>
                    <span class="summary-stat-value">${pace}</span>
                </div>
            `;
        }
        
        this.summaryStats.innerHTML = summaryHTML;
    }
    
    goHome() {
        this.isWorkoutActive = false;
        this.currentExercise = null;
        
        // Clear intervals
        if (this.statsInterval) {
            clearInterval(this.statsInterval);
            this.statsInterval = null;
        }
        
        // Stop video feed
        this.videoFeed.src = '';
        
        // Reset UI
        this.showScreen('exercise-selection');
    }
    
    showScreen(screenName) {
        // Hide all screens
        document.querySelectorAll('.screen').forEach(screen => {
            screen.classList.remove('active');
        });
        
        // Show target screen
        const targetScreen = document.getElementById(screenName === 'exercise-selection' ? 
            'exercise-selection' : screenName + '-screen');
        if (targetScreen) {
            targetScreen.classList.add('active');
        }
    }
    
    showError(message) {
        alert(message); // Simple error handling - could be improved with a modal
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new FitnessApp();
});