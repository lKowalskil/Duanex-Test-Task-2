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

# Configure logging to file and console with DEBUG level
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Log to console
        logging.FileHandler("app.log")  # Log to file "app.log"
    ]
)

logger = logging.getLogger(__name__)

app = Flask(__name__)

# Flask session configuration
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"  # Store session data in the filesystem
app.config["SECRET_KEY"] = os.urandom(24)  # Generate a random secret key for session encryption
Session(app)

# Download required NLTK datasets for text processing
nltk.download('punkt')
nltk.download('punkt_tab')
nltk.download('averaged_perceptron_tagger_eng')
nltk.download('maxent_ne_chunker')
nltk.download('maxent_ne_chunker_tab')
nltk.download('words')

# Database initialization function
def init_db():
    """Initializes the SQLite database and creates a messages table if it doesn't exist."""
    try:
        with sqlite3.connect("chat_history.db") as conn:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS messages (
                              id INTEGER PRIMARY KEY AUTOINCREMENT,
                              session_id TEXT,
                              timestamp TEXT,
                              sender TEXT,
                              message TEXT)''')
            conn.commit()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")

# Call database initialization on app startup
init_db()

# Predefined bot responses for different sentiment types
positive_responses = ["I'm glad to hear that! 😊", "That’s wonderful! How can I assist further?", "Awesome! 😊"]
neutral_responses = ["Alright! How can I assist you further?", "Okay, tell me more.", "I’m not sure I understand that.", "Could you rephrase?", "I'm here to help, but I didn't get that."]
negative_responses = ["I'm sorry you're facing issues. 😔", "I'm here to help. What seems to be the problem?"]

# Extract a name from user input if it contains a person entity
def extract_name(user_input):
    """Attempts to extract a personal name from the user's input text."""
    logger.debug(f"Extracting name from input: {user_input}")
    try:
        # Tokenize and tag the text, then identify named entities
        tokens = word_tokenize(user_input)
        pos_tags = pos_tag(tokens)
        named_entities = ne_chunk(pos_tags)
        
        # Check if any named entity is labeled as 'PERSON' (a name)
        for entity in named_entities:
            if hasattr(entity, 'label') and entity.label() == 'PERSON':
                name = ' '.join([leaf[0] for leaf in entity.leaves()])
                session['name'] = name  # Store name in session
                logger.info(f"Name '{name}' extracted and saved in session.")
                return f"Nice to meet you, {name}!"
    except Exception as e:
        logger.error(f"Name extraction error: {e}")
    
    logger.debug("No name detected in the input.")
    return None

# Save messages to the database
def save_message(session_id, sender, message):
    """Saves a message to the database with the session ID, timestamp, and sender."""
    logger.debug(f"Saving message from '{sender}' to session '{session_id}': {message}")
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect("chat_history.db") as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO messages (session_id, timestamp, sender, message) VALUES (?, ?, ?, ?)",
                           (session_id, timestamp, sender, message))
            conn.commit()
        logger.info("Message saved successfully.")
    except Exception as e:
        logger.error(f"Error saving message: {e}")

# Retrieve chat history from the database for a specific session
def get_chat_history(session_id):
    """Retrieves the chat history for the specified session ID from the database."""
    logger.debug(f"Retrieving chat history for session: {session_id}")
    try:
        with sqlite3.connect("chat_history.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT timestamp, sender, message FROM messages WHERE session_id = ?", (session_id,))
            history = cursor.fetchall()
        logger.info("Chat history retrieved successfully.")
        return history
    except Exception as e:
        logger.error(f"Error retrieving chat history: {e}")
        return []

# Clear chat history for a specific session
def clear_chat_history(session_id):
    """Clears the chat history for the specified session ID in the database."""
    logger.debug(f"Clearing chat history for session: {session_id}")
    try:
        with sqlite3.connect("chat_history.db") as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            conn.commit()
        logger.info("Chat history cleared successfully.")
    except Exception as e:
        logger.error(f"Error clearing chat history: {e}")

# Generate a bot response based on user input sentiment
def get_response(user_input):
    """Generates a bot response based on the sentiment of user input or by recognizing names."""
    logger.debug(f"Generating response for user input: {user_input}")
    if 'interaction_count' not in session:
        session['interaction_count'] = 0  # Initialize interaction count if not set

    # Analyze sentiment of user input
    sentiment = TextBlob(user_input).sentiment.polarity
    logger.debug(f"Sentiment analysis score: {sentiment}")

    # Attempt to extract and respond to a detected name
    name_response = extract_name(user_input)
    if name_response:
        logger.debug("Name response generated.")
        return name_response
    
    # Choose response based on sentiment score
    if sentiment > 0:
        response = random.choice(positive_responses)
    elif sentiment < 0:
        response = random.choice(negative_responses)
    else:
        response = random.choice(neutral_responses)

    logger.info(f"Response generated: {response}")
    return response

# Route for handling chat interaction via POST requests
@app.route('/chat', methods=['POST'])
def chat():
    """Handles chat interactions, saving messages, and generating responses."""
    logger.debug("Chat endpoint accessed.")
    
    # Set up a unique session ID if not already present
    if 'session_id' not in session:
        session['session_id'] = str(datetime.now().timestamp())
        logger.debug(f"New session created with ID: {session['session_id']}")

    session_id = session['session_id']
    user_input = request.json.get("message", "").strip()
    logger.debug(f"Received user input: {user_input}")

    save_message(session_id, "User", user_input)  # Log user's message to the database

    # If awaiting feedback, prompt and clear history after feedback
    if 'awaiting_feedback' in session and session['awaiting_feedback']:
        logger.debug("Awaiting feedback from the user.")
        clear_chat_history(session_id)
        session.pop('awaiting_feedback', None)
        session['interaction_count'] = 0
        return jsonify({"response": "Thank you for your feedback!"})

    # Generate and save bot response
    bot_response = get_response(user_input)

    # Track interactions for feedback prompt
    session['interaction_count'] = session.get('interaction_count', 0) + 1
    if session['interaction_count'] % 3 == 0:
        session['awaiting_feedback'] = True
        bot_response += " Can you please provide feedback on our conversation?"

    save_message(session_id, "Bot", bot_response)
    logger.info(f"Bot response sent: {bot_response}")

    return jsonify({"response": bot_response})

# Main index route to render chat history on page load
@app.route('/')
def index():
    """Main route to display chat history on the index page."""
    logger.debug("Index page accessed.")
    if 'session_id' not in session:
        session['session_id'] = str(datetime.now().timestamp())
        logger.debug(f"New session created with ID: {session['session_id']}")

    session_id = session['session_id']
    chat_history = get_chat_history(session_id)  # Retrieve chat history for the session
    logger.debug("Rendering chat history on index page.")
    
    return render_template('index.html', chat_history=chat_history)

# Start the Flask application with debugging enabled
if __name__ == '__main__':
    logger.info("Starting Flask application.")
    app.run(debug=True)
