from app.extensions import db
from sqlalchemy.sql import func

post_hashtag = db.Table('post_hashtag',
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
    db.Column('hashtag_id', db.Integer, db.ForeignKey('hashtag.id'), primary_key=True)
)

class Hashtag(db.Model):
    __tablename__ = 'hashtag'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    posts = db.relationship('Post', secondary=post_hashtag, back_populates='hashtags')

class Reaction(db.Model):
    __tablename__ = 'reaction'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'plus' or 'minus'
    __table_args__ = (db.UniqueConstraint('post_id', 'user_id', name='_user_post_uc'),)

class Post(db.Model):
    __tablename__ = "post"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    image_url = db.Column(db.String(256), nullable=True)

    comments = db.relationship(
        "Comment",
        backref="post",
        cascade="all, delete-orphan",
        lazy=True
    )
    # When a Post is deleted, its reactions should be removed as well.
    # Add cascade so SQLAlchemy will delete Reaction objects instead of
    # trying to NULL out the foreign key (which is NOT NULL and causes
    # IntegrityError).
    reactions = db.relationship(
        'Reaction',
        backref='post',
        cascade='all, delete-orphan',
        lazy=True
    )
    hashtags = db.relationship('Hashtag', secondary=post_hashtag, back_populates='posts')
