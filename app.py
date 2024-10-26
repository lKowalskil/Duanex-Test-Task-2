import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from textblob import TextBlob
import nltk
import random
from flask_session import Session
from nltk import word_tokenize, pos_tag, ne_chunk
import os
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(), 
        logging.FileHandler("app.log") 
    ]
)

logger = logging.getLogger(__name__)

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem" 
app.config["SECRET_KEY"] = os.urandom(24) 
Session(app)

nltk.download('punkt')
nltk.download('punkt_tab')
nltk.download('averaged_perceptron_tagger_eng')
nltk.download('maxent_ne_chunker')
nltk.download('maxent_ne_chunker_tab')
nltk.download('words')

def init_db():
    with sqlite3.connect("chat_history.db") as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS messages (
                          id INTEGER PRIMARY KEY AUTOINCREMENT,
                          session_id TEXT,
                          timestamp TEXT,
                          sender TEXT,
                          message TEXT)''')
        conn.commit()

init_db()

positive_responses = ["I'm glad to hear that! 😊", "That’s wonderful! How can I assist further?", "Awesome! 😊"]
neutral_responses = ["Alright! How can I assist you further?", "Okay, tell me more."]
negative_responses = ["I'm sorry you're facing issues. 😔", "I'm here to help. What seems to be the problem?"]
fallback_responses = ["I’m not sure I understand that.", "Could you rephrase?", "I'm here to help, but I didn't get that."]

def extract_name(user_input):
    try:
        tokens = word_tokenize(user_input)
        pos_tags = pos_tag(tokens)
        named_entities = ne_chunk(pos_tags)
        
        for entity in named_entities:
            if hasattr(entity, 'label') and entity.label() == 'PERSON':
                name = ' '.join([leaf[0] for leaf in entity.leaves()])
                session['name'] = name
                return f"Nice to meet you, {name}!"
    except Exception as e:
        logger.error(f"Name extraction error: {e}")
    
    return None

def save_message(session_id, sender, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect("chat_history.db") as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO messages (session_id, timestamp, sender, message) VALUES (?, ?, ?, ?)",
                       (session_id, timestamp, sender, message))
        conn.commit()

def get_chat_history(session_id):
    with sqlite3.connect("chat_history.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp, sender, message FROM messages WHERE session_id = ?", (session_id,))
        return cursor.fetchall()

def clear_chat_history(session_id):
    with sqlite3.connect("chat_history.db") as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        conn.commit()

def get_response(user_input):
    if 'interaction_count' not in session:
        session['interaction_count'] = 0

    sentiment = TextBlob(user_input).sentiment.polarity  

    name_response = extract_name(user_input)
    if name_response:
        return name_response
    
    if sentiment > 0:
        response = random.choice(positive_responses)
    elif sentiment < 0:
        response = random.choice(negative_responses)
    else:
        response = random.choice(neutral_responses)
    
    return response

@app.route('/chat', methods=['POST'])
def chat():
    if 'session_id' not in session:
        session['session_id'] = str(datetime.now().timestamp())

    session_id = session['session_id']
    user_input = request.json.get("message", "").strip() 

    save_message(session_id, "User", user_input)

    if 'awaiting_feedback' in session and session['awaiting_feedback']:
        clear_chat_history(session_id)  
        session.pop('awaiting_feedback', None) 
        session['interaction_count'] = 0
        return jsonify({"response": "Thank you for your feedback!"})  
    
    bot_response = get_response(user_input)

    if 'interaction_count' not in session:
        session['interaction_count'] = 0
        
    session['interaction_count'] += 1
    if session['interaction_count'] % 3 == 0 and session['interaction_count'] >= 3:
        session['awaiting_feedback'] = True 
        bot_response += " Can you please provide feedback on our conversation?"

    save_message(session_id, "Bot", bot_response)

    return jsonify({"response": bot_response})

@app.route('/')
def index():
    if 'session_id' not in session:
        session['session_id'] = str(datetime.now().timestamp())

    session_id = session['session_id']
    
    chat_history = get_chat_history(session_id)
    
    return render_template('index.html', chat_history=chat_history)

if __name__ == '__main__':
    app.run(debug=True)