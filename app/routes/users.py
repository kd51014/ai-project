from flask import Blueprint, render_template, abort, session, redirect, url_for, request, flash
from app.models import User, Post
from app.extensions import db
import os
from werkzeug.utils import secure_filename

users_bp = Blueprint('users', __name__, url_prefix="/users")


@users_bp.route('/<login>')
def profile(login):
    user = User.query.filter_by(login=login).first()
    if not user:
        abort(404)

    posts = (
        Post.query
        .filter_by(author_id=user.id)
        .order_by(Post.created_at.desc())
        .all()
    )

    return render_template(
        'users/profile.html',
        user=user,
        posts=posts
    )


@users_bp.route('/edit', methods=['GET', 'POST'])
def edit_profile():
    if not session.get('user_id'):
        return redirect(url_for('auth.login'))

    user = User.query.get(session['user_id'])

    # --- Additional security check ---
    # If a user_id is provided (e.g. ?id=...) or the user attempts
    # to edit someone else's profile (not possible in this app yet,
    # but kept for future safety)
    req_id = request.args.get('id')
    if req_id and int(req_id) != session['user_id']:
        return redirect(url_for('users.profile', login=user.login))
    # --- End security check ---

    if request.method == 'POST':
        new_bio = request.form.get('bio', '')
        user.bio = new_bio

        file = request.files.get('profile_image')
        if file and file.filename:
            ext = os.path.splitext(file.filename)[1]
            filename = f'profile_{user.id}{ext}'
            static_path = os.path.join('static', 'img', filename)
            abs_path = os.path.join(os.path.dirname(__file__), '..', static_path)
            file.save(abs_path)
            user.profile_image = '/' + static_path.replace('\\', '/')

        db.session.commit()
        flash('Profile updated successfully!')
        return redirect(url_for('users.edit_profile'))

    return render_template(
        'users/edit_profile.html',
        user=user
    )
