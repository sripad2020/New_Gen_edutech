from flask import Flask, request, jsonify, render_template,redirect,url_for,flash,session
import google.generativeai as genai
from nltk.tokenize import sent_tokenize, word_tokenize
import re
from nltk import FreqDist
from nltk.corpus import stopwords
import nltk
import sqlite3
from datetime import datetime
import random
import string

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

@app.route('/',methods=['GET','POST'])
def homes():
    return render_template('index.html')


@app.route('/log', methods=['GET', 'POST'])
def log():
    return render_template('login.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')

            if not username or not password:
                flash('Username and password are required')
                return redirect(url_for('login'))

            connection = sqlite3.connect('users.db',check_same_thread=False)
            cursor = connection.cursor()

            cursor.execute("SELECT username, email, password, course FROM user_info WHERE username = ?", (username,))
            user = cursor.fetchone()
            connection.close()

            if not user:
                flash('Invalid username or password')
                return redirect(url_for('login'))

            # Set session variables
            session['username'] = user[0]
            session['email'] = user[1]
            session['course'] = user[3]

            return redirect('/dashboard')

        except Exception as e:
            print(f"Login error: {str(e)}")
            flash('An error occurred during login')
            return redirect(url_for('login'))

    # GET request - show login form
    return render_template('login.html')

@app.route('/dashboard', methods=['GET','POST'])
def dash_board():
    if 'username' not in session:
        return redirect(url_for('log'))

    return render_template('dashboard.html',
                           username=session['username'],
                           course=session.get('course', 'No Course Assigned'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('log'))

@app.route('/signup', methods=['GET', 'POST'])
def sign():
    return render_template('signup.html')

connection = sqlite3.connect('users.db', check_same_thread=False)
cursor = connection.cursor()


@app.route('/signups', methods=['POST'])
def ups():
    if request.method == 'POST':
        try:
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            course = request.form['course']

            # Validate inputs
            if not all([username, email, password, course]):
                return jsonify({"success": False, "message": "All fields are required"}), 400

            # Check if passwords match (frontend should handle this too)
            if request.form.get('confirm-password') != password:
                return jsonify({"success": False, "message": "Passwords do not match"}), 400

            # Insert into database
            cursor.execute(
                "INSERT INTO user_info (username, email, password, course) VALUES (?, ?, ?, ?)",
                (username, email, password, course)
            )
            connection.commit()

            return jsonify({
                "success": True,
                "message": "Registration successful!",
                "redirect": "/log"  # Tell frontend where to redirect
            })

        except sqlite3.IntegrityError:
            connection.rollback()
            return jsonify({
                "success": False,
                "message": "Username or email already exists"
            }), 400

        except Exception as e:
            connection.rollback()
            print(f"Error: {e}")
            return jsonify({
                "success": False,
                "message": "Registration failed. Please try again."
            }), 500

nltk.download('punkt')
nltk.download('stopwords')


@app.route('/chat-bot', methods=['GET'])
def index():
    return render_template('chat.html',
                           what_questions=[],
                           where_questions=[],
                           when_questions=[],
                           why_questions=[],
                           who_questions=[])


def convert_paragraph_to_points(paragraph, num_points=5):
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


def clean_text(text):
    return re.sub(r'\*\*|\*', '', text)

def generate_5w_questions(topic):
    genai.configure(api_key='AIzaSyCOoAQyClkN6jGPl5iskpU0knbnERA-gVE')
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""Generate 5 different types of questions about: {topic}
    Provide exactly 5 questions, one for each W:
    1. What question (explanation/definition)
    2. Where question (location/placement)
    3. When question (timing/duration)
    4. Why question (reason/purpose)
    5. Who question (people/roles)

    Format your response as:
    What|||What is...?
    Where|||Where can...?
    When|||When does...?
    Why|||Why is...?
    Who|||Who is...?"""

    response = model.generate_content(prompt)
    questions = {
        'what': [],
        'where': [],
        'when': [],
        'why': [],
        'who': []
    }

    if response.text:
        for line in response.text.split('\n'):
            if '|||' in line:
                w_type, question = line.split('|||')
                w_type = w_type.strip().lower()
                if w_type in questions:
                    questions[w_type].append(question.strip())
    return questions


@app.route('/chat', methods=['POST'])
def chatting():
    if request.method == 'POST':
        try:
            data = request.get_json()
            user_message = data.get('message', '')
            context = data.get('context', 'general')
            genai.configure(api_key='AIzaSyCOoAQyClkN6jGPl5iskpU0knbnERA-gVE')
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"Provide a detailed response to: {user_message}"
            response = model.generate_content(prompt)
            generated_text = clean_text(response.text)
            questions = generate_5w_questions(user_message)

            return jsonify({
                'response': generated_text,
                'questions': {
                    'what': questions['what'],
                    'where': questions['where'],
                    'when': questions['when'],
                    'why': questions['why'],
                    'who': questions['who']
                }
            })
        except Exception as e:
            print(f"Error: {str(e)}")
            return jsonify({
                'response': "Sorry, I encountered an error processing your request.",
                'questions': {
                    'what': [],
                    'where': [],
                    'when': [],
                    'why': [],
                    'who': []
                }
            }), 500


@app.route('/course',methods=['GET','POST'])
def courses():
    today = datetime.today().weekday()  # Monday=0, Sunday=6
    print(today)
    course_info = []
    if today == 2:
            genai.configure(api_key='AIzaSyAM8hWwGWv5B9pTCnf14Q-Ck_gkukWUrN8')
            model = genai.GenerativeModel('gemini-1.5-flash')
            content = model.generate_content(f"Give me the information about the {session['course']}")
            generated_text = content.text
            key_points = convert_paragraph_to_points(generated_text)
            description = [clean_text(item) for item in key_points]
            days = {0: "Monday", 1: 'Tuesday', 2: "Wednesday", 3: "Thursday", 4: "Friday", 5: "Saturday", 6: 'Sunday'}
            room_name=days[today]
            course_info.append({
                "name": session['course'],
                "description": description,
                "meeting_link": f"https://meet.jit.si/{room_name}+{session['course']}"
            })
    return render_template('discussion.html', courses=course_info, is_friday=(today == 2))


@app.route('/test', methods=['GET', 'POST'])
def test():
    genai.configure(api_key='AIzaSyAM8hWwGWv5B9pTCnf14Q-Ck_gkukWUrN8')
    model = genai.GenerativeModel('gemini-1.5-flash')
    content = model.generate_content(f"Give me the information about {session['course']}")
    generated_text = content.text
    key_points = convert_paragraph_to_points(generated_text)
    description = [clean_text(item) for item in key_points if item.strip()]

    if len(description) < 10:
        description = description * (10 // len(description) + 1)
    description = description[:10]

    questions = []
    for idx, desc in enumerate(description):
        question = f"Explain: {desc}"
        correct_answer = desc
        questions.append({
            'question': question,
            'answer': correct_answer
        })

    session['questions'] = questions
    session['current_question'] = 0
    session['score'] = 0
    return redirect(url_for('show_question'))


@app.route('/question', methods=['GET', 'POST'])
def show_question():
    if 'questions' not in session:
        return redirect(url_for('test'))

    current_question = session.get('current_question', 0)
    questions = session.get('questions', [])

    if current_question >= len(questions):
        return redirect(url_for('result'))

    question = questions[current_question]

    if request.method == 'POST':
        user_answer = request.form.get('answer', '').strip()
        correct_answer = question['answer']

        # Evaluate answer similarity using Gemini
        similarity_score = evaluate_answer_similarity(correct_answer, user_answer)

        # If similarity is above 70%, consider it correct
        if similarity_score >= 0.7:
            session['score'] += 1

        session['current_question'] += 1
        return redirect(url_for('show_question'))

    return render_template('test.html',
                           question=question,
                           current_question=current_question,
                           total_questions=len(questions))


def evaluate_answer_similarity(reference_answer, user_answer):
    genai.configure(api_key='AIzaSyAM8hWwGWv5B9pTCnf14Q-Ck_gkukWUrN8')
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    Compare these two answers and provide a similarity score between 0 and 1:
    Reference Answer: {reference_answer}
    User Answer: {user_answer}
    Consider the following when scoring:
    - Semantic meaning (0.6 weight)
    - Key concepts covered (0.3 weight)
    - Technical accuracy (0.1 weight)
    Return ONLY the numerical score between 0 and 1 with no additional text.
    """
    try:
        response = model.generate_content(prompt)
        score = float(response.text.strip())
        return min(max(score, 0), 1)  # Ensure score is between 0 and 1
    except Exception as e:
        print(f"Error evaluating answer: {e}")
        return 0  # Default to 0 if evaluation fails


@app.route('/result')
def result():
    score = session.get('score', 0)
    total_questions = len(session.get('questions', []))
    percentage = (score / total_questions) * 100 if total_questions > 0 else 0

    if percentage >= 70:
        return redirect(url_for('next_page'))

    return render_template('result.html',
                           score=score,
                           total_questions=total_questions,
                           percentage=percentage)

@app.route('/next_page')
def next_page():
    return render_template('final.html')

if __name__ == '__main__':
    app.run(debug=True)