from flask import jsonify, request, make_response
from app import app, db
from models import PasswordResetToken, User, StoredJwtToken
from toolz import is_valid_email, random_generator, send_email
from flask_httpauth import HTTPTokenAuth
import os

auth = HTTPTokenAuth(scheme='Bearer')


@auth.error_handler 
def unauthorized(): 
    return make_response(jsonify({'error': 'Unauthorized access'}), 401) 


@auth.verify_token
def verify_token(token):
    return User.verify_auth_token(token)


# -------- USER SIGN UP ROUTE ----------
@app.route('/register', methods=['POST'])
def sign_up():
    data = request.json
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    email = data.get('email')
    phone = data.get('phone')
    password = data.get('password')

    if not first_name or len(first_name) < 2:
        return jsonify({'error': 'Please enter a valid first name!'}), 400

    if not is_valid_email(email):
        return jsonify({'error': 'Please enter a valid email address'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already exists'}), 400

    if not password or len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    new_user = User(first_name=first_name, last_name=last_name, email=email, phone=phone)
    new_user.set_password(password)
    db.session.add(new_user)

    try: 
        db.session.commit()
        return jsonify({'success': True, 'message': 'Account successfully created'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'User signup error: {e}'}), 500


# -------- USER LOGIN ROUTE ----------
@app.route('/login', methods=['POST'])
def login_user():
    email = request.json.get('email')
    password = request.json.get('password')

    if not email or not password:
        return jsonify({'error': 'Please enter a valid email and password'}), 400

    if not is_valid_email(email):
        return jsonify({'error': 'Invalid email format'}), 400

    user = User.query.filter_by(email=email).first()
    if user is None:
        return jsonify({'error': 'User with this email does not exist'}), 404

    if not user.check_password(password):
        return jsonify({'error': 'Invalid email or password'}), 401

    token = user.generate_auth_token()

    # Save JWT token
    token_record = StoredJwtToken(jwt_token=token, user=user)
    db.session.add(token_record)
    db.session.commit()

    return jsonify({'success': True, 'token': token, 'message': 'You are logged in'}), 200


# -------- FORGOT PASSWORD ROUTE ----------
@app.route('/forget-password', methods=['POST'])
def forgot_password():
    email = request.json.get('email')

    if not email:
        return jsonify({'error': 'Please enter your email'}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': 'User with this email does not exist'}), 404

    token = random_generator(8)
    reset = PasswordResetToken(token=token, user_id=user.id, used=False)
    db.session.add(reset)
    db.session.commit()

    # Email sending
    subject = 'Password Reset Token'
    text_body = f'Your password reset token is: {token}'
    html_body = f'<h1>{text_body}</h1>'

    try:
        send_email(subject=subject, receiver=email, text_body=text_body, html_body=html_body)
    except Exception as e:
        return jsonify({'error': f'Failed to send email: {str(e)}'}), 500

    return jsonify({'success': True, 'message': 'Password reset email sent'}), 200


# -------- RESET PASSWORD ROUTE ----------
@app.route('/reset-password', methods=['POST'])
def reset_password():
    token = request.json.get('token')
    new_password = request.json.get('new_password')
    confirm_password = request.json.get('confirm_password')

    if not token:
        return jsonify({'error': 'Please enter the token'}), 400
    if not new_password or new_password != confirm_password:
        return jsonify({'error': 'Passwords do not match or are invalid'}), 400

    reset = PasswordResetToken.query.filter_by(token=token).first()
    if not reset:
        return jsonify({'error': 'Invalid token'}), 400
    if reset.used:
        return jsonify({'error': 'Token has already been used'}), 400

    user = User.query.get(reset.user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    user.set_password(new_password)
    reset.used = True
    db.session.commit()

    return jsonify({'success': True, 'message': 'Password reset successfully'}), 200


# -------- SEND TEST EMAIL ROUTE ----------
@app.route('/send-email', methods=['POST'])
def send_test_email():
    email = request.json.get('email')

    if not email:
        return jsonify({'error': 'Please enter an email'}), 400

    try:
        otp = random_generator()
        subject = 'Pediforte OTP'
        message = f'Use this code as your Pediforte OTP: {otp}'
        send_email(subject=subject, receiver=email, text_body=message, html_body=f'<h1>{message}</h1>')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'success': True, 'message': 'Email sent successfully'}), 200
