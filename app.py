from flask import Flask, request, jsonify, render_template,redirect,url_for,flash,session
import google.generativeai as genai
from nltk.tokenize import sent_tokenize, word_tokenize
import re
from nltk import FreqDist
from nltk.corpus import stopwords
import nltk
import sqlite3
from datetime import datetime
import random,os,csv
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
    course_videos = {
        'Python': [
            {'title': 'Python Full Course for Beginners', 'video_id': 'rfscVS0vtbw', 'duration': '4:26:52'},
            {'title': 'Python OOP Tutorial', 'video_id': 'Ej_02ICOIgs', 'duration': '53:06'},
            {'title': 'Python Django Tutorial', 'video_id': 'F5mRW0jo-U4', 'duration': '1:02:07'}
        ],
        'Java': [
            {'title': 'Java Programming Tutorial', 'video_id': 'grEKMHGYyns', 'duration': '12:13:29'},
            {'title': 'Spring Boot Crash Course', 'video_id': '9SGDpanrc8U', 'duration': '2:12:53'},
            {'title': 'Java OOP Concepts', 'video_id': 'bIeqAlmNRrA', 'duration': '30:17'}
        ],
        'JavaScript': [
            {'title': 'JavaScript Crash Course', 'video_id': 'hdI2bqOjy3c', 'duration': '1:40:30'},
            {'title': 'ES6+ Features', 'video_id': 'NCwa_xi0Uuc', 'duration': '35:22'},
            {'title': 'Async JavaScript', 'video_id': 'PoRJizFvM7s', 'duration': '25:36'}
        ],
        'C': [
            {'title': 'C Programming Tutorial', 'video_id': 'KJgsSFOSQv0', 'duration': '3:46:13'},
            {'title': 'Pointers in C', 'video_id': 'zuegQmMdy8M', 'duration': '32:04'},
            {'title': 'Data Structures in C', 'video_id': 'B31LgI4Y4DQ', 'duration': '3:06:30'}
        ],
        'C++': [
            {'title': 'C++ Tutorial for Beginners', 'video_id': 'vLnPwxZdW4Y', 'duration': '4:01:19'},
            {'title': 'C++ OOP Concepts', 'video_id': 'wN0x9eZLix4', 'duration': '42:41'},
            {'title': 'STL in C++', 'video_id': 'LyGlTmaWEPs', 'duration': '1:03:58'}
        ],
        'C#': [
            {'title': 'C# Tutorial - Full Course', 'video_id': 'GhQdlIFylQ8', 'duration': '4:31:09'},
            {'title': 'ASP.NET Core Tutorial', 'video_id': 'C5cnZ-gZy2I', 'duration': '1:10:21'},
            {'title': 'Unity with C#', 'video_id': 'XtQMytORBmM', 'duration': '2:35:47'}
        ],
        'Ruby': [
            {'title': 'Ruby Programming Language', 'video_id': 't_ispmWmdjY', 'duration': '2:24:55'},
            {'title': 'Ruby on Rails Tutorial', 'video_id': 'B3Fbujmgo60', 'duration': '3:17:18'},
            {'title': 'Ruby Metaprogramming', 'video_id': '8E6Bk-t0gH8', 'duration': '28:42'}
        ],
        'Go': [
            {'title': 'Golang Tutorial', 'video_id': 'YS4e4q9oBaU', 'duration': '3:23:33'},
            {'title': 'Concurrency in Go', 'video_id': 'LvgVSSpwNDM', 'duration': '31:42'},
            {'title': 'Building APIs with Go', 'video_id': 'SonwZ6MF5BE', 'duration': '1:05:28'}
        ],
        'Rust': [
            {'title': 'Rust Programming Course', 'video_id': 'MsocPEZBd-M', 'duration': '5:21:03'},
            {'title': 'Rust for Beginners', 'video_id': 'zF34dRivLOw', 'duration': '1:29:47'},
            {'title': 'Rust Ownership Explained', 'video_id': 'VFIOSWy93H0', 'duration': '24:18'}
        ],
        'Swift': [
            {'title': 'SwiftUI Tutorial', 'video_id': 'F2ojC6TNwws', 'duration': '4:36:58'},
            {'title': 'iOS Development with Swift', 'video_id': 'EMlM6QTzJo0', 'duration': '3:43:22'},
            {'title': 'Swift Protocol-Oriented Programming', 'video_id': 'lyzcERHGH_8', 'duration': '19:35'}
        ],
        'Kotlin': [
            {'title': 'Kotlin Tutorial for Beginners', 'video_id': 'F9UC9DY-vIU', 'duration': '2:37:09'},
            {'title': 'Android Development with Kotlin', 'video_id': 'BBWyXo-3JGQ', 'duration': '5:51:24'},
            {'title': 'Kotlin Coroutines', 'video_id': 'tmzLpyfY9pI', 'duration': '42:17'}
        ],
        'PHP': [
            {'title': 'PHP Programming Language', 'video_id': 'OK_JCtrrv-c', 'duration': '4:36:39'},
            {'title': 'Laravel PHP Framework', 'video_id': 'ImtZ5yENzgE', 'duration': '4:25:50'},
            {'title': 'PHP OOP Tutorial', 'video_id': 'Anz0ArcQ5kI', 'duration': '1:52:24'}
        ],
        'TypeScript': [
            {'title': 'TypeScript Full Course', 'video_id': 'd56mG7DezGs', 'duration': '3:25:51'},
            {'title': 'TypeScript with React', 'video_id': 'F2JCjVSZlG0', 'duration': '1:20:35'},
            {'title': 'TypeScript Generics', 'video_id': 'nViEqpgwxHE', 'duration': '15:42'}
        ],
        'R': [
            {'title': 'R Programming Tutorial', 'video_id': '_V8eKsto3Ug', 'duration': '2:10:39'},
            {'title': 'Data Science with R', 'video_id': 'uaRhJ0yN8Yw', 'duration': '1:51:22'},
            {'title': 'R Data Visualization', 'video_id': 'hSPmj7mK6ng', 'duration': '1:08:33'}
        ],
        'Scala': [
            {'title': 'Scala Tutorial for Beginners', 'video_id': 'DzFt0YkZo8M', 'duration': '3:08:28'},
            {'title': 'Functional Programming in Scala', 'video_id': 'WO4nJtPJhCI', 'duration': '1:06:40'},
            {'title': 'Scala with Apache Spark', 'video_id': 'GxG8X5jqJSA', 'duration': '1:12:15'}
        ],
        'Perl': [
            {'title': 'Perl Tutorial for Beginners', 'video_id': 'WEghIXs8F6c', 'duration': '2:04:34'},
            {'title': 'Perl Regular Expressions', 'video_id': 'vvQk7YQViOQ', 'duration': '28:17'},
            {'title': 'Perl Scripting Tutorial', 'video_id': 'J1Jqg8fyAgQ', 'duration': '1:02:45'}
        ],
        'Haskell': [
            {'title': 'Haskell for Beginners', 'video_id': '02_H3LjqMr8', 'duration': '1:29:15'},
            {'title': 'Functional Programming in Haskell', 'video_id': 'LnX3B9oaKzw', 'duration': '1:04:56'},
            {'title': 'Haskell Type System', 'video_id': '6COvD8oynmI', 'duration': '42:30'}
        ],
        'Dart': [
            {'title': 'Dart Programming Tutorial', 'video_id': 'Ej_Pcr4uC2Q', 'duration': '1:20:42'},
            {'title': 'Flutter with Dart', 'video_id': '1gDhl4leEzA', 'duration': '3:22:27'},
            {'title': 'Dart Null Safety', 'video_id': 'eBr7qdWpSfs', 'duration': '18:25'}
        ],
        'Elixir': [
            {'title': 'Elixir Tutorial for Beginners', 'video_id': 'pBNOavRoNL0', 'duration': '2:45:19'},
            {'title': 'Phoenix Framework', 'video_id': 'MZvmYaFkNJI', 'duration': '1:07:45'},
            {'title': 'Elixir OTP', 'video_id': '1aM7YQx7lX0', 'duration': '35:12'}
        ],
        'Clojure': [
            {'title': 'Clojure Tutorial', 'video_id': 'VdUzS5xuqXQ', 'duration': '1:40:22'},
            {'title': 'Functional Programming in Clojure', 'video_id': 'ciGyHkDuPAE', 'duration': '52:18'},
            {'title': 'ClojureScript Tutorial', 'video_id': 'KZk2MDF3I4I', 'duration': '1:08:33'}
        ],
        'Lua': [
            {'title': 'Lua Programming Tutorial', 'video_id': 'iMacxZQMPXs', 'duration': '1:27:05'},
            {'title': 'Lua for Game Development', 'video_id': 'rVZ1gIfNq5Q', 'duration': '1:52:44'},
            {'title': 'Lua Scripting Basics', 'video_id': 'SQdA7rvqLd4', 'duration': '24:16'}
        ],
        'Assembly': [
            {'title': 'Assembly Language Tutorial', 'video_id': 'HgEGAaYdABA', 'duration': '2:44:01'},
            {'title': 'x86 Assembly', 'video_id': 'wLXIWKUWpSs', 'duration': '1:15:20'},
            {'title': 'ARM Assembly', 'video_id': 'gfmRrPjnEYw', 'duration': '1:02:35'}
        ],
        'SQL': [
            {'title': 'SQL Tutorial for Beginners', 'video_id': 'HXV3zeQKqGY', 'duration': '4:20:39'},
            {'title': 'PostgreSQL Tutorial', 'video_id': 'qw--VYLpxG4', 'duration': '3:10:45'},
            {'title': 'SQL Performance Tuning', 'video_id': '8hGN7E5xw1Q', 'duration': '1:12:33'}
        ],
        'HTML/CSS': [
            {'title': 'HTML & CSS Full Course', 'video_id': 'G3e-cpL7ofc', 'duration': '6:18:38'},
            {'title': 'CSS Grid Tutorial', 'video_id': '9zBsdzdE4sM', 'duration': '1:25:39'},
            {'title': 'Responsive Web Design', 'video_id': 'srvUrASNj0s', 'duration': '2:11:22'}
        ],
        'React': [
            {'title': 'React JS Full Course', 'video_id': 'w7ejDZ8SWv8', 'duration': '4:25:40'},
            {'title': 'React Hooks Tutorial', 'video_id': 'TNhaISOUy6Q', 'duration': '1:28:37'},
            {'title': 'React with TypeScript', 'video_id': 'jrKcJxF0lAU', 'duration': '1:42:15'}
        ]
    }
    videos = course_videos.get(session['course'])
    return render_template('dashboard.html',
                           username=session['username'],
                           course=session.get('course', 'No Course Assigned'),
                           videos=videos)


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

#
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

    # Store test results in CSV
    store_test_results(
        username=session.get('username', 'Anonymous'),
        course=session.get('course', 'Unknown'),
        correct_answers=score,
        marks_obtained=score,
        max_marks=total_questions,
        percentage=percentage
    )

    if percentage >= 70:
        return redirect(url_for('next_page'))

    return render_template('result.html',
                           score=score,
                           total_questions=total_questions,
                           percentage=percentage)


def store_test_results(username, course, correct_answers, marks_obtained, max_marks, percentage):
    # CSV file path
    csv_file = 'test_results.csv'

    # Data to be stored
    data = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'username': username,
        'subject': course,
        'correct_answers': correct_answers,
        'marks_obtained': marks_obtained,
        'max_marks': max_marks,
        'percentage': f"{percentage:.2f}%"
    }

    try:
        # Check if file exists to determine if we need headers
        file_exists = os.path.isfile(csv_file)

        with open(csv_file, mode='a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=data.keys())

            if not file_exists:
                writer.writeheader()

            writer.writerow(data)
    except Exception as e:
        print(f"Error writing to CSV: {e}")


@app.route('/progress')
def progress():
    if 'username' not in session:
        return redirect(url_for('log'))

    # Read test results from CSV
    test_results = []
    try:
        with open('test_results.csv', mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['username'] == session['username']:
                    test_results.append(row)
    except FileNotFoundError:
        pass  # No results yet

    return render_template('progress.html',
                           username=session['username'],
                           test_results=test_results,
                           course=session.get('course', 'Unknown'))

@app.route('/next_page')
def next_page():
    return render_template('final.html')

if __name__ == '__main__':
    app.run(debug=True)