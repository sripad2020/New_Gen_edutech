from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
import google.generativeai as genai
from nltk.tokenize import sent_tokenize, word_tokenize
from flask_login import UserMixin, logout_user, login_required
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
    {'title': 'Python Django Tutorial', 'video_id': 'F5mRW0jo-U4', 'duration': '1:02:07'},
    {'title': 'Python for Data Science', 'video_id': 'LHBE6Q9XlzI', 'duration': '3:42:17'},
    {'title': 'Python Flask Tutorial', 'video_id': 'Z1RJmh_OqeA', 'duration': '1:31:44'},
    {'title': 'Python Automation Tutorial', 'video_id': 'PXMJ6FS7llk', 'duration': '2:01:55'},
    {'title': 'Python for Machine Learning', 'video_id': '7eh4d6sabA0', 'duration': '6:14:20'}
],

'Java': [
    {'title': 'Java Programming Tutorial', 'video_id': 'grEKMHGYyns', 'duration': '12:13:29'},
    {'title': 'Spring Boot Crash Course', 'video_id': '9SGDpanrc8U', 'duration': '2:12:53'},
    {'title': 'Java OOP Concepts', 'video_id': 'bIeqAlmNRrA', 'duration': '30:17'},
    {'title': 'Java for Beginners', 'video_id': 'eIrMbAQSU34', 'duration': '9:00:34'},
    {'title': 'Java Multithreading Tutorial', 'video_id': '0hJm3Y5xkz4', 'duration': '1:10:42'},
    {'title': 'Java Streams API', 'video_id': 't1-YZ6bF-g0', 'duration': '58:12'},
    {'title': 'Java Data Structures & Algorithms', 'video_id': '8hly31xKli0', 'duration': '10:22:15'}
],

'JavaScript': [
    {'title': 'JavaScript Crash Course', 'video_id': 'hdI2bqOjy3c', 'duration': '1:40:30'},
    {'title': 'ES6+ Features', 'video_id': 'NCwa_xi0Uuc', 'duration': '35:22'},
    {'title': 'Async JavaScript', 'video_id': 'PoRJizFvM7s', 'duration': '25:36'},
    {'title': 'JavaScript DOM Tutorial', 'video_id': '0ik6X4DJKCc', 'duration': '1:12:15'},
    {'title': 'JavaScript Event Loop Explained', 'video_id': '8aGhZQkoFbQ', 'duration': '26:34'},
    {'title': 'JavaScript Design Patterns', 'video_id': 'tNm_NNSB3_w', 'duration': '2:10:44'},
    {'title': 'JavaScript Algorithms & Data Structures', 'video_id': 'M2bJBuaOeOQ', 'duration': '8:05:12'}
],

'C': [
    {'title': 'C Programming Tutorial', 'video_id': 'KJgsSFOSQv0', 'duration': '3:46:13'},
    {'title': 'Pointers in C', 'video_id': 'zuegQmMdy8M', 'duration': '32:04'},
    {'title': 'Data Structures in C', 'video_id': 'B31LgI4Y4DQ', 'duration': '3:06:30'},
    {'title': 'C Programming for Beginners', 'video_id': '8PopR3x-VMY', 'duration': '4:12:49'},
    {'title': 'Memory Management in C', 'video_id': 'nXvy5900m3M', 'duration': '58:20'},
    {'title': 'C File Handling Tutorial', 'video_id': 'hxO2qiwxY5g', 'duration': '29:50'},
    {'title': 'C Advanced Programming', 'video_id': 'yOyaJXpAYZQ', 'duration': '2:42:13'}
],

'C++': [
    {'title': 'C++ Tutorial for Beginners', 'video_id': 'vLnPwxZdW4Y', 'duration': '4:01:19'},
    {'title': 'C++ OOP Concepts', 'video_id': 'wN0x9eZLix4', 'duration': '42:41'},
    {'title': 'STL in C++', 'video_id': 'LyGlTmaWEPs', 'duration': '1:03:58'},
    {'title': 'C++ Templates Tutorial', 'video_id': 'I-hZkUa9mIs', 'duration': '54:25'},
    {'title': 'C++ Memory Management', 'video_id': 'nU5pZHQJ9go', 'duration': '1:17:12'},
    {'title': 'C++ Multithreading', 'video_id': 'dJYH1r2_r3I', 'duration': '1:32:45'},
    {'title': 'C++ Data Structures & Algorithms', 'video_id': '8hly31xKli0', 'duration': '10:22:15'}
],

'C#': [
    {'title': 'C# Full Course', 'video_id': 'GhQdlIFylQ8', 'duration': '4:31:09'},
    {'title': 'ASP.NET Core Tutorial', 'video_id': 'C5cnZ-gZy2I', 'duration': '1:10:21'},
    {'title': 'Unity with C#', 'video_id': 'XtQMytORBmM', 'duration': '2:35:47'},
    {'title': 'C# LINQ Tutorial', 'video_id': 'sYEK5saA1m8', 'duration': '1:02:55'},
    {'title': 'C# Advanced Topics', 'video_id': '6Xy2oxC0gss', 'duration': '2:14:19'},
    {'title': 'C# Design Patterns', 'video_id': 'wCz0g0m5_4A', 'duration': '1:25:35'},
    {'title': 'C# Multithreading', 'video_id': 'zJH8v1A6X3Q', 'duration': '1:50:05'}
],

        'Ruby': [
            {'title': 'Ruby Programming', 'video_id': 't_ispmWmdjY', 'duration': '2:24:55'},
            {'title': 'Ruby on Rails Tutorial', 'video_id': 'B3Fbujmgo60', 'duration': '3:17:18'},
            {'title': 'Ruby Metaprogramming', 'video_id': '8E6Bk-t0gH8', 'duration': '28:42'},
            {'title': 'Ruby for Beginners', 'video_id': 'UfU8udR8Kdk', 'duration': '1:48:10'},
            {'title': 'Ruby Blocks and Procs', 'video_id': 'z0lJ2k0lNfQ', 'duration': '42:31'},
            {'title': 'Ruby Gems Tutorial', 'video_id': '9QH0QtW2vG8', 'duration': '36:12'},
            {'title': 'Ruby on Rails API Mode', 'video_id': 'B2g2fW10Nhw', 'duration': '1:15:05'}
        ],

        'Go': [
            {'title': 'Golang Tutorial', 'video_id': 'YS4e4q9oBaU', 'duration': '3:23:33'},
            {'title': 'Concurrency in Go', 'video_id': 'LvgVSSpwNDM', 'duration': '31:42'},
            {'title': 'Building APIs with Go', 'video_id': 'SonwZ6MF5BE', 'duration': '1:05:28'},
            {'title': 'Go for Beginners', 'video_id': '8uiZC0l4Ajw', 'duration': '2:05:44'},
            {'title': 'Go Modules Tutorial', 'video_id': 'Z1VhG7cf83M', 'duration': '46:15'},
            {'title': 'Go Channels & Goroutines', 'video_id': '3CRUlpHfQAg', 'duration': '1:25:30'},
            {'title': 'Go Web Development', 'video_id': 'G3e-cpL7ofc', 'duration': '1:40:12'}
        ],

        'Rust': [
            {'title': 'Rust Programming Course', 'video_id': 'MsocPEZBd-M', 'duration': '5:21:03'},
            {'title': 'Rust for Beginners', 'video_id': 'zF34dRivLOw', 'duration': '1:29:47'},
            {'title': 'Rust Ownership Explained', 'video_id': 'VFIOSWy93H0', 'duration': '24:18'},
            {'title': 'Rust Error Handling', 'video_id': 'pnthPSk5LUA', 'duration': '1:05:55'},
            {'title': 'Rust Async Programming', 'video_id': 'd8LJ3cKqJ88', 'duration': '58:34'},
            {'title': 'Rust Data Structures', 'video_id': 'qD8sv3XhG6A', 'duration': '1:35:20'},
            {'title': 'Rust Web Development', 'video_id': 'o3n3vF6v7qg', 'duration': '2:12:45'}
        ],

        'Swift': [
            {'title': 'SwiftUI Tutorial', 'video_id': 'F2ojC6TNwws', 'duration': '4:36:58'},
            {'title': 'iOS Development with Swift', 'video_id': 'EMlM6QTzJo0', 'duration': '3:43:22'},
            {'title': 'Swift Protocol-Oriented Programming', 'video_id': 'lyzcERHGH_8', 'duration': '19:35'},
            {'title': 'Swift for Beginners', 'video_id': 'Ulp1Kimblg0', 'duration': '2:12:44'},
            {'title': 'SwiftUI Animations', 'video_id': 'DReytOJ8Ttg', 'duration': '1:10:20'},
            {'title': 'Swift Combine Framework', 'video_id': 'g0lQ5zxQd2A', 'duration': '55:15'},
            {'title': 'Advanced Swift', 'video_id': 'dGP8ES22X7I', 'duration': '1:25:36'}
        ],

        'Kotlin': [
            {'title': 'Kotlin for Beginners', 'video_id': 'F9UC9DY-vIU', 'duration': '2:37:09'},
            {'title': 'Android Development with Kotlin', 'video_id': 'BBWyXo-3JGQ', 'duration': '5:51:24'},
            {'title': 'Kotlin Coroutines', 'video_id': 'tmzLpyfY9pI', 'duration': '42:17'},
            {'title': 'Kotlin Object-Oriented Programming', 'video_id': '1QbZLJX5BBg', 'duration': '1:15:05'},
            {'title': 'Kotlin Android Jetpack Compose', 'video_id': 'ZL6D-dmF1lM', 'duration': '2:10:20'},
            {'title': 'Kotlin Multiplatform', 'video_id': 'FT2YfJAEJDE', 'duration': '1:35:40'},
            {'title': 'Kotlin Advanced Features', 'video_id': 'yRexWWM8grk', 'duration': '1:05:18'}
        ],

        'PHP': [
            {'title': 'PHP Programming', 'video_id': 'OK_JCtrrv-c', 'duration': '4:36:39'},
            {'title': 'Laravel Framework', 'video_id': 'ImtZ5yENzgE', 'duration': '4:25:50'},
            {'title': 'PHP OOP Tutorial', 'video_id': 'Anz0ArcQ5kI', 'duration': '1:52:24'},
            {'title': 'PHP for Beginners', 'video_id': 'oJbfyzaA2QA', 'duration': '2:14:55'},
            {'title': 'PHP MySQL Integration', 'video_id': 'tVKyqMKp4cA', 'duration': '1:05:40'},
            {'title': 'PHP API Development', 'video_id': 'R6cX7P8B3IQ', 'duration': '58:22'},
            {'title': 'Advanced PHP', 'video_id': '2eebptXfEvw', 'duration': '3:02:15'}
        ],

        'TypeScript': [
            {'title': 'TypeScript Full Course', 'video_id': 'd56mG7DezGs', 'duration': '3:25:51'},
            {'title': 'TypeScript with React', 'video_id': 'F2JCjVSZlG0', 'duration': '1:20:35'},
            {'title': 'TypeScript Generics', 'video_id': 'nViEqpgwxHE', 'duration': '15:42'},
            {'title': 'TypeScript for Beginners', 'video_id': 'BwuLxPH8IDs', 'duration': '1:15:18'},
            {'title': 'TypeScript Utility Types', 'video_id': 'rAy_3SIqT-E', 'duration': '42:10'},
            {'title': 'Advanced TypeScript', 'video_id': 'zQnBQ4tB3ZA', 'duration': '2:01:44'},
            {'title': 'TypeScript Decorators', 'video_id': 'XxVg_s8xAms', 'duration': '55:36'}
        ],
    'Lua': [
    {'title': 'Lua Programming Basics', 'video_id': 'x0y1z2a3b4c5', 'duration': '2:15:30'},
    {'title': 'Lua for Game Development', 'video_id': 'y1z2a3b4c5d6', 'duration': '3:00:45'},
    {'title': 'Lua Scripting in Roblox', 'video_id': 'z2a3b4c5d6e7', 'duration': '1:45:22'},
    {'title': 'Learn Lua in One Video', 'video_id': 'iMacxZQMPXs', 'duration': '2:12:55'},
    {'title': 'Lua Scripting Crash Course', 'video_id': 'SwJF3FJd8mA', 'duration': '1:06:30'},
    {'title': 'Lua for Beginners', 'video_id': 'C3lL8lbEohk', 'duration': '59:48'},
    {'title': 'Advanced Lua Programming', 'video_id': 'VvCyA9F0C_4', 'duration': '1:32:15'}
],

'Assembly': [
    {'title': 'Assembly Language Basics', 'video_id': 'e7f8g9h0i1j2', 'duration': '3:30:22'},
    {'title': 'x86 Assembly Tutorial', 'video_id': 'f8g9h0i1j2k3', 'duration': '2:00:45'},
    {'title': 'Assembly for Reverse Engineering', 'video_id': 'g9h0i1j2k3l4', 'duration': '1:45:30'},
    {'title': 'Assembly Language Programming', 'video_id': 'ViNnfoE56V8', 'duration': '2:54:27'},
    {'title': 'x86 Assembly Crash Course', 'video_id': '75gBFiFtAb8', 'duration': '1:20:14'},
    {'title': 'ARM Assembly Language', 'video_id': 'gfmRrPjnEw4', 'duration': '1:45:18'},
    {'title': 'Assembly Language for Beginners', 'video_id': 'M6S5n3K2mTk', 'duration': '1:36:11'}
],

'SQL': [
    {'title': 'SQL for Beginners', 'video_id': 'l4m5n6o7p8q9', 'duration': '2:45:33'},
    {'title': 'Advanced SQL Queries', 'video_id': 'm5n6o7p8q9r0', 'duration': '1:30:45'},
    {'title': 'Database Design with SQL', 'video_id': 'n6o7p8q9r0s1', 'duration': '2:00:22'},
    {'title': 'SQL Tutorial - Full Database Course', 'video_id': 'HXV3zeQKqGY', 'duration': '4:20:45'},
    {'title': 'SQL Joins Explained', 'video_id': '9yeOJ0ZMUYw', 'duration': '36:27'},
    {'title': 'Window Functions in SQL', 'video_id': 'AfP6MLc81Z0', 'duration': '42:11'},
    {'title': 'SQL Optimization Techniques', 'video_id': 'VFi5V3T2G6g', 'duration': '1:15:40'}
],

'HTML/CSS': [
    {'title': 'HTML & CSS Full Course', 'video_id': 's1t2u3v4w5x6', 'duration': '3:45:22'},
    {'title': 'Responsive Web Design', 'video_id': 't2u3v4w5x6y7', 'duration': '2:00:45'},
    {'title': 'CSS Grid and Flexbox', 'video_id': 'u3v4w5x6y7z8', 'duration': '1:30:30'},
    {'title': 'HTML Full Course', 'video_id': 'pQN-pnXPaVg', 'duration': '2:02:33'},
    {'title': 'CSS Flexbox Crash Course', 'video_id': 'JJSoEo8JSnc', 'duration': '33:11'},
    {'title': 'CSS Grid Layout Crash Course', 'video_id': 't6CBKf8K_Ac', 'duration': '36:22'},
    {'title': 'Advanced CSS Animations', 'video_id': 'zHUpx90NerM', 'duration': '1:15:12'}
],

'React': [
    {'title': 'React.js Crash Course', 'video_id': 'z8a9b0c1d2e3', 'duration': '2:30:22'},
    {'title': 'React Hooks Tutorial', 'video_id': 'a9b0c1d2e3f4', 'duration': '1:15:45'},
    {'title': 'React with Redux', 'video_id': 'b0c1d2e3f4g5', 'duration': '1:45:30'},
    {'title': 'React Tutorial for Beginners', 'video_id': 'w7ejDZ8SWv8', 'duration': '2:17:12'},
    {'title': 'React Router Tutorial', 'video_id': 'Law7wfdg_ls', 'duration': '58:49'},
    {'title': 'React State Management', 'video_id': '35lXWvCuM8o', 'duration': '1:22:15'},
    {'title': 'React Performance Optimization', 'video_id': '0ZJgIjIuY7U', 'duration': '46:20'}
],

'Angular': [
    {'title': 'Angular Full Course', 'video_id': 'g5h6i7j8k9l0', 'duration': '4:00:33'},
    {'title': 'Angular Components', 'video_id': 'h6i7j8k9l0m1', 'duration': '1:20:45'},
    {'title': 'Angular Services and DI', 'video_id': 'i7j8k9l0m1n2', 'duration': '1:15:30'},
    {'title': 'Angular Tutorial for Beginners', 'video_id': '3qBXWUpoPHo', 'duration': '2:11:17'},
    {'title': 'Angular Forms Tutorial', 'video_id': 'Fdf5aTYRW0E', 'duration': '58:40'},
    {'title': 'Angular Routing Tutorial', 'video_id': 'k5E2AVpwsko', 'duration': '1:12:05'},
    {'title': 'Angular Performance Best Practices', 'video_id': 'mQ7h1E6g1wM', 'duration': '1:05:18'}
],

'Vue': [
    {'title': 'Vue.js Crash Course', 'video_id': 'n2o3p4q5r6s7', 'duration': '2:15:22'},
    {'title': 'Vue 3 Features', 'video_id': 'o3p4q5r6s7t8', 'duration': '1:10:45'},
    {'title': 'Vue with Vuex', 'video_id': 'p4q5r6s7t8u9', 'duration': '1:30:30'},
    {'title': 'Vue.js Tutorial for Beginners', 'video_id': 'qZXt1Aom3Cs', 'duration': '3:03:15'},
    {'title': 'Vue Router Tutorial', 'video_id': '91OrK3CeW-A', 'duration': '1:05:44'},
    {'title': 'Vue 3 Composition API', 'video_id': 'wAZV2-9eGxY', 'duration': '58:37'},
    {'title': 'Vue.js Component Patterns', 'video_id': 'uNNl3vazfPQ', 'duration': '1:15:25'}
],
        'MATLAB': [
            {'title': 'MATLAB for Beginners', 'video_id': 'u9v0w1x2y3z4', 'duration': '3:00:33'},
            {'title': 'MATLAB for Data Analysis', 'video_id': 'v0w1x2y3z4a5', 'duration': '1:45:45'},
            {'title': 'MATLAB Plotting Techniques', 'video_id': 'w1x2y3z4a5b6', 'duration': '1:15:30'},
            {'title': 'MATLAB Programming Tutorial', 'video_id': 'bJFS2vRaX9s', 'duration': '2:45:22'},
            {'title': 'Simulink Basics', 'video_id': 'bZyQDv6W2Xg', 'duration': '1:12:15'},
            {'title': 'MATLAB App Designer Tutorial', 'video_id': 'LrDUxkqUazY', 'duration': '1:25:40'},
            {'title': 'MATLAB Image Processing', 'video_id': 'UOoXcrgMlkE', 'duration': '2:05:55'}
        ],

        'Julia': [
            {'title': 'Julia Programming Tutorial', 'video_id': 'b6c7d8e9f0g1', 'duration': '2:45:22'},
            {'title': 'Julia for Data Science', 'video_id': 'c7d8e9f0g1h2', 'duration': '1:30:45'},
            {'title': 'Julia Numerical Computing', 'video_id': 'd8e9f0g1h2i3', 'duration': '1:15:30'},
            {'title': 'Julia Language Crash Course', 'video_id': 'y6gR7Wc49pA', 'duration': '2:10:40'},
            {'title': 'Julia for Machine Learning', 'video_id': '6nQpZQNV9oE', 'duration': '1:55:22'},
            {'title': 'Parallel Computing in Julia', 'video_id': '4fR4gVG7kRU', 'duration': '1:20:18'},
            {'title': 'Julia DataFrames Tutorial', 'video_id': 'F_oOtaxb0L8', 'duration': '58:37'}
        ],

        'Groovy': [
            {'title': 'Groovy Programming Basics', 'video_id': 'i3j4k5l6m7n8', 'duration': '2:30:33'},
            {'title': 'Groovy with Grails', 'video_id': 'j4k5l6m7n8o9', 'duration': '3:00:45'},
            {'title': 'Groovy Scripting', 'video_id': 'k5l6m7n8o9p0', 'duration': '1:15:30'},
            {'title': 'Groovy for Java Developers', 'video_id': 'F5wUMYqgFiI', 'duration': '1:10:20'},
            {'title': 'Advanced Groovy', 'video_id': 'C3u7K89t4nI', 'duration': '1:35:15'},
            {'title': 'Groovy DSLs Tutorial', 'video_id': 'iWf_Qkql6CY', 'duration': '55:18'},
            {'title': 'Testing with Spock in Groovy', 'video_id': 'L70qBvUOFCs', 'duration': '1:12:33'}
        ],

        'Objective-C': [
            {'title': 'Objective-C Basics', 'video_id': 'p0q1r2s3t4u5', 'duration': '2:45:22'},
            {'title': 'iOS Development with Objective-C', 'video_id': 'q1r2s3t4u5v6', 'duration': '3:30:45'},
            {'title': 'Objective-C Memory Management', 'video_id': 'r2s3t4u5v6w7', 'duration': '1:15:30'},
            {'title': 'Objective-C for Beginners', 'video_id': 'mG4oR9tE2tU', 'duration': '1:45:15'},
            {'title': 'Objective-C Protocols & Delegates', 'video_id': 'jkZt9a1oYNE', 'duration': '58:50'},
            {'title': 'Mixing Swift and Objective-C', 'video_id': 'eRydgW3Y6n0', 'duration': '1:12:40'},
            {'title': 'Advanced Objective-C Features', 'video_id': 'UO3rjUqYVng', 'duration': '1:35:27'}
        ],

        'F#': [
            {'title': 'F# Programming Tutorial', 'video_id': 'w7x8y9z0a1b2', 'duration': '2:30:33'},
            {'title': 'Functional Programming in F#', 'video_id': 'x8y9z0a1b2c3', 'duration': '1:15:45'},
            {'title': 'F# for Data Science', 'video_id': 'y9z0a1b2c3d4', 'duration': '1:45:30'},
            {'title': 'F# Beginner Crash Course', 'video_id': 'NxtgD3dFh28', 'duration': '1:55:25'},
            {'title': 'Working with F# and .NET', 'video_id': '8NfQZj-7Wyw', 'duration': '1:05:40'},
            {'title': 'F# Pattern Matching', 'video_id': '3N3NcTk1n1s', 'duration': '42:18'},
            {'title': 'F# Async Programming', 'video_id': 'HqfYQqJ6y_g', 'duration': '1:12:59'}
        ],

        'Fortran': [
            {'title': 'Fortran Programming Basics', 'video_id': 'd4e5f6g7h8i9', 'duration': '2:45:22'},
            {'title': 'Fortran for Scientific Computing', 'video_id': 'e5f6g7h8i9j0', 'duration': '2:00:45'},
            {'title': 'Fortran Parallel Programming', 'video_id': 'f6g7h8i9j0k1', 'duration': '1:30:30'},
            {'title': 'Modern Fortran Tutorial', 'video_id': '7fPq7sWyfYo', 'duration': '2:05:10'},
            {'title': 'Fortran for Beginners', 'video_id': 'N9OZt1XMlUg', 'duration': '1:45:22'},
            {'title': 'Fortran Array Operations', 'video_id': 'pOQMBV4Bz5U', 'duration': '58:33'},
            {'title': 'Fortran Optimization Techniques', 'video_id': '3jq3e7k5QmE', 'duration': '1:15:41'}
        ],

        'Erlang': [
            {'title': 'Erlang Programming Tutorial', 'video_id': 'k1l2m3n4o5p6', 'duration': '2:30:33'},
            {'title': 'Erlang Concurrency', 'video_id': 'l2m3n4o5p6q7', 'duration': '1:15:45'},
            {'title': 'Building Systems with Elixir', 'video_id': 'm3n4o5p6q7r8', 'duration': '1:45:30'},
            {'title': 'Erlang for Beginners', 'video_id': 'a2o9rQbp0o0', 'duration': '1:25:18'},
            {'title': 'Erlang OTP Tutorial', 'video_id': 'Bd9onGO69rU', 'duration': '2:10:44'},
            {'title': 'Erlang Fault Tolerance', 'video_id': 'eBzMa8pVtBM', 'duration': '59:40'},
            {'title': 'Distributed Systems in Erlang', 'video_id': 'E1Y8XwBx5_s', 'duration': '1:35:55'}
        ],

        'D': [
            {'title': 'D Programming Basics', 'video_id': 'r8s9t0u1v2w3', 'duration': '2:15:22'},
            {'title': 'D for Systems Programming', 'video_id': 's9t0u1v2w3x4', 'duration': '1:45:45'},
            {'title': 'D Performance Optimization', 'video_id': 't0u1v2w3x4y5', 'duration': '1:15:30'},
            {'title': 'D Programming Language Tutorial', 'video_id': 'lGJ9f12lEBo', 'duration': '1:50:20'},
            {'title': 'Advanced D Features', 'video_id': 'v5xRmYqZ8y0', 'duration': '1:05:15'},
            {'title': 'D for Game Development', 'video_id': 'dQ23D_YwCOo', 'duration': '58:22'},
            {'title': 'D Metaprogramming', 'video_id': 'VRx_RfX1Yv8', 'duration': '1:35:14'}
        ],

        'COBOL': [
            {'title': 'COBOL Programming Basics', 'video_id': 'y5z6a7b8c9d0', 'duration': '2:45:33'},
            {'title': 'COBOL for Mainframes', 'video_id': 'z6a7b8c9d0e1', 'duration': '2:00:45'},
            {'title': 'COBOL Data Processing', 'video_id': 'a7b8c9d0e1f2', 'duration': '1:30:30'},
            {'title': 'COBOL Tutorial for Beginners', 'video_id': '8U5nw6b5ZkU', 'duration': '3:12:15'},
            {'title': 'COBOL File Handling', 'video_id': 'DqYhUpfEyKk', 'duration': '1:05:10'},
            {'title': 'COBOL Batch Processing', 'video_id': 'ThtlFYtN3Ew', 'duration': '58:18'},
            {'title': 'COBOL Debugging Techniques', 'video_id': 'C0V7Qahqjsk', 'duration': '1:15:25'}
        ],

        'Lisp': [
            {'title': 'Lisp Programming Tutorial', 'video_id': 'f2g3h4i5j6k7', 'duration': '2:30:22'},
            {'title': 'Functional Programming in Lisp', 'video_id': 'g3h4i5j6k7l8', 'duration': '1:15:45'},
            {'title': 'Lisp for AI Development', 'video_id': 'h4i5j6k7l8m9', 'duration': '1:45:30'},
            {'title': 'Common Lisp Crash Course', 'video_id': 'ymSq4wHrqyE', 'duration': '2:05:12'},
            {'title': 'Emacs Lisp Tutorial', 'video_id': 'KPgVQj4cT_E', 'duration': '1:02:25'},
            {'title': 'Scheme Programming Basics', 'video_id': '8jQikdBhJu8', 'duration': '1:15:55'},
            {'title': 'Macros in Lisp', 'video_id': '0xV3U7IqUrs', 'duration': '52:18'}
        ],

        'Prolog': [
            {'title': 'Prolog Programming Basics', 'video_id': 'm9n0o1p2q3r4', 'duration': '2:15:33'},
            {'title': 'Prolog for AI', 'video_id': 'n0o1p2q3r4s5', 'duration': '1:45:45'},
            {'title': 'Logic Programming in Prolog', 'video_id': 'o1p2q3r4s5t6', 'duration': '1:15:30'},
            {'title': 'Learn Prolog Now', 'video_id': 'p7rK5lWhr1o', 'duration': '1:55:18'},
            {'title': 'Prolog Backtracking Explained', 'video_id': 'mC_TtT9U0ZY', 'duration': '48:44'},
            {'title': 'Prolog with SWI-Prolog', 'video_id': '7GxkU9xQxN4', 'duration': '1:20:14'},
            {'title': 'Prolog Advanced Topics', 'video_id': 'O_nz6YyH7Yw', 'duration': '1:35:20'}
        ],

        'Ada': [
            {'title': 'Ada Programming Tutorial', 'video_id': 't6u7v8w9x0y1', 'duration': '2:45:22'},
            {'title': 'Ada for Embedded Systems', 'video_id': 'u7v8w9x0y1z2', 'duration': '2:00:45'},
            {'title': 'Ada Tasking', 'video_id': 'v8w9x0y1z2a3', 'duration': '1:30:30'},
            {'title': 'Ada Basics', 'video_id': 'FcQy8vYULFw', 'duration': '1:15:44'},
            {'title': 'Advanced Ada Programming', 'video_id': '5c5ekfV2h7Y', 'duration': '1:35:11'},
            {'title': 'Ada for Safety-Critical Systems', 'video_id': 'McnKuUO8cOE', 'duration': '58:36'},
            {'title': 'Ada Generic Programming', 'video_id': 'mv5K7slVtwI', 'duration': '1:25:29'}
        ],

        'Crystal': [
            {'title': 'Crystal Programming Basics', 'video_id': 'a3b4c5d6e7f8', 'duration': '2:30:33'},
            {'title': 'Crystal for Web Development', 'video_id': 'b4c5d6e7f8g9', 'duration': '1:45:45'},
            {'title': 'Crystal Performance Tips', 'video_id': 'c5d6e7f8g9h0', 'duration': '1:15:30'},
            {'title': 'Crystal Language Tutorial', 'video_id': 'tqJj2oEjCjA', 'duration': '1:20:44'},
            {'title': 'Crystal for CLI Tools', 'video_id': 'Tep4nVY_tjg', 'duration': '52:30'},
            {'title': 'Metaprogramming in Crystal', 'video_id': 'zjDYvV8Zm6A', 'duration': '1:05:10'},
            {'title': 'Crystal Concurrency Model', 'video_id': 'FmVkW9KexnM', 'duration': '1:18:54'}
        ],

        'Nim': [
            {'title': 'Nim Programming Tutorial', 'video_id': 'h0i1j2k3l4m5', 'duration': '2:15:22'},
            {'title': 'Nim for Systems Programming', 'video_id': 'i1j2k3l4m5n6', 'duration': '1:45:45'},
            {'title': 'Nim Metaprogramming', 'video_id': 'j2k3l4m5n6o7', 'duration': '1:15:30'},
            {'title': 'Learn Nim in One Video', 'video_id': '9a1yIsT0lgA', 'duration': '1:50:18'},
            {'title': 'Nim Macros Explained', 'video_id': 'm69irLjBBMQ', 'duration': '42:27'},
            {'title': 'Nim Game Development', 'video_id': 'rH1tXz9POmA', 'duration': '1:12:33'},
            {'title': 'Nim Networking Tutorial', 'video_id': 'c6V3U6GH7jE', 'duration': '58:16'}
        ],

        'Zig': [
            {'title': 'Zig Programming Basics', 'video_id': 'o7p8q9r0s1t2', 'duration': '2:30:33'},
            {'title': 'Zig for Systems Programming', 'video_id': 'p8q9r0s1t2u3', 'duration': '1:45:45'},
            {'title': 'Zig Memory Management', 'video_id': 'q9r0s1t2u3v4', 'duration': '1:15:30'},
            {'title': 'Zig Language Tutorial', 'video_id': 'QFjZxUx0ZkA', 'duration': '1:05:50'},
            {'title': 'Zig Build System Explained', 'video_id': 'DazjMthdTx0', 'duration': '48:15'},
            {'title': 'Zig Game Development', 'video_id': 'E6zvhDCr48E', 'duration': '1:18:40'},
            {'title': 'Zig Advanced Features', 'video_id': 'o-3b6pGZy_M', 'duration': '1:30:22'}
        ],

        'Bash': [
            {'title': 'Bash Scripting Tutorial', 'video_id': 'v4w5x6y7z8a9', 'duration': '2:15:22'},
            {'title': 'Advanced Bash Scripting', 'video_id': 'w5x6y7z8a9b0', 'duration': '1:45:45'},
            {'title': 'Bash for Automation', 'video_id': 'x6y7z8a9b0c1', 'duration': '1:30:30'},
            {'title': 'Bash Scripting for Beginners', 'video_id': 'SPwyp2NG-bE', 'duration': '1:25:17'},
            {'title': 'Bash Loops and Conditionals', 'video_id': 'O7v5bwYIWDA', 'duration': '43:12'},
            {'title': 'Bash Functions Explained', 'video_id': 'BO2K-VS6j8o', 'duration': '36:40'},
            {'title': 'Bash Script Projects', 'video_id': 's_vR9nzO8wI', 'duration': '1:15:28'}
        ],
    'PowerShell': [
    {'title': 'PowerShell Basics', 'video_id': 'c1d2e3f4g5h6', 'duration': '2:30:33'},
    {'title': 'PowerShell for System Admins', 'video_id': 'd2e3f4g5h6i7', 'duration': '1:45:45'},
    {'title': 'PowerShell Scripting', 'video_id': 'e3f4g5h6i7j8', 'duration': '1:30:30'},
    {'title': 'Learn Windows PowerShell in a Month of Lunches', 'video_id': 'r-8rd1aXxAk', 'duration': '3:15:42'},
    {'title': 'PowerShell Advanced Functions', 'video_id': 'vU79WJq9sAE', 'duration': '1:12:55'},
    {'title': 'PowerShell Remoting Guide', 'video_id': 'Q3yJ1cQXnJ8', 'duration': '0:49:28'},
    {'title': 'Error Handling in PowerShell', 'video_id': 'qU7cPZnqS3g', 'duration': '0:38:14'},
    {'title': 'Automating Tasks with PowerShell', 'video_id': 'y2p8aD54kFQ', 'duration': '1:27:36'},
    {'title': 'Working with APIs in PowerShell', 'video_id': 'o0iOmW5VtC0', 'duration': '0:58:22'},
    {'title': 'PowerShell Desired State Configuration (DSC)', 'video_id': 'pTjM2Kq5nlg', 'duration': '1:09:10'}
],
    'Shell': [
    {'title': 'Shell Scripting Tutorial', 'video_id': 'j8k9l0m1n2o3', 'duration': '2:15:22'},
    {'title': 'Advanced Shell Scripting', 'video_id': 'k9l0m1n2o3p4', 'duration': '1:45:45'},
    {'title': 'Shell for Automation', 'video_id': 'l0m1n2o3p4q5', 'duration': '1:30:30'},
    {'title': 'Bash Shell Scripting Tutorial | Full Course', 'video_id': 'rMpa-VgJ_UQ', 'duration': '—'},
    {'title': 'Shell Scripting Crash Course (Edureka)', 'video_id': 'GtovwKDemnI', 'duration': '—'},
    {'title': 'Learn Bash Scripting in 1 Hour | Shell Scripting Tutorial', 'video_id': 'PNhq_4d-5ek', 'duration': '—'},
    {'title': 'Learn Shell Scripting Basics for Beginners', 'video_id': 'mNWbvSijIV0', 'duration': '—'}
],

'Pascal': [
    {'title': 'Pascal Programming Basics', 'video_id': 'q5r6s7t8u9v0', 'duration': '2:30:33'},
    {'title': 'Pascal for Beginners', 'video_id': 'r6s7t8u9v0w1', 'duration': '1:45:45'},
    {'title': 'Pascal Data Structures', 'video_id': 's7t8u9v0w1x2', 'duration': '1:30:30'},
    {'title': '—Pascal Tutorial—', 'video_id': '—', 'duration': '—'},
    {'title': '—Pascal Crash Course—', 'video_id': '—', 'duration': '—'},
    {'title': '—Pascal Object-Oriented Programming—', 'video_id': '—', 'duration': '—'},
    {'title': '—Advanced Pascal Techniques—', 'video_id': '—', 'duration': '—'}
],

'OCaml': [
    {'title': 'OCaml Programming Tutorial', 'video_id': 'x2y3z4a5b6c7', 'duration': '2:15:22'},
    {'title': 'Functional Programming in OCaml', 'video_id': 'y3z4a5b6c7d8', 'duration': '1:45:45'},
    {'title': 'OCaml Type System', 'video_id': 'z4a5b6c7d8e9', 'duration': '1:15:30'},
    {'title': 'Introduction | OCaml Programming | Chapter 1 Video 1', 'video_id': 'MUcka_SvhLw', 'duration': '—'},
    {'title': 'Getting started with OCaml. Part 1', 'video_id': '_L_UMDI7-3E', 'duration': '—'},
    {'title': 'OCaml Tutorial – Learn how to use the OCaml Programming Language', 'video_id': 'PGGl5WcNOIU', 'duration': '—'},
    {'title': 'Intro to OCaml + Functional Programming', 'video_id': 'spwvg0DThh4', 'duration': '—'}
],

    'Racket': [
    {'title': 'An Introduction to the Racket Programming Language', 'video_id': 'n_7drg-R-YY', 'duration': '1:02:45'},
    {'title': 'Racket Programming Part 1: The Basics', 'video_id': 'CLPphLbBP7w', 'duration': '0:48:20'},
    {'title': 'Introduction to Functional Programming with Racket', 'video_id': '4BxGreUvXgM', 'duration': '1:15:10'},
    {'title': 'Getting started with (Dr)Racket', 'video_id': 'thswAtQSt0I', 'duration': '0:37:55'},
    {'title': 'Introduction to Racket - Simply Explained', 'video_id': 'kelxchu8UJQ', 'duration': '0:42:33'},
    {'title': 'Introduction to Racket Programming Part 1', 'video_id': '8IZ_IBsYKGY', 'duration': '0:55:40'},
    {'title': 'DSL Embedding in Racket (Part 1) - Matthew Flatt', 'video_id': 'WQGh_NemRy4', 'duration': '1:20:15'}
],

        'Smalltalk': [
            {'title': 'Smalltalk Programming Tutorial', 'video_id': 'l6m7n8o9p0q1', 'duration': '2:15:22'},
            {'title': 'Smalltalk OOP Concepts', 'video_id': 'm7n8o9p0q1r2', 'duration': '1:45:45'},
            {'title': 'Smalltalk for GUI Apps', 'video_id': 'n8o9p0q1r2s3', 'duration': '1:30:30'},
            {'title': 'Learning Smalltalk in One Hour', 'video_id': 'HTm2mQqXavE', 'duration': '1:05:17'},
            {'title': 'Smalltalk and MVC Architecture', 'video_id': 'h3X7lQv79pU', 'duration': '0:58:42'},
            {'title': 'Advanced Smalltalk Programming', 'video_id': 's1oC5T8rP3w', 'duration': '1:22:15'},
            {'title': 'Smalltalk Development with Pharo', 'video_id': 'l4MYvH6jQZU', 'duration': '1:15:28'}
        ],

        'Solidity': [
    {'title': 'Solidity Tutorial - Full Course', 'video_id': 'ipwxYa-F1uY', 'duration': '6:31:22'},
    {'title': 'Learn Blockchain, Solidity, and Full Stack Web3 Development with JavaScript – 32-Hour Course', 'video_id': 'gyMwXuJrbJQ', 'duration': '—'},
    {'title': 'Solidity, Blockchain, and Smart Contract Course', 'video_id': 'M576WGiDBdQ', 'duration': '—'},
    {'title': 'Learn Solidity: The COMPLETE Beginner’s Guide (Latest Version 0.8)', 'video_id': 'EhPeHeoKF88', 'duration': '—'},
    {'title': 'Solidity Tutorial for Beginners – Full Course (2023)', 'video_id': 'AYpftDFiIgk', 'duration': '—'}
],


        'Networking': [
            {'title': 'OSI Model Explained', 'video_id': 'vv4y_uOneC0', 'duration': '0:12:32'},
            {'title': 'TCP/IP Model Overview', 'video_id': 'C7XwzD5JmxQ', 'duration': '0:15:44'},
            {'title': 'Subnetting Tutorial', 'video_id': 'XzY4vD9qRIw', 'duration': '0:18:55'},
            {'title': 'DNS and How It Works', 'video_id': '72snZctFFtA', 'duration': '0:10:20'},
            {'title': 'HTTP vs HTTPS Explained', 'video_id': 'hExRDVZHhig', 'duration': '0:09:45'},
            {'title': 'What is a VPN and How it Works', 'video_id': 'oM0JLFbG0cQ', 'duration': '0:14:10'},
            {'title': 'Firewalls Explained', 'video_id': 'i4xk0UkO4rE', 'duration': '0:11:37'}
        ],

        'Cloud-Computing': [
    {'title': 'IaaS, PaaS, and SaaS Explained', 'video_id': '36zducUX16w', 'duration': '0:08:55'},
    {'title': 'Public vs Private vs Hybrid Cloud', 'video_id': 'mxT233EdY5c', 'duration': '0:12:34'},
    {'title': 'Cloud Security Basics', 'video_id': '2uaTPmNvH0I', 'duration': '0:09:59'}
    ],

        'Arduino-Programming': [
    {'title': 'Arduino Programming for Beginners', 'video_id': 'fCxzA9_kg6s', 'duration': '1:20:14'},
    {'title': 'Arduino Projects for Beginners', 'video_id': 'nL34zDTPkcs', 'duration': '2:14:35'},
    {'title': 'Arduino Sensors and Actuators', 'video_id': 'v8DkIM3ac7M', 'duration': '1:07:40'},
    {'title': 'Arduino IoT Projects', 'video_id': 'm9-4pM9c7QA', 'duration': '1:03:28'},
    {'title': 'Arduino Robotics Projects', 'video_id': '7vhvnaWUZjE', 'duration': '1:25:55'}
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
