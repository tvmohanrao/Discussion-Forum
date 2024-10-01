from flask import Flask, render_template, redirect, url_for, session, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
import os
from auth import auth  # Import the auth blueprint

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generate a 24-byte (48-character) random string

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['discussion_forum']
threads = db['threads']
users = db['users']  # Collection for user information
likes_dislikes = db['likes_dislikes']  # Collection for storing likes and dislikes

# Register blueprint
app.register_blueprint(auth)

# Pass str() function to Jinja2 environment
@app.context_processor
def utility_processor():
    return dict(str=str)

@app.route('/')
def index():
    if 'user' in session:
        # User is logged in
        user_info = users.find_one({'_id': ObjectId(session['user'])})
        if user_info:
            username = user_info['username']
            email = user_info['email']  # Retrieve email
            all_threads = list(threads.find())
            return render_template('index.html', user=username, email=email, threads=all_threads)
        else:
            return redirect(url_for('auth.login'))
    else:
        # User is not logged in
        return redirect(url_for('auth.login'))


@app.route('/create_thread', methods=['POST'])
def create_thread():
    if 'user' in session:
        # User is logged in
        title = request.form['title']
        content = request.form['content']
        username = users.find_one({'_id': ObjectId(session['user'])})['username']  # Retrieve username
        # Insert the new thread into the 'threads' collection
        new_thread = {'title': title, 'content': content, 'username': username, 'comments': []}
        threads.insert_one(new_thread)
        return redirect(url_for('index'))
    else:
        # User is not logged in
        return redirect(url_for('auth.login'))

@app.route('/add_comment/<string:thread_id>', methods=['POST'])
def add_comment(thread_id):
    if 'user' in session:
        # User is logged in
        text = request.form['text']
        # Find the thread by its ID
        thread = threads.find_one({'_id': ObjectId(thread_id)})
        if thread:
            # Append the new comment to the 'comments' list of the thread
            new_comment = {'username': users.find_one({'_id': ObjectId(session['user'])})['username'], 'text': text}
            threads.update_one({'_id': ObjectId(thread_id)}, {'$push': {'comments': new_comment}})
        return redirect(url_for('index'))
    else:
        # User is not logged in
        return redirect(url_for('auth.login'))

@app.route('/delete_thread/<string:thread_id>', methods=['POST'])
def delete_thread(thread_id):
    if 'user' in session:
        # User is logged in
        username = users.find_one({'_id': ObjectId(session['user'])})['username']
        thread = threads.find_one({'_id': ObjectId(thread_id)})
        if thread and thread['username'] == username:  # Check if the user is the creator of the thread
            threads.delete_one({'_id': ObjectId(thread_id)})
    return redirect(url_for('index'))

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q')  # Get the search query from the URL query parameters
    if query:
        # Perform search logic here based on the query
        thread_results = threads.find({'$text': {'$search': query}})
        return render_template('search_results.html', query=query, thread_results=thread_results)
    else:
        # If no query is provided, return a message indicating no search query
        return "No search query provided"
    

# Route for liking a thread
@app.route('/like_thread/<string:thread_id>', methods=['POST'])
def like_thread(thread_id):
    if 'user' in session:
        user_id = session['user']
        # Check if the user has already liked the thread
        existing_like = likes_dislikes.find_one({'user_id': user_id, 'thread_id': ObjectId(thread_id), 'type': 'like'})
        if not existing_like:
            # Increment the like count in the threads collection
            threads.update_one({'_id': ObjectId(thread_id)}, {'$inc': {'likes': 1}})
            # Insert the like into the likes_dislikes collection
            likes_dislikes.insert_one({'user_id': user_id, 'thread_id': ObjectId(thread_id), 'type': 'like'})
            return jsonify({'success': True})
    return jsonify({'success': False})

# Route for disliking a thread
@app.route('/dislike_thread/<string:thread_id>', methods=['POST'])
def dislike_thread(thread_id):
    if 'user' in session:
        user_id = session['user']
        # Check if the user has already disliked the thread
        existing_dislike = likes_dislikes.find_one({'user_id': user_id, 'thread_id': ObjectId(thread_id), 'type': 'dislike'})
        if not existing_dislike:
            # Increment the dislike count in the threads collection
            threads.update_one({'_id': ObjectId(thread_id)}, {'$inc': {'dislikes': 1}})
            # Insert the dislike into the likes_dislikes collection
            likes_dislikes.insert_one({'user_id': user_id, 'thread_id': ObjectId(thread_id), 'type': 'dislike'})
            return jsonify({'success': True})
    return jsonify({'success': False})




if __name__ == '__main__':
    app.run(debug=True, port=5001)
