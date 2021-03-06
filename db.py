from datetime import datetime
from flask import Flask, request, flash, url_for, redirect, \
     render_template, abort
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy.orm
from cockroachdb.sqlalchemy import run_transaction

DATABASE = {
    'drivername': 'cockroachdb',
    'host': 'localhost',
    'port': '26257',
    'username': 'root',
    'database': 'context'
}

app = Flask(__name__)
app.config.from_pyfile('hello.cfg')
db = SQLAlchemy(app)
sessionmaker = sqlalchemy.orm.sessionmaker(db.engine)

def session():
    return sessionmaker()

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column('msg_id', db.Integer, primary_key=True)
    channel = db.Column("channel", db.String)
    name = db.Column("name", db.String)
    message = db.Column("message", db.String)
    timestamp = db.Column("timestamp", db.DateTime)

    def __init__(self, channel, name, message, scores, timestamp):
        self.channel = channel
        self.name = name
        self.message = message
        self.timestamp = datetime.utcnow()

class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column('event_id', db.Integer, primary_key=True)
    channel = db.Column("channel", db.String)
    name = db.Column("name", db.String)
    message = db.Column("message", db.String)
    links = db.Column("links", db.String)
    timestamp = db.Column("timestamp", db.DateTime)

    def __init__(self, channel, name, message, links, timestamp):
        self.channel = channel
        self.name = name
        self.message = message
        self.links = links
        self.timestamp = timestamp
