from flask import Flask, render_template, request, jsonify, session 
import requests
import random
import html

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Needed for session management

def fetch_trivia_question(difficulty):
    url = f"https://opentdb.com/api.php?amount=10&category=18&type=multiple&difficulty={difficulty}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data['response_code'] == 0 and data['results']:
            return data['results'][0]
    return None

def adjust_difficulty(current, correct):
    if correct:
        return {'easy': 'medium', 'medium': 'hard', 'hard': 'hard'}[current]
    else:
        return {'hard': 'medium', 'medium': 'easy', 'easy': 'easy'}[current]

@app.route('/')
def index():
    session.clear()
    session['score'] = 0
    session['difficulty'] = 'easy'
    session['history'] = []
    session['performance'] = {
        'easy': {'correct': 0, 'incorrect': 0},
        'medium': {'correct': 0, 'incorrect': 0},
        'hard': {'correct': 0, 'incorrect': 0}
    }
    return render_template('index.html')

@app.route('/get-question')
def get_question():
    if session.get('score', 0) >= 10:
        return jsonify({'finished': True})

    difficulty = session.get('difficulty', 'easy')
    q = fetch_trivia_question(difficulty)

    if not q:
        return jsonify({'error': 'Unable to fetch question'}), 500

    question_text = html.unescape(q['question'])
    correct_answer = html.unescape(q['correct_answer'])
    options = [html.unescape(ans) for ans in q['incorrect_answers']] + [correct_answer]
    random.shuffle(options)

    session['current_question'] = {
        'question': question_text,
        'correct_answer': correct_answer,
        'difficulty': difficulty,
        'options': options
    }

    return jsonify({
        'question': question_text,
        'options': options,
        'difficulty': difficulty
    })

@app.route('/submit-answer', methods=['POST'])
def submit_answer():
    data = request.json
    user_answer = data.get('answer')
    q_data = session.get('current_question', {})
    correct_answer = q_data.get('correct_answer')
    difficulty = q_data.get('difficulty')
    correct = user_answer == correct_answer

    if correct:
        session['score'] += 1

    session['difficulty'] = adjust_difficulty(difficulty, correct)

    perf = session['performance'][difficulty]
    perf['correct' if correct else 'incorrect'] += 1

    session['history'].append({
        'question': q_data['question'],
        'difficulty': difficulty,
        'user_answer': user_answer,
        'correct_answer': correct_answer,
        'correct': correct
    })

    return jsonify({
        'correct': correct,
        'correct_answer': correct_answer,
        'score': session['score']
    })

@app.route('/results')
def results():
    return jsonify({
        'score': session['score'],
        'performance': session['performance'],
        'history': session['history']
    })

if __name__ == '__main__':
    app.run(debug=True)