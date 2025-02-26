import os
from flask import Flask, render_template, request, jsonify, session
import google.generativeai as genai
import markdown
import json
import re

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Needed for session storage

genai.configure(api_key="AIzaSyA-IvpCksoe_kJeXCvQlIxz4doLM0CsTzQ")

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=generation_config,
)

chat_session = model.start_chat(history=[])


@app.route('/')
def login_page():
    """Render login.html as the first page."""
    return render_template('login.html')


@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/ai')
def ai_page():
    return render_template('ai.html')


@app.route('/flashcards')
def flashcards():
    return render_template('flashcards.html')


@app.route('/test')
def test():
    return render_template('test.html')


@app.route('/generate_test', methods=['POST'])
def generate_test():
    try:
        data = request.json
        school_board = data.get("school_board")
        topic = data.get("topic")

        if not school_board or not topic:
            return jsonify({"error": "Missing school board or topic"}), 400

        prompt = f"""
        Generate a test with 30 questions on the topic "{topic}" for the {school_board} school board.
        Structure:
        - 15 short-answer questions
        - 10 medium-answer questions
        - 5 long-answer questions
        Format JSON as:
        {{
            "questions": [
                {{"type": "short", "question": "Short question 1?"}},
                {{"type": "medium", "question": "Medium question 1?"}},
                {{"type": "long", "question": "Long question 1?"}}
            ]
        }}
        Respond with only JSON, no extra text.
        """

        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Extract JSON safely
        json_text = response_text.strip().replace("```json", "").replace("```", "")
        try:
            test_data = json.loads(json_text)
        except json.JSONDecodeError:
            return jsonify({"error": "AI response not in valid JSON format"}), 500

        session["test_questions"] = test_data["questions"]
        return jsonify(test_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/submit_test', methods=['POST'])
def submit_test():
    try:
        answers = request.json.get("answers")
        questions = session.get("test_questions", [])

        if not answers or not questions:
            return jsonify({"error": "No answers submitted or test not found"}), 400

        prompt = f"""
        Grade the following test answers based on correctness and clarity:
        {json.dumps(questions)}
        Student Answers:
        {json.dumps(answers)}
        Give feedback and a score out of 100.
        JSON Format:
        {{
            "score": 85,
            "feedback": [
                {{"question": "Question 1?", "feedback": "Correct"}},
                {{"question": "Question 2?", "feedback": "Needs more detail"}}
            ]
        }}
        """

        response = model.generate_content(prompt)
        response_text = response.text.strip()

        json_text = response_text.strip().replace("```json", "").replace("```", "")
        try:
            results = json.loads(json_text)
        except json.JSONDecodeError:
            return jsonify({"error": "Error processing test results"}), 500

        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/generate_flashcards', methods=['POST'])
def generate_flashcards():
    try:
        topic = request.json.get("topic")
        if not topic:
            return jsonify({"error": "No topic provided"}), 400

        prompt = f"""
        Generate exactly 20 quiz flashcards for the topic: {topic}.
        Respond as JSON:
        [
            {{"question": "What is X?", "answer": "Y"}}
        ]
        """

        response = model.generate_content(prompt)
        response_text = response.text.strip()

        json_text = response_text.strip().replace("```json", "").replace("```", "")
        try:
            flashcards = json.loads(json_text)
        except json.JSONDecodeError:
            return jsonify({"error": "AI response is not in JSON format"}), 500

        session["flashcards"] = flashcards
        session["current_index"] = 0
        return jsonify({"flashcards": flashcards})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/next_flashcard', methods=['POST'])
def next_flashcard():
    flashcards = session.get("flashcards", [])
    if not flashcards:
        return jsonify({"error": "No flashcards available"}), 400

    current_index = session.get("current_index", 0)
    if current_index < len(flashcards) - 1:
        session["current_index"] += 1

    return jsonify(flashcards[session["current_index"]])


@app.route('/prev_flashcard', methods=['POST']) 
def prev_flashcard():
    flashcards = session.get("flashcards", [])
    if not flashcards:
        return jsonify({"error": "No flashcards available"}), 400

    current_index = session.get("current_index", 0)
    if current_index > 0:
        session["current_index"] -= 1

    return jsonify(flashcards[session["current_index"]])


@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_message = request.json.get("message")
        last_message = session.get("last_message", "")

        conversation_history = f"{last_message}\nUser: {user_message}"

        response = chat_session.send_message(conversation_history)

        reply = response.text if hasattr(response, "text") else "No response received."
        formatted_reply = markdown.markdown(reply)

        session["last_message"] = user_message

        return jsonify({"reply": formatted_reply})

    except Exception as e:
        return jsonify({"reply": "Error: " + str(e)})


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
