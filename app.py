from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
import google.generativeai as genai
from nltk.tokenize import sent_tokenize, word_tokenize
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
import re
from nltk import FreqDist
from nltk.corpus import stopwords
import nltk
import sqlite3
from datetime import datetime
import random, os, csv
import string
import numpy as np
import PyPDF2

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

def clean_markdown(text: str) -> str:
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'#+\s*', '', text)
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    text = re.sub(r'`{3}.*?`{3}', '', text, flags=re.DOTALL)
    text = re.sub(r'`(.*?)`', r'\1', text)
    text = re.sub(r'^\s*>+\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*[\*\-+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()

# Ensure NLTK data is downloaded
nltk.download('punkt')
nltk.download('stopwords')

@app.route('/', methods=['GET', 'POST'])
def homes():
    return render_template('index.html')

@app.route('/log',methods=['GET'])
def logs():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')

            # Basic validation
            if not username or not password:
                flash('Username and password are required', 'error')
                return redirect(url_for('logs'))

            # Database query
            connection = sqlite3.connect('users.db', check_same_thread=False)
            cursor = connection.cursor()
            cursor.execute("SELECT username, email, password, course FROM user_info WHERE username = ?", (username,))
            user = cursor.fetchone()
            connection.close()

            if not user:
                flash('Invalid username or password', 'error')
                return redirect(url_for('logs'))

            # Verify password (insecure - replace with proper password hashing)
            if password != user[2]:  # Compare with stored password
                flash('Invalid username or password', 'error')
                return redirect(url_for('logs'))

            # Successful login
            session['username'] = user[0]  # Username
            session['email'] = user[1]     # Email
            session['course'] = user[3]    # Course
            return redirect('/dashboard')

        except Exception as e:
            print(f"Login error: {str(e)}")
            flash('An error occurred during login', 'error')
            return redirect(url_for('logs'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('login'))


@app.route('/dashboard', methods=['GET', 'POST'])
def dash_board():
    if 'username' not in session:
        return redirect(url_for('log'))
    course_videos = {
        # 1. Python
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
        {'title': 'C# Full Course', 'video_id': 'GhQdlIFylQ8', 'duration': '4:31:09'},
        {'title': 'ASP.NET Core Tutorial', 'video_id': 'C5cnZ-gZy2I', 'duration': '1:10:21'},
        {'title': 'Unity with C#', 'video_id': 'XtQMytORBmM', 'duration': '2:35:47'}
    ],
    'Ruby': [
        {'title': 'Ruby Programming', 'video_id': 't_ispmWmdjY', 'duration': '2:24:55'},
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
        {'title': 'Kotlin for Beginners', 'video_id': 'F9UC9DY-vIU', 'duration': '2:37:09'},
        {'title': 'Android Development with Kotlin', 'video_id': 'BBWyXo-3JGQ', 'duration': '5:51:24'},
        {'title': 'Kotlin Coroutines', 'video_id': 'tmzLpyfY9pI', 'duration': '42:17'}
    ],
    'PHP': [
        {'title': 'PHP Programming', 'video_id': 'OK_JCtrrv-c', 'duration': '4:36:39'},
        {'title': 'Laravel Framework', 'video_id': 'ImtZ5yENzgE', 'duration': '4:25:50'},
        {'title': 'PHP OOP Tutorial', 'video_id': 'Anz0ArcQ5kI', 'duration': '1:52:24'}
    ],
    'TypeScript': [
        {'title': 'TypeScript Full Course', 'video_id': 'd56mG7DezGs', 'duration': '3:25:51'},
        {'title': 'TypeScript with React', 'video_id': 'F2JCjVSZlG0', 'duration': '1:20:35'},
        {'title': 'TypeScript Generics', 'video_id': 'nViEqpgwxHE', 'duration': '15:42'}
    ],
    'Scala': [
        {'title': 'Scala Programming Tutorial', 'video_id': 'h8i9j0k1l2m3', 'duration': '3:30:22'},
        {'title': 'Functional Programming in Scala', 'video_id': 'i9j0k1l2m3n4', 'duration': '1:15:45'},
        {'title': 'Akka Actors in Scala', 'video_id': 'j0k1l2m3n4o5', 'duration': '2:00:30'}
    ],
    'Perl': [
        {'title': 'Perl Programming Basics', 'video_id': 'o5p6q7r8s9t0', 'duration': '2:20:15'},
        {'title': 'Perl for System Administration', 'video_id': 'p6q7r8s9t0u1', 'duration': '1:45:30'},
        {'title': 'Regular Expressions in Perl', 'video_id': 'q7r8s9t0u1v2', 'duration': '50:22'}
    ],
    'Haskell': [
        {'title': 'Haskell for Beginners', 'video_id': 'v2w3x4y5z6a7', 'duration': '3:10:40'},
        {'title': 'Functional Programming in Haskell', 'video_id': 'w3x4y5z6a7b8', 'duration': '1:20:15'},
        {'title': 'Haskell Monads Explained', 'video_id': 'x4y5z6a7b8c9', 'duration': '45:30'}
    ],
    'Dart': [
        {'title': 'Dart Programming Tutorial', 'video_id': 'c9d0e1f2g3h4', 'duration': '2:50:33'},
        {'title': 'Flutter with Dart', 'video_id': 'd0e1f2g3h4i5', 'duration': '4:15:22'},
        {'title': 'Dart Asynchronous Programming', 'video_id': 'e1f2g3h4i5j6', 'duration': '40:15'}
    ],
    'Elixir': [
        {'title': 'Elixir Programming Basics', 'video_id': 'j6k7l8m9n0o1', 'duration': '2:45:10'},
        {'title': 'Phoenix Framework Tutorial', 'video_id': 'k7l8m9n0o1p2', 'duration': '3:30:45'},
        {'title': 'Elixir Concurrency Model', 'video_id': 'l8m9n0o1p2q3', 'duration': '50:22'}
    ],
    'Clojure': [
        {'title': 'Clojure Programming Tutorial', 'video_id': 'q3r4s5t6u7v8', 'duration': '3:00:22'},
        {'title': 'Functional Programming in Clojure', 'video_id': 'r4s5t6u7v8w9', 'duration': '1:25:45'},
        {'title': 'ClojureScript for Web', 'video_id': 's5t6u7v8w9x0', 'duration': '2:10:30'}
    ],
    'Lua': [
        {'title': 'Lua Programming Basics', 'video_id': 'x0y1z2a3b4c5', 'duration': '2:15:30'},
        {'title': 'Lua for Game Development', 'video_id': 'y1z2a3b4c5d6', 'duration': '3:00:45'},
        {'title': 'Lua Scripting in Roblox', 'video_id': 'z2a3b4c5d6e7', 'duration': '1:45:22'}
    ],
    'Assembly': [
        {'title': 'Assembly Language Basics', 'video_id': 'e7f8g9h0i1j2', 'duration': '3:30:22'},
        {'title': 'x86 Assembly Tutorial', 'video_id': 'f8g9h0i1j2k3', 'duration': '2:00:45'},
        {'title': 'Assembly for Reverse Engineering', 'video_id': 'g9h0i1j2k3l4', 'duration': '1:45:30'}
    ],
    'SQL': [
        {'title': 'SQL for Beginners', 'video_id': 'l4m5n6o7p8q9', 'duration': '2:45:33'},
        {'title': 'Advanced SQL Queries', 'video_id': 'm5n6o7p8q9r0', 'duration': '1:30:45'},
        {'title': 'Database Design with SQL', 'video_id': 'n6o7p8q9r0s1', 'duration': '2:00:22'}
    ],
    'HTML/CSS': [
        {'title': 'HTML & CSS Full Course', 'video_id': 's1t2u3v4w5x6', 'duration': '3:45:22'},
        {'title': 'Responsive Web Design', 'video_id': 't2u3v4w5x6y7', 'duration': '2:00:45'},
        {'title': 'CSS Grid and Flexbox', 'video_id': 'u3v4w5x6y7z8', 'duration': '1:30:30'}
    ],
    'React': [
        {'title': 'React.js Crash Course', 'video_id': 'z8a9b0c1d2e3', 'duration': '2:30:22'},
        {'title': 'React Hooks Tutorial', 'video_id': 'a9b0c1d2e3f4', 'duration': '1:15:45'},
        {'title': 'React with Redux', 'video_id': 'b0c1d2e3f4g5', 'duration': '1:45:30'}
    ],
    'Angular': [
        {'title': 'Angular Full Course', 'video_id': 'g5h6i7j8k9l0', 'duration': '4:00:33'},
        {'title': 'Angular Components', 'video_id': 'h6i7j8k9l0m1', 'duration': '1:20:45'},
        {'title': 'Angular Services and DI', 'video_id': 'i7j8k9l0m1n2', 'duration': '1:15:30'}
    ],
    'Vue': [
        {'title': 'Vue.js Crash Course', 'video_id': 'n2o3p4q5r6s7', 'duration': '2:15:22'},
        {'title': 'Vue 3 Features', 'video_id': 'o3p4q5r6s7t8', 'duration': '1:10:45'},
        {'title': 'Vue with Vuex', 'video_id': 'p4q5r6s7t8u9', 'duration': '1:30:30'}
    ],
    'MATLAB': [
        {'title': 'MATLAB for Beginners', 'video_id': 'u9v0w1x2y3z4', 'duration': '3:00:33'},
        {'title': 'MATLAB for Data Analysis', 'video_id': 'v0w1x2y3z4a5', 'duration': '1:45:45'},
        {'title': 'MATLAB Plotting Techniques', 'video_id': 'w1x2y3z4a5b6', 'duration': '1:15:30'}
    ],
    'Julia': [
        {'title': 'Julia Programming Tutorial', 'video_id': 'b6c7d8e9f0g1', 'duration': '2:45:22'},
        {'title': 'Julia for Data Science', 'video_id': 'c7d8e9f0g1h2', 'duration': '1:30:45'},
        {'title': 'Julia Numerical Computing', 'video_id': 'd8e9f0g1h2i3', 'duration': '1:15:30'}
    ],
    'Groovy': [
        {'title': 'Groovy Programming Basics', 'video_id': 'i3j4k5l6m7n8', 'duration': '2:30:33'},
        {'title': 'Groovy with Grails', 'video_id': 'j4k5l6m7n8o9', 'duration': '3:00:45'},
        {'title': 'Groovy Scripting', 'video_id': 'k5l6m7n8o9p0', 'duration': '1:15:30'}
    ],
    'Objective-C': [
        {'title': 'Objective-C Basics', 'video_id': 'p0q1r2s3t4u5', 'duration': '2:45:22'},
        {'title': 'iOS Development with Objective-C', 'video_id': 'q1r2s3t4u5v6', 'duration': '3:30:45'},
        {'title': 'Objective-C Memory Management', 'video_id' : 'r2s3t4u5v6w7', 'duration': '1:15:30'}
    ],
    'F#': [
        {'title': 'F# Programming Tutorial', 'video_id': 'w7x8y9z0a1b2', 'duration': '2:30:33'},
        {'title': 'Functional Programming in F#', 'video_id': 'x8y9z0a1b2c3', 'duration': '1:15:45'},
        {'title': 'F# for Data Science', 'video_id': 'y9z0a1b2c3d4', 'duration': '1:45:30'}
    ],
    'Fortran': [
        {'title': 'Fortran Programming Basics', 'video_id': 'd4e5f6g7h8i9', 'duration': '2:45:22'},
        {'title': 'Fortran for Scientific Computing', 'video_id': 'e5f6g7h8i9j0', 'duration': '2:00:45'},
        {'title': 'Fortran Parallel Programming', 'video_id': 'f6g7h8i9j0k1', 'duration': '1:30:30'}
    ],
    'Erlang': [
        {'title': 'Erlang Programming Tutorial', 'video_id': 'k1l2m3n4o5p6', 'duration': '2:30:33'},
        {'title': 'Erlang Concurrency', 'video_id': 'l2m3n4o5p6q7', 'duration': '1:15:45'},
        {'title': 'Building Systems with Elixir', 'video_id': 'm3n4o5p6q7r8', 'duration': '1:45:30'}
    ],
    'D': [
        {'title': 'D Programming Basics', 'video_id': 'r8s9t0u1v2w3', 'duration': '2:15:22'},
        {'title': 'D for Systems Programming', 'video_id': 's9t0u1v2w3x4', 'duration': '1:45:45'},
        {'title': 'D Performance Optimization', 'video_id': 't0u1v2w3x4y5', 'duration': '1:15:30'}
    ],
    'COBOL': [
        {'title': 'COBOL Programming Basics', 'video_id': 'y5z6a7b8c9d0', 'duration': '2:45:33'},
        {'title': 'COBOL for Mainframes', 'video_id': 'z6a7b8c9d0e1', 'duration': '2:00:45'},
        {'title': 'COBOL Data Processing', 'video_id': 'a7b8c9d0e1f2', 'duration': '1:30:30'}
    ],
    'Lisp': [
        {'title': 'Lisp Programming Tutorial', 'video_id': 'f2g3h4i5j6k7', 'duration': '2:30:22'},
        {'title': 'Functional Programming in Lisp', 'video_id': 'g3h4i5j6k7l8', 'duration': '1:15:45'},
        {'title': 'Lisp for AI Development', 'video_id': 'h4i5j6k7l8m9', 'duration': '1:45:30'}
    ],
    'Prolog': [
        {'title': 'Prolog Programming Basics', 'video_id': 'm9n0o1p2q3r4', 'duration': '2:15:33'},
        {'title': 'Prolog for AI', 'video_id': 'n0o1p2q3r4s5', 'duration': '1:45:45'},
        {'title': 'Logic Programming in Prolog', 'video_id': 'o1p2q3r4s5t6', 'duration': '1:15:30'}
    ],
    'Ada': [
        {'title': 'Ada Programming Tutorial', 'video_id': 't6u7v8w9x0y1', 'duration': '2:45:22'},
        {'title': 'Ada for Embedded Systems', 'video_id': 'u7v8w9x0y1z2', 'duration': '2:00:45'},
        {'title': 'Ada Tasking', 'video_id': 'v8w9x0y1z2a3', 'duration': '1:30:30'}
    ],
    'Crystal': [
        {'title': 'Crystal Programming Basics', 'video_id': 'a3b4c5d6e7f8', 'duration': '2:30:33'},
        {'title': 'Crystal for Web Development', 'video_id': 'b4c5d6e7f8g9', 'duration': '1:45:45'},
        {'title': 'Crystal Performance Tips', 'video_id': 'c5d6e7f8g9h0', 'duration': '1:15:30'}
    ],
    'Nim': [
        {'title': 'Nim Programming Tutorial', 'video_id': 'h0i1j2k3l4m5', 'duration': '2:15:22'},
        {'title': 'Nim for Systems Programming', 'video_id': 'i1j2k3l4m5n6', 'duration': '1:45:45'},
        {'title': 'Nim Metaprogramming', 'video_id': 'j2k3l4m5n6o7', 'duration': '1:15:30'}
    ],
    'Zig': [
        {'title': 'Zig Programming Basics', 'video_id': 'o7p8q9r0s1t2', 'duration': '2:30:33'},
        {'title': 'Zig for Systems Programming', 'video_id': 'p8q9r0s1t2u3', 'duration': '1:45:45'},
        {'title': 'Zig Memory Management', 'video_id': 'q9r0s1t2u3v4', 'duration': '1:15:30'}
    ],
    'Bash': [
        {'title': 'Bash Scripting Tutorial', 'video_id': 'v4w5x6y7z8a9', 'duration': '2:15:22'},
        {'title': 'Advanced Bash Scripting', 'video_id': 'w5x6y7z8a9b0', 'duration': '1:45:45'},
        {'title': 'Bash for Automation', 'video_id': 'x6y7z8a9b0c1', 'duration': '1:30:30'}
    ],
    'PowerShell': [
        {'title': 'PowerShell Basics', 'video_id': 'c1d2e3f4g5h6', 'duration': '2:30:33'},
        {'title': 'PowerShell for System Admins', 'video_id': 'd2e3f4g5h6i7', 'duration': '1:45:45'},
        {'title': 'PowerShell Scripting', 'video_id': 'e3f4g5h6i7j8', 'duration': '1:30:30'}
    ],
    'Shell': [
        {'title': 'Shell Scripting Tutorial', 'video_id': 'j8k9l0m1n2o3', 'duration': '2:15:22'},
        {'title': 'Advanced Shell Scripting', 'video_id': 'k9l0m1n2o3p4', 'duration': '1:45:45'},
        {'title': 'Shell for Automation', 'video_id': 'l0m1n2o3p4q5', 'duration': '1:30:30'}
    ],
    'Pascal': [
        {'title': 'Pascal Programming Basics', 'video_id': 'q5r6s7t8u9v0', 'duration': '2:30:33'},
        {'title': 'Pascal for Beginners', 'video_id': 'r6s7t8u9v0w1', 'duration': '1:45:45'},
        {'title': 'Pascal Data Structures', 'video_id': 's7t8u9v0w1x2', 'duration': '1:30:30'}
    ],
    'OCaml': [
        {'title': 'OCaml Programming Tutorial', 'video_id': 'x2y3z4a5b6c7', 'duration': '2:15:22'},
        {'title': 'Functional Programming in OCaml', 'video_id': 'y3z4a5b6c7d8', 'duration': '1:45:45'},
        {'title': 'OCaml Type System', 'video_id': 'z4a5b6c7d8e9', 'duration': '1:15:30'}
    ],
    'Racket': [
        {'title': 'Racket Programming Basics', 'video_id': 'e9f0g1h2i3j4', 'duration': '2:30:33'},
        {'title': 'Functional Programming in Racket', 'video_id': 'f0g1h2i3j4k5', 'duration': '1:45:45'},
        {'title': 'Racket for DSLs', 'video_id': 'g1h2i3j4k5l6', 'duration': '1:30:30'}
    ],
    'Smalltalk': [
        {'title': 'Smalltalk Programming Tutorial', 'video_id': 'l6m7n8o9p0q1', 'duration': '2:15:22'},
        {'title': 'Smalltalk OOP Concepts', 'video_id': 'm7n8o9p0q1r2', 'duration': '1:45:45'},
        {'title': 'Smalltalk for GUI Apps', 'video_id': 'n8o9p0q1r2s3', 'duration': '1:30:30'}
    ],
    'Solidity': [
        {'title': 'Solidity for Beginners', 'video_id': 's3t4u5v6w7x8', 'duration': '2:30:33'},
        {'title': 'Smart Contracts with Solidity', 'video_id': 't4u5v6w7x8y9', 'duration': '1:45:45'},
        {'title': 'Solidity Security Best Practices', 'video_id': 'u5v6w7x8y9z0', 'duration': '1:30:30'}
    ]
}
    videos = course_videos.get(session['course'])
    return render_template('dashboard.html',
                           username=session['username'],
                           course=session.get('course', 'No Course Assigned'),
                           videos=videos)



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

            if not all([username, email, password, course]):
                return jsonify({"success": False, "message": "All fields are required"}), 400

            if request.form.get('confirm-password') != password:
                return jsonify({"success": False, "message": "Passwords do not match"}), 400

            cursor.execute(
                "INSERT INTO user_info (username, email, password, course) VALUES (?, ?, ?, ?)",
                (username, email, password, course)
            )
            connection.commit()

            return jsonify({
                "success": True,
                "message": "Registration successful!",
                "redirect": "/log"
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
    model = genai.GenerativeModel('gemini-2.0-flash')
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

@app.route('/upload', methods=['GET','POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "No file selected"}), 400

    try:
        if file and file.filename.lower().endswith(('.pdf', '.txt', '.doc', '.docx')):
            # Extract text based on file type
            if file.filename.lower().endswith('.pdf'):
                pdf_reader = PyPDF2.PdfReader(file)
                text = ''
                for page in pdf_reader.pages:
                    text += page.extract_text() or ''
            else:  # .doc or .docx or any format files apart from pdf
                return jsonify({"success": False, "error": "DOC/DOCX files are not supported yet"}), 400

            # Store the document text in session
            session['document_text'] = text
            session['document_name'] = file.filename

            # Generate 5W questions based on document content
            questions = generate_5w_questions(text[:1000])  # Limit to first 1000 chars to avoid token limits

            return jsonify({
                "success": True,
                "message": f"File '{file.filename}' uploaded successfully.",
                "questions": questions
            })
        else:
            return jsonify({"success": False, "error": "Unsupported file type"}), 400
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return jsonify({"success": False, "error": "Error processing file"}), 500

@app.route('/clear-document', methods=['POST'])
def clear_document():
    try:
        session.pop('document_text', None)
        session.pop('document_name', None)
        return jsonify({"success": True, "message": "Document cleared from session"})
    except Exception as e:
        print(f"Error clearing document: {str(e)}")
        return jsonify({"success": False, "error": "Error clearing document"}), 500


@app.route('/chat', methods=['POST'])
def chatting():
    if request.method == 'POST':
        try:
            data = request.get_json()
            user_message = data.get('message', '').strip()
            context = data.get('context', 'general')

            if not user_message:
                return jsonify({
                    'response': "Please provide a message.",
                    'questions': {
                        'what': [],
                        'where': [],
                        'when': [],
                        'why': [],
                        'who': []
                    },
                    'sentiment': {
                        'gemini': None,
                        'final_emotion': None,
                        'show_popup': False,
                        'sentiment_description': "No message provided for sentiment analysis."
                    }
                }), 400

            genai.configure(api_key='AIzaSyCOoAQyClkN6jGPl5iskpU0knbnERA-gVE')
            model = genai.GenerativeModel('gemini-2.0-flash')
            document_text = session.get('document_text', '')
            document_name = session.get('document_name', '')

            emotion_prompt = f"""
            Analyze the emotion in the following text and classify it as one of the following: 
            'happy', 'sad', 'angry', 'surprised', 'fearful', or 'neutral'. 
            Text: {user_message}
            Return only the emotion label (happy, sad, angry, surprised, fearful, or neutral).
            """
            try:
                emotion_response = model.generate_content(emotion_prompt)
                gemini_emotion = emotion_response.text.strip().lower() if emotion_response.text else 'neutral'
            except Exception as e:
                print(f"Error in Gemini sentiment analysis: {e}")
                gemini_emotion = 'neutral'
            final_emotion = gemini_emotion
            show_popup = bool(gemini_emotion != 'neutral')  # Show popup for non-neutral emotions

            # Define emotion-specific descriptions
            emotion_descriptions = {
                'happy': f"Your message '{user_message}' conveys a happy emotion, reflecting joy or satisfaction. That's wonderful to see! Keep sharing your positive vibes!",
                'sad': f"Your message '{user_message}' expresses a sad emotion, indicating a sense of sorrow or disappointment. We're here to support you—feel free to share more.",
                'angry': f"Your message '{user_message}' shows an angry emotion, suggesting frustration or irritation. Let's explore this further to address any concerns.",
                'surprised': f"Your message '{user_message}' indicates a surprised emotion, reflecting astonishment or unexpected feelings. That's intriguing—tell me more!",
                'fearful': f"Your message '{user_message}' conveys a fearful emotion, suggesting worry or anxiety. We're here to help—let us know how we can assist.",
                'neutral': f"Your message '{user_message}' has a neutral emotion, indicating a balanced or factual tone. Great to have a clear perspective!"
            }

            sentiment_description = emotion_descriptions.get(
                final_emotion,
                f"Your message '{user_message}' was analyzed, but the emotion is unclear. Please provide more context!"
            )

            if document_text:
                prompt = f"""
                Based on the following document content, provide a detailed response to the user's query: '{user_message}'.
                Document: {document_text[:20000]}  # Limit to avoid token issues

                If the query is not directly related to the document, provide a general response but mention the document context where relevant.
                Additionally, summarize the document in up to 5 key points.
                """
                try:
                    response = model.generate_content(prompt)
                    generated_text = clean_text(
                        response.text) if response.text else "Sorry, I couldn't process the document content."
                    # Extract key points from document
                    key_points = convert_paragraph_to_points(document_text, num_points=5)
                    generated_text += "\n\n**Document Key Points**:\n" + "\n".join(
                        [f"- {point}" for point in key_points])
                except Exception as e:
                    print(f"Error generating response with document: {e}")
                    generated_text = "Sorry, I couldn't process the document content."

                # Generate 5W questions based on document
                questions = generate_5w_questions(document_text[:1000])
            else:
                # General response without document
                response_prompt = f"Provide a detailed response to: {user_message}"
                try:
                    response = model.generate_content(response_prompt)
                    generated_text = clean_text(
                        clean_markdown(response.text)) if response.text else "Sorry, I couldn't generate a response."
                except Exception as e:
                    print(f"Error generating response: {e}")
                    generated_text = "Sorry, I couldn't generate a response."
                questions = generate_5w_questions(user_message)

            return jsonify({
                'response': generated_text,
                'questions': questions,
                'sentiment': {
                    'gemini': gemini_emotion,
                    'final_emotion': final_emotion,
                    'show_popup': show_popup,
                    'sentiment_description': sentiment_description
                }
            })

        except Exception as e:
            print(f"Error in /chat route: {str(e)}")
            return jsonify({
                'response': "An error occurred while processing your request.",
                'questions': {
                    'what': [],
                    'where': [],
                    'when': [],
                    'why': [],
                    'who': []
                },
                'sentiment': {
                    'gemini': None,
                    'final_emotion': None,
                    'show_popup': False,
                    'sentiment_description': "Error during sentiment analysis."
                }
            }), 500
@app.route('/course', methods=['GET', 'POST'])
def courses():
    today = datetime.today().weekday()
    course_info = []
    if today == 2:
        genai.configure(api_key='AIzaSyAM8hWwGWv5B9pTCnf14Q-Ck_gkukWUrN8')
        model = genai.GenerativeModel('gemini-2.0-flash')
        content = model.generate_content(f"Give me the information about the {session['course']}")
        generated_text = content.text
        key_points = convert_paragraph_to_points(generated_text)
        description = [clean_text(item) for item in key_points]
        days = {0: "Monday", 1: 'Tuesday', 2: "Wednesday", 3: "Thursday", 4: "Friday", 5: "Saturday", 6: 'Sunday'}
        room_name = days[today]
        course_info.append({
            "name": session['course'],
            "description": description,
            "meeting_link": f"https://meet.jit.si/{room_name}+{session['course']}"
        })
    return render_template('discussion.html', courses=course_info, is_wednesday=(today == 2))


@app.route('/test', methods=['GET', 'POST'])
def test():
    genai.configure(api_key='AIzaSyAM8hWwGWv5B9pTCnf14Q-Ck_gkukWUrN8')
    model = genai.GenerativeModel('gemini-2.0-flash')

    prompt = f"""
        Generate exactly 10 high-quality multiple choice questions about {session['course']}.
        Each question must:
        - Be clear and specific
        - Have 4 plausible options (a, b, c, d)
        - Include one clearly correct answer
        - Have 3 incorrect but related distractors
        - Avoid using "all of the above" or "none of the above"
        - Mark the correct answer with (correct)

        Format example:
        1. What is the primary purpose of a constructor in object-oriented programming?
        a) To destroy objects when they're no longer needed
        b) To initialize new objects (correct)
        c) To perform arithmetic calculations
        d) To display output to the console

        Now generate 10 questions about {session['course']} following this exact format.
        """

    try:
        content = model.generate_content(prompt)
        generated_text = content.text

        questions = []
        current_question = None
        lines = [line.strip() for line in generated_text.split('\n') if line.strip()]

        for line in lines:
            if re.match(r'^\d+\.', line):
                if current_question and len(current_question['options']) == 4:
                    questions.append(current_question)
                question_text = re.sub(r'^\d+\.', '', line).strip()
                current_question = {
                    'question': question_text,
                    'options': [],
                    'correct_answer': None
                }
            elif re.match(r'^[a-d]\)', line):
                if current_question and len(current_question['options']) < 4:
                    option_text = re.sub(r'^[a-d]\)', '', line).strip()
                    if '(correct)' in option_text.lower():
                        option_text = option_text.replace('(correct)', '').strip()
                        current_question['correct_answer'] = option_text
                    current_question['options'].append(option_text)

        if current_question and len(current_question['options']) == 4 and current_question['correct_answer']:
            questions.append(current_question)

        if len(questions) < 10:
            needed = 10 - len(questions)
            fallback_prompt = f"""
                Generate {needed} additional high-quality MCQs about {session['course']} with:
                - One clearly correct answer
                - Three plausible but incorrect options
                - No "all/none of the above"
                """
            fallback_content = model.generate_content(fallback_prompt)
            # Parse additional questions similarly (simplified for brevity)
            # Assume fallback generates in the same format
            for line in fallback_content.text.split('\n'):
                if re.match(r'^\d+\.', line):
                    if current_question and len(current_question['options']) == 4:
                        questions.append(current_question)
                    question_text = re.sub(r'^\d+\.', '', line).strip()
                    current_question = {
                        'question': question_text,
                        'options': [],
                        'correct_answer': None
                    }
                elif re.match(r'^[a-d]\)', line):
                    if current_question and len(current_question['options']) < 4:
                        option_text = re.sub(r'^[a-d]\)', '', line).strip()
                        if '(correct)' in option_text.lower():
                            option_text = option_text.replace('(correct)', '').strip()
                            current_question['correct_answer'] = option_text
                        current_question['options'].append(option_text)

        if current_question and len(current_question['options']) == 4 and current_question['correct_answer']:
            questions.append(current_question)

        session['questions'] = questions[:10]
        session['current_question'] = 0
        session['score'] = 0
        session['user_answers'] = []
        return redirect(url_for('show_question'))

    except Exception as e:
        print(f"Error generating questions: {e}")
        default_questions = []
        for i in range(1, 11):
            default_questions.append({
                'question': f"Sample question {i} about {session.get('course', 'this topic')}?",
                'options': [
                    f"Option A for question {i}",
                    f"Option B for question {i}",
                    f"Correct answer for question {i}",
                    f"Option D for question {i}"
                ],
                'correct_answer': f"Correct answer for question {i}"
            })
        session['questions'] = default_questions
        session['current_question'] = 0
        session['score'] = 0
        session['user_answers'] = []
        return redirect(url_for('show_question'))


@app.route('/question', methods=['GET', 'POST'])
def show_question():
    if 'questions' not in session:
        return redirect(url_for('test'))

    current_idx = session['current_question']
    questions = session['questions']

    if current_idx >= len(questions):
        return redirect(url_for('result'))

    if request.method == 'POST':
        user_answer = request.form.get('answer', '').strip()
        session['user_answers'].append(user_answer)

        correct_answer = questions[current_idx]['correct_answer']
        if user_answer.lower() == correct_answer.lower():
            session['score'] += 1

        session['current_question'] += 1
        return redirect(url_for('show_question'))

    current_q = questions[current_idx]
    options = current_q['options']
    correct = current_q['correct_answer']

    options = list(set(options))
    if correct not in options:
        options = options[:3] + [correct]
    random.shuffle(options)

    return render_template('test.html',
                           question=current_q['question'],
                           options=options,
                           current_question=current_idx + 1,
                           total_questions=len(questions),
                           correct_answer=correct)


def store_test_results(username, course, correct_answers, marks_obtained, max_marks, percentage):
    csv_file = 'test_results.csv'
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
        file_exists = os.path.isfile(csv_file)
        with open(csv_file, mode='a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=data.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(data)
    except Exception as e:
        print(f"Error writing to CSV: {e}")


@app.route('/result')
def result():
    questions = session.get('questions', [])
    user_answers = session.get('user_answers', [])
    score = session.get('score', 0)
    total = len(questions)
    percentage = (score / total) * 100 if total > 0 else 0

    # Store test results
    store_test_results(
        username=session.get('username', 'Unknown'),
        course=session.get('course', 'Unknown'),
        correct_answers=score,
        marks_obtained=score,
        max_marks=total,
        percentage=percentage
    )

    # Detailed results for display
    detailed_results = []
    for i, q in enumerate(questions):
        user_answer = user_answers[i] if i < len(user_answers) else "No answer"
        correct_answer = q['correct_answer']
        is_correct = user_answer.lower() == correct_answer.lower()
        detailed_results.append({
            'question': q['question'],
            'user_answer': user_answer,
            'correct_answer': correct_answer,
            'is_correct': is_correct
        })

    # Proficiency metrics
    accuracy = percentage
    correctness = [1 if d['is_correct'] else 0 for d in detailed_results]
    consistency = (1 - (np.std(correctness) / 0.5)) * 100 if correctness else 0
    time_per_question = session.get('time_per_question', [10] * total)
    avg_time = np.mean(time_per_question) if time_per_question else 10
    time_efficiency = max(0, 100 - (avg_time / 30))
    difficulties = [q.get('difficulty', 'medium') for q in questions]
    diff_map = {'easy': 1, 'medium': 2, 'hard': 3}
    weighted_score = sum(diff_map.get(d, 2) for i, d in enumerate(difficulties) if correctness[i] == 1)
    max_possible = sum(diff_map.get(d, 2) for d in difficulties)
    difficulty_handling = (weighted_score / max_possible) * 100 if max_possible > 0 else 0
    topics = {}
    for i, q in enumerate(questions):
        topic = q.get('topic', 'General')
        if topic not in topics:
            topics[topic] = {'total': 0, 'correct': 0}
        topics[topic]['total'] += 1
        topics[topic]['correct'] += correctness[i]
    topic_mastery = {t: (topics[t]['correct'] / topics[t]['total']) * 100 for t in topics}
    streak_pattern = []
    current_streak = 0
    for c in correctness:
        if c == 1:
            current_streak += 1
        else:
            if current_streak > 0:
                streak_pattern.append(f"+{current_streak}")
            current_streak = 0
    if current_streak > 0:
        streak_pattern.append(f"+{current_streak}")
    confidence_levels = session.get('confidence_levels', [1] * total)
    high_conf_correct = sum(1 for i in range(total) if confidence_levels[i] > 2 and correctness[i] == 1)
    overconfidence = sum(1 for i in range(total) if confidence_levels[i] > 2 and correctness[i] == 0)
    avg_options = sum(len(q['options']) for q in questions) / total if total > 0 else 4
    incorrect_count = total - score
    expected_random = (1 / avg_options) * total
    guessing_tendency = max(0, (incorrect_count - expected_random) / total * 100) if total > 0 else 0
    window_size = max(1, total // 3)
    learning_curve = [
        sum(correctness[i:i + window_size]) / window_size
        for i in range(0, total, window_size)
    ]
    error_clusters = []
    error_run = 0
    for c in correctness:
        if c == 0:
            error_run += 1
        else:
            if error_run > 1:
                error_clusters.append(f"{error_run} errors")
            error_run = 0
    if error_run > 1:
        error_clusters.append(f"{error_run} errors")

    proficiency = {
        'accuracy': accuracy,
        'consistency': consistency,
        'time_efficiency': time_efficiency,
        'difficulty_handling': difficulty_handling,
        'topic_mastery': topic_mastery,
        'streak_pattern': streak_pattern,
        'overconfidence': overconfidence,
        'guessing_tendency': guessing_tendency,
        'learning_curve': learning_curve,
        'error_clusters': error_clusters
    }

    return render_template('result.html',
                           score=score,
                           total=total,
                           percentage=percentage,
                           detailed_results=detailed_results,
                           proficiency=proficiency)


@app.route('/progress')
def progress():
    if 'username' not in session:
        return redirect(url_for('log'))

    genai.configure(api_key='AIzaSyAM8hWwGWv5B9pTCnf14Q-Ck_gkukWUrN8')
    model = genai.GenerativeModel('gemini-2.0-flash')

    test_results = []
    try:
        with open('test_results.csv', mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['username'] == session['username']:
                    row['percentage_float'] = float(row['percentage'].strip('%'))
                    test_results.append(row)
    except FileNotFoundError:
        pass

    test_results.sort(key=lambda x: x['timestamp'])

    progression_analysis = ""
    skill_trajectory = ""
    recommendations = ""

    if test_results:
        results_summary = "\n".join(
            f"{row['timestamp']}: {row['subject']} - {row['percentage']} (Score: {row['marks_obtained']}/{row['max_marks']})"
            for row in test_results
        )

        response = model.generate_content(
            f"Analyze this learning progression data and provide a detailed time-series "
            f"forecast for career growth potential in {session.get('course', 'the field')}:\n\n"
            f"{results_summary}\n\n"
            "Include: 1) Skill acquisition rate 2) Projected mastery timeline "
            "3) Comparison to industry benchmarks 4) Potential career milestones"
        )
        progression_analysis = response.text

        response = model.generate_content(
            f"Based on these test results over time, create a detailed skill trajectory "
            f"analysis for {session['username']}:\n\n{results_summary}\n\n"
            "Identify: 1) Core competencies developed 2) Emerging strengths "
            "3) Knowledge gaps to address 4) Recommended specialization paths"
        )
        skill_trajectory = response.text

        response = model.generate_content(
            f"Create a personalized 6-month upskilling roadmap for {session['username']} "
            f"based on these test results:\n\n{results_summary}\n\n"
            "Include: 1) Key skills to focus on 2) Recommended learning resources "
            "3) Project suggestions 4) Certification paths 5) Networking opportunities"
        )
        recommendations = response.text

        dates = [row['timestamp'] for row in test_results]
        percentages = [row['percentage_float'] for row in test_results]
        subjects = [row['subject'] for row in test_results]

        if len(dates) > 1:
            x = np.arange(len(dates))
            y = percentages
            coeff = np.polyfit(x, y, 1)
            forecast = np.polyval(coeff, np.arange(len(dates) + 3))
            forecast_dates = dates + [f"Future {i + 1}" for i in range(3)]
        else:
            forecast = []
            forecast_dates = []
    else:
        dates = []
        percentages = []
        subjects = []
        forecast = []
        forecast_dates = []

    return render_template('progress.html',
                           username=session['username'],
                           test_results=test_results,
                           course=session.get('course', 'Unknown'),
                           progression_analysis=progression_analysis,
                           skill_trajectory=skill_trajectory,
                           recommendations=recommendations,
                           dates=dates,
                           percentages=percentages,
                           subjects=subjects,
                           forecast=forecast,
                           forecast_dates=forecast_dates)


if __name__ == '__main__':
    app.run(debug=True)