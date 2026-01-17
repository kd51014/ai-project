from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.models import User
from app.extensions import db

import re

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


def validate_password(password):
    """
    Validates password:
    - minimum 10 characters
    - at least one uppercase letter
    - at least one lowercase letter
    - at least one digit
    """
    if len(password) < 10:
        return False, 'Password must be at least 10 characters long.'
    if not re.search(r'[A-Z]', password):
        return False, 'Password must contain at least one uppercase letter.'
    if not re.search(r'[a-z]', password):
        return False, 'Password must contain at least one lowercase letter.'
    if not re.search(r'\d', password):
        return False, 'Password must contain at least one digit.'
    return True, None


def validate_login(login):
    """
    Validates login:
    - cannot be empty
    - must be unique
    """
    if not login or len(login.strip()) == 0:
        return False, 'Login cannot be empty.'
    if User.query.filter_by(login=login).first():
        return False, 'User with this login already exists.'
    return True, None


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        login = request.form.get('login', '').strip()
        password = request.form.get('password', '')
        password2 = request.form.get('password2', '')

        # Empty field validation
        if not login:
            flash('Login cannot be empty.')
            return render_template('auth/register.html')
        if not password:
            flash('Password cannot be empty.')
            return render_template('auth/register.html')
        if not password2:
            flash('You must confirm your password.')
            return render_template('auth/register.html')

        # Password validation
        if password != password2:
            flash('Passwords must match.')
            return render_template('auth/register.html')

        is_valid, error_msg = validate_password(password)
        if not is_valid:
            flash(error_msg)
            return render_template('auth/register.html')

        # Login validation
        is_valid, error_msg = validate_login(login)
        if not is_valid:
            flash(error_msg)
            return render_template('auth/register.html')

        # User registration
        try:
            user = User(login=login, is_admin=False)  # Always create a regular user
            user.set_password(password)  # Sets the password hash
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! You can now log in.')
            return redirect(url_for('auth.login'))
        except Exception:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.')
            return render_template('auth/register.html')

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form.get('login', '').strip()
        password = request.form.get('password', '')

        # Empty field validation
        if not login:
            flash('You must provide a login.')
            return render_template('auth/login.html')
        if not password:
            flash('You must provide a password.')
            return render_template('auth/login.html')

        # User verification
        user = User.query.filter_by(login=login).first()
        if not user or not user.check_password(password):
            flash('Invalid login or password.')
            return render_template('auth/login.html')

        # Log in user
        session['user_id'] = user.id
        session['user_login'] = user.login
        return redirect(url_for('posts.index'))

    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_login', None)
    return redirect(url_for('posts.index'))
