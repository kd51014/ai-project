from flask import Flask
from app.config import Config
from app.extensions import db
from app.routes import posts_bp
from app.routes.auth import auth_bp
from app.routes.users import users_bp
from app.models import User
import re
import os

def parse_mentions(text):
    """Convert @username mentions into profile links."""
    if not text:
        return text

    def replace_mention(match):
        username = match.group(1)
        # Create a link for each @username (404 if user does not exist)
        return f'<a href="/users/{username}">@{username}</a>'

    pattern = r'@(\w+)'  # @username: letters, numbers, underscores
    return re.sub(pattern, replace_mention, text)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    # Register Jinja2 filter for mentions
    app.jinja_env.filters['parse_mentions'] = parse_mentions

    # Register blueprints
    app.register_blueprint(posts_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)

    with app.app_context():
        db.create_all()

        # Create admin user if not exists
        admin = User.query.filter_by(login='admin').first()
        if not admin:
            admin = User(login='admin', is_admin=True)
            admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')  # fallback password
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()

    return app

app = create_app()