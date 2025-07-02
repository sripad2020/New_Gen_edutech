from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
import google.generativeai as genai
from nltk.tokenize import sent_tokenize, word_tokenize
import re
from nltk import FreqDist
from nltk.corpus import stopwords
import nltk
import sqlite3
from datetime import datetime
import random, os, csv
import string
import numpy as np
from keras.api.models import load_model
from keras.api.preprocessing.sequence import pad_sequences
import pickle
from sklearn.preprocessing import LabelEncoder
import logging
from functools import wraps

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure NLTK data is downloaded
nltk.download('punkt')
nltk.download('stopwords')


# Load ML models and components
def load_ml_components():
    components = {
        'sentiment_model': None,
        'tokenizer': None,
        'maxlen': None,
        'enc': None
    }

    try:
        components['sentiment_model'] = load_model('text_classification_model.h5')
        with open('tokenizer.pkl', 'rb') as f:
            components['tokenizer'] = pickle.load(f)
        with open('maxlen.pkl', 'rb') as f:
            components['maxlen'] = pickle.load(f)
        with open('label_encoder.pkl', 'rb') as f:
            components['enc'] = pickle.load(f)
    except Exception as e:
        logger.error(f"Error loading ML components: {e}")

    return components


ml_components = load_ml_components()


# Database connection
def get_db_connection():
    conn = sqlite3.connect('users.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


# Initialize database
def init_db():
    try:
        conn = get_db_connection()
        conn.execute('''
            CREATE TABLE IF NOT EXISTS user_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                course TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
    finally:
        conn.close()


init_db()


# Decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in to access this page')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


# Utility functions
def convert_paragraph_to_points(paragraph, num_points=5):
    try:
        sentences = sent_tokenize(paragraph)
        words = word_tokenize(paragraph.lower())
        stop_words = set(stopwords.words('english'))
        filtered_words = [word for word in words if word.isalnum() and word not in stop_words]
        freq_dist = FreqDist(filtered_words)

        sentence_scores = {}
        for sentence in sentences:
            sentence_word_tokens = word_tokenize(sentence.lower())
            sentence_word_tokens = [word for word in sentence_word_tokens if word.isalnum()]
            score = sum(freq_dist.get(word, 0) for word in sentence_word_tokens)
            sentence_scores[sentence] = score

        sorted_sentences = sorted(sentence_scores, key=sentence_scores.get, reverse=True)
        return sorted_sentences[:num_points]
    except Exception as e:
        logger.error(f"Error converting paragraph to points: {e}")
        return []


def clean_text(text):
    return re.sub(r'\*\*|\*', '', text)


def generate_mcq_questions(topic, num_questions=10):
    try:
        genai.configure(api_key='AIzaSyCOoAQyClkN6jGPl5iskpU0knbnERA-gVE')
        model = genai.GenerativeModel('gemini-2.0-flash')

        prompt = f"""
        Generate exactly {num_questions} high-quality multiple choice questions about {topic}.
        Each question must follow these guidelines:
        1. Focus on important concepts from {topic}
        2. Provide 4 options (a, b, c, d) where:
           - One option is clearly correct (marked with "(correct)")
           - Three options are plausible but incorrect
        3. Format each question like this:
           Q1. [Question text]?
           a) [Option 1]
           b) [Correct option] (correct)
           c) [Option 3]
           d) [Option 4]
        """

        response = model.generate_content(prompt)
        return parse_mcq_response(response.text, num_questions)
    except Exception as e:
        logger.error(f"Error generating MCQ questions: {e}")
        return generate_fallback_questions(topic, num_questions)


def parse_mcq_response(text, num_questions):
    questions = []
    current_question = None

    for line in text.split('\n'):
        line = line.strip()

        # Detect question start
        if re.match(r'^(Q?\d+\.|Question \d+:?)', line):
            if current_question and len(current_question['options']) == 4:
                questions.append(current_question)

            question_text = re.sub(r'^(Q?\d+\.|Question \d+:?)\s*', '', line)
            current_question = {
                'question': question_text,
                'options': [],
                'correct_answer': None
            }
        # Detect options
        elif re.match(r'^[a-d]\)', line):
            if current_question:
                option_text = re.sub(r'^[a-d]\)\s*', '', line)
                is_correct = '(correct)' in option_text.lower()

                if is_correct:
                    option_text = re.sub(r'\(correct\)', '', option_text, flags=re.IGNORECASE).strip()
                    current_question['correct_answer'] = option_text

                current_question['options'].append(option_text)

    # Add the last question if complete
    if current_question and len(current_question['options']) == 4:
        questions.append(current_question)

    return questions[:num_questions]


def generate_fallback_questions(topic, num_questions):
    base_question = {
        'question': f"What is an important concept in {topic}?",
        'options': [
            "A common misconception",
            "The correct concept",
            "A related but different concept",
            "An outdated approach"
        ],
        'correct_answer': "The correct concept"
    }
    return [dict(base_question, question=f"{base_question['question']} ({i + 1})") for i in range(num_questions)]


def store_test_results(username, course, correct_answers, max_marks):
    try:
        csv_file = 'test_results.csv'
        percentage = (correct_answers / max_marks) * 100 if max_marks > 0 else 0

        data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'username': username,
            'subject': course,
            'correct_answers': correct_answers,
            'max_marks': max_marks,
            'percentage': f"{percentage:.2f}%"
        }

        file_exists = os.path.isfile(csv_file)
        with open(csv_file, mode='a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=data.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(data)
    except Exception as e:
        logger.error(f"Error storing test results: {e}")


# Routes
@app.route('/')
def home():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Username and password are required')
            return redirect(url_for('login'))

        try:
            conn = get_db_connection()
            user = conn.execute(
                "SELECT username, email, password, course FROM user_info WHERE username = ?",
                (username,)
            ).fetchone()
            conn.close()

            if not user:
                flash('Invalid username or password')
                return redirect(url_for('login'))

            # In a real app, verify password hash here
            if password != user['password']:
                flash('Invalid username or password')
                return redirect(url_for('login'))

            session['username'] = user['username']
            session['email'] = user['email']
            session['course'] = user['course']

            return redirect(url_for('dashboard'))
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            flash('An error occurred during login')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            confirm_password = request.form.get('confirm-password')
            course = request.form['course']

            if not all([username, email, password, confirm_password, course]):
                return jsonify({"success": False, "message": "All fields are required"}), 400

            if password != confirm_password:
                return jsonify({"success": False, "message": "Passwords do not match"}), 400

            conn = get_db_connection()
            conn.execute(
                "INSERT INTO user_info (username, email, password, course) VALUES (?, ?, ?, ?)",
                (username, email, password, course)
            )
            conn.commit()
            conn.close()

            return jsonify({
                "success": True,
                "message": "Registration successful!",
                "redirect": "/login"
            })
        except sqlite3.IntegrityError:
            return jsonify({
                "success": False,
                "message": "Username or email already exists"
            }), 400
        except Exception as e:
            logger.error(f"Signup error: {e}")
            return jsonify({
                "success": False,
                "message": "Registration failed. Please try again."
            }), 500

    return render_template('signup.html')


@app.route('/dashboard')
@login_required
def dashboard():
    # Sample course videos data
    course_videos = {
        'Python': [
            {'title': 'Python Full Course', 'video_id': 'rfscVS0vtbw', 'duration': '4:26:52'},
            # Add more videos...
        ],
        # Add other courses...
    }

    videos = course_videos.get(session['course'], [])
    return render_template('dashboard.html',
                           username=session['username'],
                           course=session.get('course', 'No Course'),
                           videos=videos)


@app.route('/test', methods=['GET', 'POST'])
@login_required
def test():
    try:
        questions = generate_mcq_questions(session['course'])

        # Shuffle options for each question
        for question in questions:
            correct = question['correct_answer']
            random.shuffle(question['options'])
            question['correct_answer'] = correct  # Update reference after shuffle

        session['questions'] = questions
        session['current_question'] = 0
        session['score'] = 0
        session['user_answers'] = []

        return redirect(url_for('show_question'))
    except Exception as e:
        logger.error(f"Test generation error: {e}")
        flash('Error generating test. Using fallback questions.')
        return redirect(url_for('fallback_test'))


@app.route('/fallback-test')
@login_required
def fallback_test():
    session['questions'] = generate_fallback_questions(session['course'], 10)
    session['current_question'] = 0
    session['score'] = 0
    session['user_answers'] = []
    return redirect(url_for('show_question'))


@app.route('/question', methods=['GET', 'POST'])
@login_required
def show_question():
    if 'questions' not in session:
        return redirect(url_for('test'))

    current_idx = session.get('current_question', 0)
    questions = session.get('questions', [])

    if current_idx >= len(questions):
        return redirect(url_for('result'))

    question_data = questions[current_idx]

    if request.method == 'POST':
        user_answer = request.form.get('answer', '').strip()
        session['user_answers'].append(user_answer)

        if user_answer == question_data['correct_answer']:
            session['score'] += 1

        session['current_question'] += 1
        return redirect(url_for('show_question'))

    return render_template('test.html',
                           question=question_data['question'],
                           options=question_data['options'],
                           current_question=current_idx + 1,
                           total_questions=len(questions))


@app.route('/result')
@login_required
def result():
    questions = session.get('questions', [])
    user_answers = session.get('user_answers', [])
    score = session.get('score', 0)
    total_questions = len(questions)
    percentage = (score / total_questions) * 100 if total_questions > 0 else 0

    detailed_results = []
    for i in range(total_questions):
        detailed_results.append({
            'question': questions[i]['question'],
            'user_answer': user_answers[i] if i < len(user_answers) else 'Not answered',
            'correct_answer': questions[i]['correct_answer'],
            'is_correct': (i < len(user_answers)) and (user_answers[i] == questions[i]['correct_answer'])
        })

    store_test_results(
        username=session['username'],
        course=session['course'],
        correct_answers=score,
        max_marks=total_questions
    )

    if percentage >= 70:
        return redirect(url_for('next_page'))

    return render_template('result.html',
                           score=score,
                           total_questions=total_questions,
                           percentage=percentage,
                           detailed_results=detailed_results)


@app.route('/progress')
@login_required
def progress():
    test_results = []
    try:
        with open('test_results.csv', mode='r') as file:
            reader = csv.DictReader(file)
            test_results = [row for row in reader if row['username'] == session['username']]
    except FileNotFoundError:
        pass

    return render_template('progress.html',
                           username=session['username'],
                           test_results=test_results,
                           course=session['course'])


@app.route('/next-page')
@login_required
def next_page():
    return render_template('final.html')


if __name__ == '__main__':
    app.run(debug=True)