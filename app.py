import sqlite3

from flask import Flask, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort
from datetime import datetime
import logging
from os import system
import sys

# Count all database connections
connection_count = 0

# set logger to handle STDOUT and STDERR 
logger = logging.getLogger('techtrends_logs')

log_format = logging.Formatter('%(levelname)s:%(asctime)s - %(message)s')

logger.setLevel(logging.DEBUG)
print(logging.getLevelName(logger.level))
if logging.getLevelName(logger.level) == 'INFO' or 'DEBUG':
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(log_format)
    stdout_handler.setLevel(logging.getLevelName(logger.level))
    logger.addHandler(stdout_handler)
else:
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(log_format)
    stderr_handler.setLevel(logging.getLevelName(logger.level))
    logger.addHandler(stderr_handler)
    
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
                              (post_id, )).fetchone()
    connection.close()
    return post


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
        logger.error(
            'Article with id "{id}" does not exist!'.format(id=post_id))
        return render_template('404.html'), 404
    else:
        logger.info('Article "{title}" retrieved!'.format(title=post['title']))
        return render_template('post.html', post=post)


# Define the About Us page
@app.route('/about')
def about():
    logger.info('About page rendered!')
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
            connection.execute(
                'INSERT INTO posts (title, content) VALUES (?, ?)',
                (title, content))
            connection.commit()
            connection.close()
            logger.info('Article "{title}" created!'.format(title=title))
            return redirect(url_for('index'))
    return render_template('create.html')


# Define healthz endpoint
@app.route('/healthz')
def healthz():
    try:
        connection = get_db_connection()
        connection.cursor()
        connection.execute('SELECT * FROM posts')
        connection.close()
        return {'result': 'OK - healthy'}
    except Exception:
        return {'result': 'ERROR - unhealthy'}, 500


# Define metrics endpoint
@app.route('/metrics')
def metrics():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    post_count = len(posts)
    data = {"db_connection_count": connection_count, "post_count": post_count}
    return data



# start the application on port 3111
if __name__ == "__main__":
    ## stream logs to a file
    #logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

    app.run(host='0.0.0.0', port='3111')