import logging
import sqlite3

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort
from datetime import datetime

# Count all database connections
connection_count = 0

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    global connection_count
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    connection_count += 1
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

def get_article_count(metrics_obj):
    """
    Count the number of articles and increment the number of connections used
    Parameters:
    metrics_obj (dict): Dictionary with basic data for metrics endpoint response
    """
    connection = get_db_connection()
    article_count = connection.execute('SELECT count(*) FROM posts').fetchone()
    connection.close()

    metrics_obj['db_connection_count'] += 1
    metrics_obj['post_count'] = article_count[0]


def valid_db_connection():
    """
    Checks if connecting to database is successful.
    """
    try:
        connection = get_db_connection()
        connection.close()
    except:
        raise Exception("Database connection failure")


def post_table_exists():
    """
    Checks if POST table exists.
    """
    try:
        connection = get_db_connection()
        connection.execute('SELECT 1 FROM posts').fetchone()
        connection.close()
    except:
        raise Exception("Table 'posts' does not exist")

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
      return render_template('404.html'), 404
    else:
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()

            return redirect(url_for('index'))

    return render_template('create.html')

@app.route('/healthz', methods=['GET'])
def healthz():
    try:
        connection = get_db_connection()
        connection.cursor()
        connection.execute('SELECT * FROM posts')
        connection.close()
        return {'result': 'OK - healthy'}
    except Exception:
        return {'result': 'ERROR - unhealthy'}, 500


@app.route('/metrics', methods=['GET'])
def metrics():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    post_count = len(posts)
    data = {"db_connection_count": connection_count, "post_count": post_count}
    return data

#Function that logs messages
def log_message(msg):
    app.logger.info('{time} | {message}'.format(
        time=datetime.now().strftime("%m/%d/%Y, %H:%M:%S"), message=msg))

# start the application on port 3111
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
app.run(host='0.0.0.0', port='3111')
