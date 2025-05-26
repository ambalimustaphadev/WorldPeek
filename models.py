import os
import jwt
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from datetime import datetime, timedelta


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    email = db.Column(db.String(200), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(200), nullable=False)
    created = db.Column(db.DateTime, default=datetime.now)

    # Relationships
    # country_history = db.relationship('CountryHistory', back_populates='user', cascade='all, delete-orphan')
    stored_jwt_tokens = db.relationship('StoredJwtToken', back_populates='user', cascade='all, delete-orphan')
    search_history = db.relationship('UserSearchHistory', back_populates='user', cascade='all, delete-orphan')

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self):
        return f"<User {self.email}>"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_auth_token(self):
        expiry_date = datetime.utcnow() + timedelta(days=10)
        payload = {'id': self.id, 'exp': expiry_date}
        token = jwt.encode(payload, os.environ.get('SECRET_KEY'), algorithm='HS256')
        return token

    @staticmethod
    def verify_auth_token(token):
        if not token:
            return None
        try:
            active_token = StoredJwtToken.query.filter_by(jwt_token=token).first()
            if active_token:
                payload = jwt.decode(token, os.environ.get('SECRET_KEY'), algorithms=['HS256'])
                return User.query.get(payload['id'])
        except jwt.ExpiredSignatureError:
            print('Token has expired')
        except jwt.DecodeError:
            print('Token is invalid')
        return None

class StoredJwtToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jwt_token = db.Column(db.String(255), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    user = db.relationship('User', back_populates='stored_jwt_tokens')

class PasswordResetToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(10), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    used = db.Column(db.Boolean, default=False)
    generated_at = db.Column(db.DateTime, default=datetime.now)

class Country(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    capital = db.Column(db.String(128))
    calling_code = db.Column(db.String(10))
    population = db.Column(db.Integer)
    tld = db.Column(db.String(10))
    timezones = db.Column(db.PickleType)
    currencies = db.Column(db.PickleType)
    flag = db.Column(db.String(256))
    languages = db.Column(db.PickleType)
    latlng = db.Column(db.PickleType)


class UserSearchHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # For country name searches (e.g., "Nigeria")
    country_name = db.Column(db.String(100), nullable=True)

    # For feature searches (e.g., timezone, currency)
    search_query = db.Column(db.String(256), nullable=True)
    search_type = db.Column(db.String(50), nullable=True)  # e.g., 'timezone', 'currency', 'full_info'
    extra_info = db.Column(db.String(256))  # e.g. 'capital,population,languages'
    viewed_at = db.Column(db.DateTime, default=datetime.now)


    user = db.relationship('User', back_populates='search_history')


# class CountryHistory(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     country_name = db.Column(db.String(100))
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#     search_type = db.Column(db.String(50), nullable=False)
#     viewed_at = db.Column(db.DateTime, default=datetime.now)

#     user = db.relationship('User', back_populates='country_history')

# class SearchHistory(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#     query = db.Column(db.String(256))
#     result_type = db.Column(db.String(50))  # e.g., 'timezone', 'currency', etc.
#     timestamp = db.Column(db.DateTime, default=datetime.now)

#     user = db.relationship('User', back_populates='search_history')

