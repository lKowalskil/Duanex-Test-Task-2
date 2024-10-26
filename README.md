# Flask Chatbot Application

This is a chatbot application built with Flask, using natural language processing to detect names, assess sentiment, and respond with contextually appropriate messages. The chatbot includes an HTML front end with a dark/light mode toggle, and maintains a simple session-based chat history stored in SQLite.

## Features
- **Session-based Interaction**: Each user session is tracked for a continuous chat experience.
- **Sentiment Analysis**: Using TextBlob to respond differently to positive, neutral, and negative sentiments.
- **Named Entity Recognition**: Identifies user names within the conversation using NLTK.
- **Feedback System**: Asks users for feedback after a specific number of interactions.
- **Dark/Light Mode**: User-friendly interface built with TailwindCSS that supports dark mode toggling.

## Prerequisites
- **Python 3.8+**
- **Flask** and **Flask-Session** for session management
- **SQLite** (bundled with Python)
- **NLTK** and **TextBlob** for natural language processing
- **TailwindCSS** for styling (loaded via CDN in the HTML template)

## Setup

1. **Clone the Repository**
    ```bash
    git clone https://github.com/your-username/flask-chatbot.git
    cd flask-chatbot
    ```

2. **Install Dependencies**
    Make sure to install required packages using `pip`:
    ```bash
    pip install -r requirements.txt
    ```

3. **Initialize the SQLite Database**
    The chatbot uses a local SQLite database to store chat history. The database is automatically created with the required tables when the application starts.

## Running the Application

To start the Flask application:

```bash
python app.py
```

By default, the application will be accessible at [http://127.0.0.1:5000](http://127.0.0.1:5000).

## Usage

- **Start a Conversation**: Open the application in a browser and type a message. The bot will respond based on the sentiment of your message.
- **Sentiment Responses**:
  - **Positive messages** receive an encouraging response.
  - **Neutral messages** receive a general response.
  - **Negative messages** receive a sympathetic response.
- **Feedback Prompt**: After three interactions, the bot will ask for feedback.
- **Dark Mode Toggle**: Click the “Toggle Dark Mode” button in the header to switch between themes.

## Troubleshooting

- **NLTK Data Not Found**: Ensure that required NLTK data packages are installed. Re-run the `nltk.downloader` commands if necessary.
- **Duplicate Message Submission**: Ensure the JavaScript `sendMessage()` function is not bound multiple times. If the issue persists, try testing in incognito mode.
- **Session Data Loss**: Make sure `SESSION_TYPE` is correctly set to `filesystem` in `app.config`.

## Logging

Application events and errors are logged to `app.log` in the root directory. Logging is configured at the `DEBUG` level to capture detailed information for debugging.
