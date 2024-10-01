from flask import Blueprint, render_template, request, redirect, url_for, session
from pymongo import MongoClient
import bcrypt

auth = Blueprint('auth', __name__)

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['discussion_forum']
users = db['users']

# Hash password
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# Verify password
def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)

# Signup route
@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        
        # Check if user already exists
        if users.find_one({'email': email}):
            return render_template('signup.html', error='Email already exists. Please choose another one.')
        
        # Hash password
        hashed_password = hash_password(password)
        
        # Insert user into the database
        users.insert_one({'email': email, 'username': username, 'password': hashed_password})
        
        # Redirect to login page
        return redirect(url_for('auth.login'))
    return render_template('signup.html')

# Login route
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Check if user exists
        user = users.find_one({'email': email})
        if user:
            # Verify password
            if verify_password(password, user['password']):
                # Set session variables
                session['user'] = str(user['_id'])
                return redirect(url_for('index'))
        return render_template('login.html', error='Invalid email or password')
    return render_template('login.html')

@auth.route('/logout', methods=['POST'])
def logout():
    # Clear the user session
    session.pop('user', None)
    return redirect(url_for('auth.login'))
