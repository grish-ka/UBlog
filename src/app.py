import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import urllib.request
import urllib.parse
import json
import hashlib

app = Flask(__name__)
app.secret_key = "super_secret_ublog_key" # Required for logging in and keeping users in a "session"

# --- Database Configuration ---
db_url = os.environ.get("DATABASE_URL")
if db_url:
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///ublog.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# --- Database Models ---
# The association table for following users (Many-to-Many relationship)
followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

# The association table for linking Posts to Blogs without breaking existing data
blog_posts = db.Table('blog_posts',
    db.Column('blog_id', db.Integer, db.ForeignKey('blog.id')),
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'))
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    # Roles can be: 'user', 'moderator', or 'admin'
    role = db.Column(db.String(20), default='user') 
    about_me = db.Column(db.String(140))
    
    # Relationships for Follows and Posts
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')
        
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic', cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        # Creates a unique profile picture URL based on their email!
        digest = hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    owner = db.relationship('User', backref=db.backref('owned_blogs', lazy='dynamic'))
    posts = db.relationship('Post', secondary=blog_posts, backref=db.backref('blogs', lazy='dynamic'), lazy='dynamic')

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=db.func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    comments = db.relationship('Comment', backref='post', lazy='dynamic', cascade="all, delete-orphan")

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=db.func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

# Automatically create the database tables if they don't exist
with app.app_context():
    db.create_all()
    # Safe migration trick: Add 'about_me' column if it doesn't exist yet!
    try:
        db.session.execute(db.text('ALTER TABLE user ADD COLUMN about_me VARCHAR(140)'))
        db.session.commit()
    except Exception:
        pass
        
    # Auto-upgrade the environment variable admin to the permanent 'owner' role
    admin_email = os.environ.get("ADMIN_EMAIL")
    if admin_email:
        root_user = User.query.filter_by(email=admin_email).first()
        if root_user and root_user.role != 'owner':
            root_user.role = 'owner'
            db.session.commit()

# --- Helper Functions ---
def verify_recaptcha(recaptcha_response):
    secret_key = os.environ.get("RECAPTCHA_SECRET_KEY")
    # If no key is configured, bypass for local testing
    if not secret_key:
        return True 
    
    url = 'https://www.google.com/recaptcha/api/siteverify'
    values = {'secret': secret_key, 'response': recaptcha_response}
    data = urllib.parse.urlencode(values).encode('utf-8')
    try:
        req = urllib.request.Request(url, data=data)
        response = urllib.request.urlopen(req)
        result = json.loads(response.read().decode())
        return result.get('success', False)
    except Exception:
        return False

# This protects routes so only logged-in users can see them!
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to view this page.")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# This protects routes so ONLY admins can see them!
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to view this page.")
            return redirect(url_for('login'))
            
        current_user = db.session.get(User, session["user_id"])
        if not current_user or current_user.role not in ['admin', 'owner']:
            flash("Access Denied: You must be an Admin to perform this action.")
            return redirect(url_for('index'))
            
        return f(*args, **kwargs)
    return decorated_function

# --- Routes ---
@app.route("/", methods=["GET"])
def index():
    # Get the currently logged-in user
    current_user = None
    blogs = []
    
    if "user_id" in session:
        current_user = db.session.get(User, session["user_id"])
        
    # Get the search query from the URL (if one exists)
    search_query = request.args.get("q", "")
    
    if search_query:
        # Search blogs by title (case-insensitive for SQLite)
        blogs = Blog.query.filter(Blog.title.ilike(f"%{search_query}%")).all()
    else:
        # Just grab all blogs
        blogs = Blog.query.all()
        
    return render_template("index.html", user=current_user, blogs=blogs, search_query=search_query)

@app.route("/blog/<int:blog_id>", methods=["GET", "POST"])
def view_blog(blog_id):
    current_user = None
    if "user_id" in session:
        current_user = db.session.get(User, session["user_id"])
        
    blog = db.session.get(Blog, blog_id)
    if not blog:
        flash("Blog not found.")
        return redirect(url_for('index'))
        
    # Handle creating a post specific to this blog
    if request.method == "POST" and current_user:
        post_body = request.form.get("body")
        if post_body:
            new_post = Post(body=post_body, author=current_user)
            blog.posts.append(new_post) # Safer append to avoid potential crashes
            db.session.add(new_post)
            db.session.commit()
            flash("Your post is now live!")
            return redirect(url_for('view_blog', blog_id=blog.id))
            
    # Fetch posts specific to this blog
    posts = blog.posts.order_by(Post.timestamp.desc()).all()
    return render_template("blog.html", user=current_user, blog=blog, posts=posts)

@app.route("/create_blog", methods=["POST"])
@login_required
def create_blog():
    current_user = db.session.get(User, session["user_id"])
    title = request.form.get("title")
    description = request.form.get("description")
    
    if title:
        # Prevent duplicate blog names
        if Blog.query.filter_by(title=title).first():
            flash("A blog with that title already exists!")
        else:
            new_blog = Blog(title=title, description=description, owner=current_user)
            db.session.add(new_blog)
            db.session.commit()
            flash(f"Blog '{title}' successfully created!")
            
    return redirect(url_for('index'))

@app.route("/delete_post/<int:post_id>", methods=["POST"])
@login_required
def delete_post(post_id):
    current_user = db.session.get(User, session["user_id"])
    post = db.session.get(Post, post_id)
    
    if post:
        # Only allow deletion if it's their own post, OR if they are an admin/owner/moderator
        if post.user_id == current_user.id or current_user.role in ['admin', 'owner', 'moderator']:
            
            # NESTED DELETE: Erase all comments on this post first!
            for comment in post.comments:
                db.session.delete(comment)
                
            db.session.delete(post)
            db.session.commit()
            flash("Post and all its comments deleted successfully.")
        else:
            flash("You don't have permission to delete this post.")
            
    return redirect(request.referrer or url_for('index'))

@app.route("/post/<int:post_id>/comment", methods=["POST"])
@login_required
def add_comment(post_id):
    post = db.session.get(Post, post_id)
    if not post:
        flash("Post not found.")
        return redirect(request.referrer or url_for('index'))
        
    body = request.form.get("body")
    if body:
        current_user = db.session.get(User, session["user_id"])
        new_comment = Comment(body=body, author=current_user, post=post)
        db.session.add(new_comment)
        db.session.commit()
        flash("Comment added successfully!")
        
    return redirect(request.referrer or url_for('index'))

@app.route("/delete_comment/<int:comment_id>", methods=["POST"])
@login_required
def delete_comment(comment_id):
    comment = db.session.get(Comment, comment_id)
    if comment:
        current_user = db.session.get(User, session["user_id"])
        # Allow author, admin, owner, or moderator to delete comment
        if current_user.id == comment.user_id or current_user.role in ['admin', 'owner', 'moderator']:
            db.session.delete(comment)
            db.session.commit()
            flash("Comment deleted.")
        else:
            flash("You don't have permission to delete this comment.")
    return redirect(request.referrer or url_for('index'))

@app.route("/delete_blog/<int:blog_id>", methods=["POST"])
@admin_required
def delete_blog(blog_id):
    blog = db.session.get(Blog, blog_id)
    if blog:
        db.session.delete(blog)
        db.session.commit()
        flash(f"Blog '{blog.title}' was deleted successfully.")
    # Request.referrer sends you back to the page you clicked delete from (e.g. Admin Dashboard)
    return redirect(request.referrer or url_for('index'))

@app.route("/admin")
@admin_required
def admin_dashboard():
    current_user = db.session.get(User, session["user_id"])
    users = User.query.all()
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    blogs = Blog.query.all()
    
    return render_template("admin.html", user=current_user, users=users, posts=posts, blogs=blogs)

@app.route("/explore")
@login_required
def explore():
    current_user = db.session.get(User, session["user_id"])
    all_users = User.query.all()
    return render_template("explore.html", current_user=current_user, users=all_users)
    
@app.route("/user/<username>")
@login_required
def user_profile(username):
    current_user = db.session.get(User, session["user_id"])
    profile_user = User.query.filter_by(username=username).first()
    
    if not profile_user:
        flash("User not found!")
        return redirect(url_for("index"))
        
    is_following = current_user.followed.filter(followers.c.followed_id == profile_user.id).count() > 0
    return render_template("user_profile.html", current_user=current_user, profile_user=profile_user, is_following=is_following)

@app.route("/edit_profile", methods=["POST"])
@login_required
def edit_profile():
    current_user = db.session.get(User, session["user_id"])
    about_me = request.form.get("about_me")
    if about_me is not None:
        current_user.about_me = about_me
        db.session.commit()
        flash("Your profile bio has been updated.")
    return redirect(url_for('user_profile', username=current_user.username))

@app.route("/follow/<username>", methods=["POST"])
@login_required
def follow(username):
    current_user = db.session.get(User, session["user_id"])
    user_to_follow = User.query.filter_by(username=username).first()
    
    if not user_to_follow:
        flash("User not found.")
        return redirect(url_for("index"))
        
    if user_to_follow == current_user:
        flash("You cannot follow yourself!")
        return redirect(url_for("user_profile", username=username))
        
    current_user.followed.append(user_to_follow)
    db.session.commit()
    flash(f"You are now following {username}!")
    return redirect(url_for("user_profile", username=username))

@app.route("/unfollow/<username>", methods=["POST"])
@login_required
def unfollow(username):
    current_user = db.session.get(User, session["user_id"])
    user_to_unfollow = User.query.filter_by(username=username).first()
    
    if not user_to_unfollow:
        flash("User not found.")
        return redirect(url_for("index"))
        
    if user_to_unfollow == current_user:
        flash("You cannot unfollow yourself!")
        return redirect(url_for("user_profile", username=username))
        
    current_user.followed.remove(user_to_unfollow)
    db.session.commit()
    flash(f"You stopped following {username}.")
    return redirect(url_for("user_profile", username=username))

@app.route("/promote/<username>", methods=["POST"])
@admin_required
def promote_user(username):
    user_to_update = User.query.filter_by(username=username).first()
    if not user_to_update:
        flash("User not found.")
        return redirect(url_for('index'))
        
    # Backend Security: Prevent the owner from ever being demoted
    if user_to_update.role == 'owner':
        flash("The Owner cannot be demoted or modified!")
        return redirect(url_for('user_profile', username=username))
        
    action = request.form.get("action")
    if action == "promote":
        user_to_update.role = 'moderator'
        flash(f"{username} has been promoted to Moderator (Purple Cog)!")
    elif action == "promote_admin":
        user_to_update.role = 'admin'
        flash(f"{username} has been promoted to Admin (Blue Cog)!")
    elif action == "demote":
        user_to_update.role = 'user'
        flash(f"{username} has been demoted to a regular user.")
        
    db.session.commit()
    return redirect(url_for('user_profile', username=username))

@app.route("/delete_user/<int:user_id>", methods=["POST"])
@admin_required
def delete_user(user_id):
    user_to_delete = db.session.get(User, user_id)
    if not user_to_delete:
        flash("User not found.")
        return redirect(url_for('admin_dashboard'))
        
    # Backend Security: Prevent the owner from ever being deleted
    if user_to_delete.role == 'owner':
        flash("The Owner cannot be deleted!")
        return redirect(url_for('admin_dashboard'))
        
    # Prevent admin from accidentally deleting themselves
    current_user = db.session.get(User, session["user_id"])
    if user_to_delete.id == current_user.id:
        flash("You cannot delete yourself!")
        return redirect(url_for('admin_dashboard'))
        
    # NESTED DELETE: Wipe everything this user ever created!
    # 1. Delete their comments
    for comment in user_to_delete.comments:
        db.session.delete(comment)
    # 2. Delete their posts (and the comments attached to those posts)
    for post in user_to_delete.posts:
        for post_comment in post.comments:
            db.session.delete(post_comment)
        db.session.delete(post)
    # 3. Delete their blogs
    for blog in user_to_delete.owned_blogs:
        db.session.delete(blog)
        
    # Finally, delete the user
    db.session.delete(user_to_delete)
    db.session.commit()
    
    flash(f"User {user_to_delete.username} and ALL their content has been eradicated.")
    return redirect(url_for('admin_dashboard'))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        recaptcha_response = request.form.get("g-recaptcha-response")
        if not verify_recaptcha(recaptcha_response):
            flash("Please complete the reCAPTCHA.")
            return redirect(url_for("signup"))

        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if User.query.filter_by(email=email).first() or User.query.filter_by(username=username).first():
            flash("Email or username already exists!")
            return redirect(url_for("signup"))

        role = "user"
        admin_email = os.environ.get("ADMIN_EMAIL")
        if admin_email and email == admin_email:
            role = "owner"

        new_user = User(username=username, email=email, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash("Account created! You can now log in.")
        return redirect(url_for("login"))

    site_key = os.environ.get("RECAPTCHA_SITE_KEY", "")
    return render_template("signup.html", site_key=site_key)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        recaptcha_response = request.form.get("g-recaptcha-response")
        if not verify_recaptcha(recaptcha_response):
            flash("Please complete the reCAPTCHA.")
            return redirect(url_for("login"))

        email = request.form.get("email")
        password = request.form.get("password")
        
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            flash("Logged in successfully!")
            return redirect(url_for("index"))
        else:
            flash("Incorrect email or password.")
            
    site_key = os.environ.get("RECAPTCHA_SITE_KEY", "")
    return render_template("login.html", site_key=site_key)

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("You have been logged out.")
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)