from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
import google.generativeai as genai
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

genai.configure(api_key="AIzaSyC8kJ3_lSe-ghge61HeffnXTOUmPwYXeKk")
model = genai.GenerativeModel(
    model_name="models/gemini-2.0-pro-exp",
    system_instruction=(
        "You are a helpful and empathetic assistant who only provides support for mental health topics. "
        "You must not answer any questions that are unrelated to emotional well-being, anxiety, depression, stress, trauma, "
        "grief, loneliness, panic, self-care, or psychological health. "
        "If the user asks about other topics, respond with a polite message saying you can only help with mental health concerns."
    )
)
DATABASE = 'users.db'

def init_db():
    if not os.path.exists(DATABASE):
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        username TEXT PRIMARY KEY,
                        password TEXT NOT NULL
                    )''')
        
        conn.commit()
        conn.close()
        print("Database initialized and users table created.")
    else:
        print("Database already exists.")

init_db()

def query_db(query, args=(), one=False):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cur = conn.execute(query, args)
    rv = cur.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv

@app.route('/')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = query_db('SELECT * FROM users WHERE username = ? AND password = ?', [username, password], one=True)
    if user:
        session['username'] = username
        return redirect(url_for('chat_page'))
    else:
        return render_template('login.html', error="Invalid username or password.")

@app.route('/signup')
def signup_page():
    return render_template('signup.html')

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['username']
    password = request.form['password']
    existing_user = query_db('SELECT * FROM users WHERE username = ?', [username], one=True)
    if existing_user:
        return render_template('signup.html', error="User already exists.")
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
    conn.commit()
    conn.close()
    session['username'] = username
    return redirect(url_for('chat_page'))

@app.route('/chat', methods=['GET'])
def chat_page():
    if 'username' not in session:
        return redirect(url_for('login_page'))
    return render_template('chat.html', username=session['username'])

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get("message", "").strip()
    if not user_message:
        return jsonify({"reply": "Please enter a message."})
    
    try:
        response = model.generate_content(user_message)
        reply = response.text.strip()
        return jsonify({"reply": reply})
    except Exception as e:
        print("Gemini error:", e)
        return jsonify({"reply": "There was an issue processing your request. Please try again later."})

@app.route('/logout')
def logout():
    session.clear()
    flash('Successfully logged out.', 'success')
    return redirect(url_for('login_page'))

if __name__ == '__main__':
    app.run(debug=True)