import tweepy
import pandas as pd
from datetime import datetime, timedelta
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

# Twitter API credentials
API_KEY = 'your_api_key'
API_SECRET_KEY = 'your_api_secret_key'
ACCESS_TOKEN = 'your_access_token'
ACCESS_TOKEN_SECRET = 'your_access_token_secret'

# Set up Tweepy
auth = tweepy.OAuthHandler(API_KEY, API_SECRET_KEY)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth, wait_on_rate_limit=True)

# Flask setup
app = Flask(__name__)
socketio = SocketIO(app)

# Global variable to store tweets
tweets_data = []


def fetch_tweets(keyword1, keyword2, start_time, end_time):
    query = f'{keyword1} OR {keyword2}'
    tweets = tweepy.Cursor(api.search_tweets, q=query, lang='en', since=start_time, until=end_time).items(100)
    tweets_list = [[tweet.created_at, tweet.text] for tweet in tweets]
    return tweets_list


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/fetch', methods=['POST'])
def fetch():
    keyword1 = request.form['keyword1']
    keyword2 = request.form['keyword2']
    start_date = request.form['start_date']
    end_date = request.form['end_date']

    start_time = datetime.strptime(start_date, '%Y-%m-%d')
    end_time = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)

    global tweets_data
    tweets_data = fetch_tweets(keyword1, keyword2, start_time.strftime('%Y-%m-%d'), end_time.strftime('%Y-%m-%d'))

    # Emit data to the dashboard
    socketio.emit('update_data', {'tweets': tweets_data})

    return 'Fetching data...'


@app.route('/analyze', methods=['GET'])
def analyze():
    keyword1 = request.args.get('keyword1')
    keyword2 = request.args.get('keyword2')

    # Filter tweets containing the keywords
    keyword1_count = sum(keyword1.lower() in tweet[1].lower() for tweet in tweets_data)
    keyword2_count = sum(keyword2.lower() in tweet[1].lower() for tweet in tweets_data)

    return {
        'keyword1': keyword1,
        'keyword1_count': keyword1_count,
        'keyword2': keyword2,
        'keyword2_count': keyword2_count
    }


@socketio.on('connect')
def handle_connect():
    emit('update_data', {'tweets': tweets_data})


if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
