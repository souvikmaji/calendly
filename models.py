# Data models for users, availability, and meetings

from db import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

class Availability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_time = db.Column(db.Integer, nullable=False)  # Epoch timestamp
    end_time = db.Column(db.Integer, nullable=False)    # Epoch timestamp

class Meeting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    meeting_time = db.Column(db.Integer, nullable=False)  # Epoch timestamp