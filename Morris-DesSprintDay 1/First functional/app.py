import os
from flask import Flask, render_template, request, redirect, url_for, session
from googleapiclient.discovery import build
from google.oauth2 import service_account

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Load Google API credentials from JSON file
SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = 'credentials.json'

# Dummy user database (replace with a real database in production)
users = {
    "user1": {"password": "password1", "calendar_id": None},
    "user2": {"password": "password2", "calendar_id": None}
}

# Function to create a new Google Calendar for a user
def create_calendar(user_id):
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=creds)

    calendar = {
        'summary': f'Calendar for {user_id}',
        'timeZone': 'America/Los_Angeles'
    }

    created_calendar = service.calendars().insert(body=calendar).execute()
    users[user_id]['calendar_id'] = created_calendar['id']

# Function to get Google Calendar events for a user
def get_calendar_events(user_id):
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=creds)

    calendar_id = users[user_id]['calendar_id']
    if calendar_id:
        try:
            events_result = service.events().list(calendarId=calendar_id, maxResults=10).execute()
            events = events_result.get('items', [])
            return events
        except Exception as e:
            print("Error fetching calendar events:", e)
            return None
    else:
        return None

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in users and users[username]['password'] == password:
            session['username'] = username
            return redirect(url_for('calendar'))
        else:
            return render_template('login.html', error="Invalid username or password. Please try again.")
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in users:
            return "Username already exists. <a href='/signup'>Try again</a>"
        else:
            users[username] = {"password": password, "calendar_id": None}
            create_calendar(username)
            session['username'] = username
            return redirect(url_for('calendar'))
    return render_template('signup.html')

@app.route('/calendar')
def calendar():
    if 'username' in session:
        username = session['username']
        if 'calendar_id' not in users[username]:
            create_calendar(username)
        events = get_calendar_events(username)
        if events:
            return render_template('calendar.html', username=username, events=events)
        else:
            return "No calendar events found."
    else:
        return redirect(url_for('login'))
    

if __name__ == '__main__':
    app.run(debug=True)