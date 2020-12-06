from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
import requests
import os
import operator
import re
import nltk
from stop_words import stops
from collections import Counter
from bs4 import BeautifulSoup

from rq import Queue
from rq.job import Job
from worker import conn

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)

queue = Queue(connection=conn)

from models import *

@app.route('/', methods = ['GET', 'POST'])
def index():
    results = {}
    if request.method == 'POST':
        from app import count_and_save_words

        url = request.form['url']
        if not url[:8].startswith(('https://', 'http://')):
            url = 'http://' + url
        job = queue.enqueue_call(
            func = count_and_save_words, args = (url, ), result_ttl = 5000
        )
        print('Job Id: ', job.get_id())
            
    return render_template('index.html', results = results)


@app.route('/results/<id>', methods = ['GET'])
def get_result(id):
    job = Job.fetch(id, connection=conn)

    if job.is_finished:
        result = Result.query.filter_by(id=job.result).first()
        results = sorted(
            result.result_no_stop_words.items(),
            key=operator.itemgetter(1),
            reverse=True
        )[:10]
        return jsonify(results)
    else:
        return 'Nay!', 202


def count_and_save_words(url):
    errors = []
    try:
        res = requests.get(url) # to send external HTTP GET requests to passed URL
    except:
        errors.append('URL looks invalid!')
        return { 'errors': errors }

    raw = BeautifulSoup(res.text, 'html.parser').get_text() # to remove HTML tags
    nltk.data.path.append('./nltk_data/')
    tokens = nltk.word_tokenize(raw) # tokenize raw text
    text = nltk.Text(tokens) # Convert tokens to nltk text object

    nonPunct = re.compile('.*[A-Za-z].*')
    raw_words = [w for w in text if nonPunct.match(w)]
    raw_word_count = Counter(raw_words)

    no_stop_words = [w for w in raw_words if w.lower() not in stops]
    no_stop_words_count = Counter(no_stop_words)

    try:
        result = Result(
            url = url,
            data = raw_word_count,
            data_no_stop_words = no_stop_words_count
        )
        print('Result: ', result)
        db.session.add(result)
        db.session.commit()
    except:
        errors.append("Can't add item to database")
        return { 'errors': errors }
    return result.id


if __name__ == '__main__':
    app.run()
