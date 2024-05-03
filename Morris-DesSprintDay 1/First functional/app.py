import os
from flask import Flask, render_template, request, redirect, url_for, session
from gcsa.google_calendar import GoogleCalendar
from gcsa.event import Event
from gcsa.calendar import Calendar

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.static_folder = 'static'

# Dummy user database
users = {
    "user1": {"password": "password1", "calendar_id": None},
    "user2": {"password": "password2", "calendar_id": None}
}

def get_calendar(user_id):
    return GoogleCalendar('dancevirusofficial@gmail.com', credentials_path='ITSC3155-Design-Sprint-main\Morris-DesSprintDay 1\First functional\credentials.json')

def create_calendar(user_id):
    try:
        calendar = get_calendar(user_id)

        # Create a new calendar instance
        new_calendar = Calendar(
            'My Calendar',
            description='Calendar for personal events'
        )

        # Add the new calendar
        calendar = calendar.add_calendar(new_calendar)
        
        # Update user data with calendar_id
        users[user_id]['calendar_id'] = calendar.calendar_id
        session['calendar_id'] = calendar.calendar_id
    except Exception as e:
        print(f"Error creating calendar for user {user_id}: {e}")

def list_events(user_id):
    try:
        calendar = get_calendar(user_id)
        events = list(calendar.get_events())
        return events
    except Exception as e:
        print(f"Error fetching events for user {user_id}: {e}")
        return []

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username in users:
            return "Username already exists. <a href='/signup'>Try again</a>"
        else:
            users[username] = {"password": password, "calendar_id": None}
            session['username'] = username
            return redirect(url_for('authorize'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username in users and users[username]['password'] == password:
            session['username'] = username
            return redirect(url_for('calendar'))
        else:
            return "Invalid username or password. <a href='/login'>Try again</a>"
    return render_template('login.html')

@app.route('/calendar')
def calendar():
    if 'username' in session:
        username = session['username']
        if 'calendar_id' not in session:
            create_calendar(username)

        if 'calendar_id' in session:
            events = list_events(username)
            return render_template('calendar.html', username=username, events=events)
        else:
            return "Calendar not found. Please try again."
    else:
        return redirect(url_for('login'))

@app.route('/authorize')
def authorize():
    # Your authorization logic here
    # For simplicity, I'm just redirecting to the OAuth callback
    return redirect(url_for('oauth_callback'))

@app.route('/oauth_callback')
def oauth_callback():
    # Your OAuth callback logic here
    # For simplicity, I'm just redirecting to the calendar
    return redirect(url_for('calendar'))

from datetime import datetime

@app.route('/create_event', methods=['POST'])
def create_event():
    if 'username' in session:
        username = session['username']
        event_title = request.form.get('event_title')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')

        try:
            calendar = get_calendar(username)
            event = Event(event_title, start=datetime.fromisoformat(start_time), end=datetime.fromisoformat(end_time))
            calendar.add_event(event)
            return redirect(url_for('calendar'))
        except Exception as e:
            print(f"Error creating event for user {username}: {e}")
            return "Error creating event. Please try again."
    else:
        return redirect(url_for('login'))



@app.route('/delete_event', methods=['POST'])
def delete_event():
    if 'username' in session:
        username = session['username']
        try:
            calendar = get_calendar(username)
            event_id = request.form.get('event_id')

            # Check if event_id is provided
            if not event_id:
                return "Error: Event ID is missing."

            # Delete the event
            calendar.delete_event(event_id)
            return redirect(url_for('calendar'))
        except Exception as e:
            print(f"Error deleting event for user {username}: {e}")
            return "Error deleting event. Please try again."
    else:
        return redirect(url_for('login'))




@app.route('/delete_calendar', methods=['POST'])
def delete_calendar():
    if 'username' in session:
        username = session['username']
        try:
            calendar = get_calendar(username)
            calendar_id = users[username]['calendar_id']
            calendar.delete_calendar(calendar_id)
            users[username]['calendar_id'] = None
            session.pop('calendar_id', None)
            return redirect(url_for('calendar'))
        except Exception as e:
            print(f"Error deleting calendar for user {username}: {e}")
            return "Error deleting calendar. Please try again."
    else:
        return redirect(url_for('login'))

@app.route('/update_calendar', methods=['POST'])
def update_calendar():
    if 'username' in session:
        username = session['username']
        try:
            calendar = get_calendar(username)
            calendar_id = users[username]['calendar_id']
            calendar_obj = calendar.get_calendar(calendar_id)
            

            calendar_obj.summary = request.form.get('summary')

            calendar.update_calendar(calendar_obj)
            return redirect(url_for('calendar'))
        except Exception as e:
            print(f"Error updating calendar for user {username}: {e}")
            return "Error updating calendar. Please try again."
    else:
        return redirect(url_for('login'))


@app.route('/clear_calendar', methods=['POST'])
def clear_calendar():
    if 'username' in session:
        username = session['username']
        try:
            calendar = get_calendar(username)
            calendar_id = users[username]['calendar_id']
            events = list(calendar.get_events())
            for event in events:
                calendar.delete_event(event.id)
            return redirect(url_for('calendar'))
        except Exception as e:
            print(f"Error clearing calendar for user {username}: {e}")
            return "Error clearing calendar. Please try again."
    else:
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
