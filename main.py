from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
from nltk.tokenize import sent_tokenize, word_tokenize
import re
from nltk import FreqDist
from nltk.corpus import stopwords
import nltk

app = Flask(__name__)


nltk.download('punkt')
nltk.download('stopwords')


@app.route('/', methods=['GET'])
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


if __name__ == '__main__':
    app.run(debug=True)