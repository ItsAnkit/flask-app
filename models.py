from app import db
from sqlalchemy.dialects.postgresql import JSON

class Result(db.Model):
    __tablename__ = 'results'

    id = db.Column(db.Integer, primary_key = True)
    url = db.Column(db.String())
    data = db.Column(JSON)
    data_no_stop_words = db.Column(JSON)

    def __init__(self, url, data, data_no_stop_words):
        self.url = url
        self.data = data
        self.data_no_stop_words = data_no_stop_words

    # for object representation
    def __repr__(self):
        return '<id {}>'.format(self.id)
