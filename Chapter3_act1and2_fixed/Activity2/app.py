from flask import Flask, render_template, request, redirect, url_for, session
from db import get_db
import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'
db = get_db()

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('feed'))
    return redirect(url_for('login'))

# --- Task 2: Authentication Logic ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    # TODO: Verify if username exists in the database
    if request.method == 'POST':
        username = request.form['username']
        # --- Answer Start: User Verification ---
        user = db.users.find_one({'username': username})
        if user:
            session['user_id'] = username
            return redirect(url_for('feed'))
        return f"User '{username}' not found. <a href='{url_for('login')}'>Try again</a> or <a href='{url_for('register')}'>Register</a>"
        # --- Answer End ---
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    # TODO: Check if username exists; if not, insert new user
    if request.method == 'POST':
        username = request.form['username']
        # --- Answer Start: Check Duplicate and Insert User ---
        if db.users.find_one({'username': username}):
            return f"Username '{username}' already exists. <a href='{url_for('register')}'>Try another</a> or <a href='{url_for('login')}'>Login</a>"
        db.users.insert_one({
            'username': username,
            'followers': [],
            'following': [],
            'created_at': datetime.datetime.now()
        })
        session['user_id'] = username
        return redirect(url_for('feed'))
        # --- Answer End ---
    return render_template('register.html')

# --- Task 2: Feed Logic ---

@app.route('/feed', methods=['GET'])
def feed():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    current_user = session['user_id']
    
    # TODO: Use Aggregation Pipeline ($lookup) to get posts with author details
    # Aggregation Pipeline: Join posts with user info to get the author's details handy (if needed) structure
    # --- Answer Start: Aggregation Pipeline ($lookup) ---
    pipeline = [
        {'$lookup': {
            'from': 'users',
            'localField': 'username',
            'foreignField': 'username',
            'as': 'author'
        }},
        {'$unwind': {'path': '$author', 'preserveNullAndEmptyArrays': True}},
        {'$sort': {'created_at': -1}}
    ]
    posts = list(db.posts.aggregate(pipeline))
    # --- Answer End ---
    
    # Collect all usernames to fetch their follower counts
    
    # Collect all usernames to fetch their follower counts
    usernames = set()
    for post in posts:
        usernames.add(post['username'])
        for comment in post.get('comments', []):
            usernames.add(comment['username'])
            
    # Fetch user data
    users = db.users.find({'username': {'$in': list(usernames)}})
    user_counts = {u['username']: len(u.get('followers', [])) for u in users}
    
    return render_template('feed.html', posts=posts, current_user=current_user, user_counts=user_counts)

# --- Task 2: Post Creation (Create Post) ---

@app.route('/post', methods=['GET', 'POST'])
def create_post():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'GET':
        return redirect(url_for('feed'))
    
    caption = request.form['caption']
    image_url = request.form['image_url']
    
    # TODO: Insert new post document (username, caption, image_url, created_at, comments=[])
    # --- Answer Start: Insert Post Document ---
    db.posts.insert_one({
        'username': session['user_id'],
        'caption': caption,
        'image_url': image_url,
        'created_at': datetime.datetime.now(),
        'comments': []
    })
    # --- Answer End ---
    return redirect(url_for('feed'))

# --- Task 2: Post Creation (Add Comment) ---

@app.route('/post/<post_id>/comment', methods=['GET', 'POST'])
def add_comment(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'GET':
        return redirect(url_for('feed'))
    
    comment_text = request.form['comment']
    from bson.objectid import ObjectId
    
    # TODO: Use $push to add a new comment to the post's 'comments' list
    # Update using $push to add embedded comment
    # --- Answer Start: Update with $push ---
    db.posts.update_one(
        {'_id': ObjectId(post_id)},
        {'$push': {'comments': {
            'username': session['user_id'],
            'text': comment_text,
            'created_at': datetime.datetime.now()
        }}}
    )
    # --- Answer End ---
    return redirect(url_for('feed'))

# --- Task 2: Profile Logic ---

@app.route('/user/<username>')
def profile(username):
    # TODO: Fetch user profile and all posts by this user (sorted by date)
    # --- Answer Start: Fetch User and Posts ---
    user = db.users.find_one({'username': username})
    if not user:
        return f"User '{username}' not found. <a href='{url_for('feed')}'>Back to feed</a>", 404
    user_posts = list(db.posts.find({'username': username}).sort('created_at', -1))
    # --- Answer End ---
    
    return render_template('profile.html', user=user, posts=user_posts, current_user=session.get('user_id'))

# --- Task 2: Relationship Management (Follow) ---

@app.route('/follow/<target_user>', methods=['GET', 'POST'])
def follow(target_user):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'GET':
        return redirect(url_for('profile', username=target_user))
        
    current_user = session['user_id']
    
    # TODO: Update TWO documents using $addToSet
    # 1. Add target_user to current_user's 'following'
    # 2. Add current_user to target_user's 'followers'
    
    # --- Answer Start: Update Relationships ($addToSet) ---
    if current_user != target_user and db.users.find_one({'username': target_user}):
        db.users.update_one({'username': current_user}, {'$addToSet': {'following': target_user}})
        db.users.update_one({'username': target_user}, {'$addToSet': {'followers': current_user}})
    # --- Answer End ---
    
    return redirect(url_for('profile', username=target_user))

# --- Task 2: Relationship Management (Unfollow) ---

@app.route('/unfollow/<target_user>', methods=['GET', 'POST'])
def unfollow(target_user):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'GET':
        return redirect(url_for('profile', username=target_user))
        
    current_user = session['user_id']
    
    # TODO: Update TWO documents using $pull
    # 1. Remove target_user from current_user's 'following'
    # 2. Remove current_user from target_user's 'followers'
    
    # --- Answer Start: Remove Relationships ($pull) ---
    db.users.update_one({'username': current_user}, {'$pull': {'following': target_user}})
    db.users.update_one({'username': target_user}, {'$pull': {'followers': current_user}})
    # --- Answer End ---
    
    return redirect(url_for('profile', username=target_user))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
