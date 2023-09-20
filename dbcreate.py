from flask_sqlalchemy import SQLAlchemy
from flask import Flask
import datetime

db = SQLAlchemy()

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    followers = db.relationship('Followers', backref='users', lazy=True)
    name = db.Column(db.String, nullable=False)
    surname = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    location = db.Column(db.String, nullable=False)

class Followers(db.Model):
    __tablename__ = 'followers'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime, nullable=False)


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/bugra/Desktop/Coding/VoteApp/database.db'
db.init_app(app)

with app.app_context():
    db.create_all()