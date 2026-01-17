from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.extensions import db
from app.models import Post, Comment, User, Reaction, Hashtag, post_hashtag
from sqlalchemy import func
import os
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

posts_bp = Blueprint("posts", __name__)


def parse_hashtags(text):
    """Extracts #hashtags from a string and returns a list of unique names (without #)."""
    import re
    return list(set([tag[1:] for tag in re.findall(r"#\w+", text)]))


# Ensure image_url column exists (fallback / legacy support)
if not hasattr(Post, 'image_url'):
    Post.image_url = db.Column(db.String(256), nullable=True)


def save_post_image(file, post_id):
    if not file or not file.filename:
        return None
    ext = os.path.splitext(file.filename)[1]
    filename = f'post_{post_id}{ext}'
    static_path = os.path.join('static', 'img', filename)
    abs_path = os.path.join(os.path.dirname(__file__), '..', static_path)
    file.save(abs_path)
    return '/' + static_path.replace('\\', '/')


def calculate_popularity_score(post, top_hashtags):
    """Calculates a popularity score for a post based on multiple criteria."""
    score = 0

    # 1. Positive reactions (+) – 2 points per plus
    plus_count = sum(1 for r in post.reactions if r.type == 'plus')
    score += plus_count * 2

    # 2. Total reactions – 1 point per reaction
    total_reactions = len(post.reactions)
    score += total_reactions

    # 3. Number of comments – 5 points per comment
    comments_count = Comment.query.filter_by(post_id=post.id).count()
    score += comments_count * 5

    # 4. Bonus for top 5 hashtag – 10 points
    post_hashtag_ids = [tag.id for tag in post.hashtags]
    top_hashtag_ids = [tag.id for tag in top_hashtags]
    if any(tag_id in top_hashtag_ids for tag_id in post_hashtag_ids):
        score += 10

    # 5. New post boost – up to 7 points (1 per day since creation)
    if post.created_at:
        try:
            if isinstance(post.created_at, datetime):
                days_old = (datetime.now() - post.created_at).days
            else:
                created_dt = datetime.fromisoformat(
                    str(post.created_at).replace('Z', '+00:00')
                )
                days_old = (datetime.now() - created_dt.replace(tzinfo=None)).days

            if days_old <= 7:
                score += (7 - days_old)
        except (AttributeError, ValueError, TypeError):
            pass

    return score


@posts_bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if not session.get("user_id"):
            flash("You must be logged in to add a post.")
            return redirect(url_for("auth.login"))

        title = request.form["title"]
        content = request.form["content"]
        hashtags = parse_hashtags(f"{title} {content}")

        post = Post(
            title=title,
            content=content,
            author_id=session["user_id"]
        )

        # Commit first to get post_id
        db.session.add(post)
        db.session.commit()

        file = request.files.get('image')
        if file and file.filename:
            post.image_url = save_post_image(file, post.id)
            db.session.commit()

        # Attach hashtags
        for name in hashtags:
            tag = Hashtag.query.filter_by(name=name.lower()).first()
            if not tag:
                tag = Hashtag(name=name.lower())
                db.session.add(tag)
            if tag not in post.hashtags:
                post.hashtags.append(tag)

        db.session.commit()
        return redirect(url_for("posts.index"))

    # Fetch top 5 hashtags (needed for popularity score)
    hashtags = (
        db.session.query(
            Hashtag,
            func.count(post_hashtag.c.post_id).label('count')
        )
        .join(post_hashtag)
        .group_by(Hashtag.id)
        .order_by(func.count(post_hashtag.c.post_id).desc())
        .limit(5)
        .all()
    )
    hashtags = [h[0] for h in hashtags]

    # Fetch all posts
    posts = Post.query.all()

    # Calculate popularity scores
    posts_with_scores = []
    for post in posts:
        score = calculate_popularity_score(post, hashtags)
        posts_with_scores.append((post, score))

    # Sort by score descending
    posts_with_scores.sort(key=lambda x: x[1], reverse=True)
    posts = [post for post, score in posts_with_scores]

    reactions_map = {}
    your_reactions = {}
    user_id = session.get("user_id")

    for post in posts:
        plus = sum(1 for r in post.reactions if r.type == 'plus')
        minus = sum(1 for r in post.reactions if r.type == 'minus')
        reactions_map[post.id] = {'plus': plus, 'minus': minus}

        your_reactions[post.id] = None
        if user_id:
            your = [r for r in post.reactions if r.user_id == user_id]
            if your:
                your_reactions[post.id] = your[0].type

    return render_template(
        "index.html",
        posts=posts,
        reactions_map=reactions_map,
        your_reactions=your_reactions,
        hashtags=hashtags
    )


@posts_bp.route("/post/<int:post_id>", methods=["GET", "POST"])
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)

    if request.method == "POST":
        if not session.get("user_id"):
            flash("You must be logged in to add a comment.")
            return redirect(url_for("auth.login"))

        content = request.form["content"]
        parent_id = request.form.get("parent_id")

        if parent_id:
            parent = Comment.query.get(int(parent_id))
            comment = Comment(
                content=content,
                post=post,
                parent=parent,
                author_id=session["user_id"]
            )
        else:
            comment = Comment(
                content=content,
                post=post,
                author_id=session["user_id"]
            )

        db.session.add(comment)
        db.session.commit()
        return redirect(url_for("posts.post_detail", post_id=post.id))

    comments = Comment.query.filter_by(
        post_id=post.id,
        parent_id=None
    ).all()

    plus = sum(1 for r in post.reactions if r.type == 'plus')
    minus = sum(1 for r in post.reactions if r.type == 'minus')

    your_reaction = None
    if session.get('user_id'):
        your = [r for r in post.reactions if r.user_id == session['user_id']]
        if your:
            your_reaction = your[0].type

    return render_template(
        "posts/detail.html",
        post=post,
        comments=comments,
        plus=plus,
        minus=minus,
        your_reaction=your_reaction
    )


@posts_bp.route('/react/<int:post_id>/<reaction_type>', methods=['POST'])
def react(post_id, reaction_type):
    if not session.get('user_id'):
        flash('You must be logged in to react.')
        return redirect(url_for('auth.login'))

    if reaction_type not in ('plus', 'minus'):
        flash('Invalid reaction.')
        return redirect(url_for('posts.index'))

    post = Post.query.get_or_404(post_id)
    user_id = session['user_id']

    reaction = Reaction.query.filter_by(
        post_id=post.id,
        user_id=user_id
    ).first()

    if reaction:
        if reaction.type == reaction_type:
            return redirect(request.referrer or url_for('posts.index'))
        reaction.type = reaction_type
    else:
        reaction = Reaction(
            post_id=post.id,
            user_id=user_id,
            type=reaction_type
        )
        db.session.add(reaction)

    db.session.commit()
    return redirect(request.referrer or url_for('posts.index'))


# Display posts with a selected hashtag
@posts_bp.route('/hashtag/<name>')
def posts_by_hashtag(name):
    tag = Hashtag.query.filter_by(name=name.lower()).first_or_404()
    posts = tag.posts

    reactions_map = {}
    your_reactions = {}
    user_id = session.get("user_id")

    for post in posts:
        plus = sum(1 for r in post.reactions if r.type == 'plus')
        minus = sum(1 for r in post.reactions if r.type == 'minus')
        reactions_map[post.id] = {'plus': plus, 'minus': minus}

        your_reactions[post.id] = None
        if user_id:
            your = [r for r in post.reactions if r.user_id == user_id]
            if your:
                your_reactions[post.id] = your[0].type

    hashtags = (
        db.session.query(
            Hashtag,
            func.count(post_hashtag.c.post_id).label('count')
        )
        .join(post_hashtag)
        .group_by(Hashtag.id)
        .order_by(func.count(post_hashtag.c.post_id).desc())
        .limit(5)
        .all()
    )
    hashtags = [h[0] for h in hashtags]

    return render_template(
        'index.html',
        posts=posts,
        reactions_map=reactions_map,
        your_reactions=your_reactions,
        hashtags=hashtags,
        selected_tag=name.lower()
    )


from flask import abort
from flask import g

@posts_bp.before_app_request
def load_current_user():
    g.current_user = User.query.get(session['user_id']) if session.get('user_id') else None


@posts_bp.app_context_processor
def inject_current_user():
    """Make current_user available in templates as a convenience variable.

    Some templates reference `current_user` (e.g. to check admin rights).
    We already set `g.current_user` in `before_app_request`; expose it here so
    templates can safely use `current_user.is_admin` without failing.
    """
    return {"current_user": getattr(g, 'current_user', None)}

@posts_bp.route('/delete/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    if not session.get('user_id'):
        flash("You must be logged in to delete a post.")
        return redirect(url_for('auth.login'))

    user = User.query.get(session['user_id'])
    if not user or not getattr(user, 'is_admin', False):
        abort(403)  # Forbidden

    post = Post.query.get_or_404(post_id)

    # Usuń obrazek jeśli istnieje
    if getattr(post, 'image_url', None):
        try:
            abs_path = os.path.join(os.path.dirname(__file__), '..', post.image_url.lstrip('/'))
            if os.path.exists(abs_path):
                os.remove(abs_path)
        except Exception as e:
            print(f"Failed to delete image: {e}")

    # Usuń post
    db.session.delete(post)
    db.session.commit()

    flash("Post deleted successfully.")
    return redirect(url_for('posts.index'))
