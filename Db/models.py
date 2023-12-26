from . import db
from flask_login import UserMixin

class users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    preferred_gender = db.Column(db.String(10), nullable=False)
    about = db.Column(db.String(200))
    photo = db.Column(db.String(200))
    hidden = db.Column(db.Boolean, default=False)

    def repr(self):
        return f'id:{self.id}, username:{self.username}'