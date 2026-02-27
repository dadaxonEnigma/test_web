from flask import Flask, render_template, jsonify, request
from pathlib import Path
import json

app = Flask(__name__)

# Configuration
DATA_DIR = Path(__file__).parent / "data"

class TestParser:
    @staticmethod
    def parse_test(content):
        """Parse test file content into questions and answers"""
        lines = content.split('\n')
        questions = []
        current_question = None

        for line in lines:
            line = line.strip()
            if not line:
                if current_question and current_question['options']:
                    questions.append(current_question)
                    current_question = None
                continue

            if not current_question:
                current_question = {
                    'text': line,
                    'options': [],
                    'correct': -1
                }
            else:
                is_correct = line.startswith('*')
                text = line[1:].strip() if is_correct else line

                if text:
                    if is_correct:
                        current_question['correct'] = len(current_question['options'])
                    current_question['options'].append(text)

        if current_question and current_question['options']:
            questions.append(current_question)

        return questions

    @staticmethod
    def load_tests():
        """Load all test files from data directory"""
        tests = {}
        if not DATA_DIR.exists():
            return tests

        for file_path in sorted(DATA_DIR.glob("*.txt")):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    test_data = TestParser.parse_test(content)
                    if test_data:
                        tests[file_path.stem] = test_data
            except Exception as e:
                print(f"Ошибка загрузки {file_path}: {e}")

        return tests

# Load tests
TESTS = TestParser.load_tests()

@app.route('/')
def index():
    """Serve main page"""
    return render_template('index.html')

@app.route('/api/tests')
def get_tests():
    """Get list of tests"""
    tests_list = []
    for name, questions in TESTS.items():
        tests_list.append({
            'name': name,
            'count': len(questions)
        })
    return jsonify(sorted(tests_list, key=lambda x: x['name']))

@app.route('/api/test/<test_name>')
def get_test(test_name):
    """Get test questions"""
    if test_name not in TESTS:
        return jsonify({'error': 'Тест не найден'}), 404

    test_data = TESTS[test_name]
    questions = []
    for q in test_data:
        questions.append({
            'text': q['text'],
            'options': q['options'],
            'correct': q['correct']
        })

    return jsonify({
        'name': test_name,
        'questions': questions
    })

@app.route('/api/check-answer', methods=['POST'])
def check_answer():
    """Check if answer is correct"""
    data = request.json
    test_name = data.get('test_name')
    question_idx = data.get('question_idx')
    answer_idx = data.get('answer_idx')

    if test_name not in TESTS:
        return jsonify({'error': 'Тест не найден'}), 404

    test_data = TESTS[test_name]
    if question_idx >= len(test_data):
        return jsonify({'error': 'Вопрос не найден'}), 404

    question = test_data[question_idx]
    is_correct = answer_idx == question['correct']

    return jsonify({
        'is_correct': is_correct,
        'correct_answer': question['correct'],
        'correct_text': question['options'][question['correct']]
    })

if __name__ == '__main__':
    if not TESTS:
        print("⚠️ Тесты не найдены! Проверьте папку 'data'")
    else:
        print(f"✅ Загружено {len(TESTS)} тестов")
        for name, tests in TESTS.items():
            print(f"   - {name}: {len(tests)} вопросов")

    app.run(debug=False, host='0.0.0.0', port=5000)
