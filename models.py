# models.py
from extensions import db
from datetime import datetime

class Hall(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cameras = db.relationship('Camera', backref='hall', lazy=True)

class Camera(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    stream_url = db.Column(db.String(200), nullable=False)
    hall_id = db.Column(db.Integer, db.ForeignKey('hall.id'), nullable=False)
    counts = db.relationship('PeopleCount', backref='camera', lazy=True)

class PeopleCount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    camera_id = db.Column(db.Integer, db.ForeignKey('camera.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    count = db.Column(db.Integer, default=0)
    in_count = db.Column(db.Integer, default=0)
    out_count = db.Column(db.Integer, default=0)