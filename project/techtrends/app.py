import sqlite3
import logging
import sys
from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

# Function to get a database connection.
# This function connects to database with the name `database.db`

def get_db_connection():
    try:
        connection = sqlite3.connect('database.db')
        connection.row_factory = sqlite3.Row
        one_row = connection.execute("SELECT * FROM posts LIMIT 1;")

        app.config["total_conn"] += 1
    except Exception as ex:
        app.logger.error("No database connection found! Contact admin")
        return False

    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'
app.config["total_conn"] = 0
app.config["total_posts"] = 0


# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    total_posts = len(posts)
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        app.logger.error('Page not found - Return 404 Page')
        return render_template('404.html'), 404
    else:
        app.logger.info('Article "{}" is retrieved!'.format(post['title']))
        return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.info('The "About Us" page is retrieved')
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
            app.logger.info('Article "{}" is created!'.format(title))
            return redirect(url_for('index'))

    return render_template('create.html')

@app.route('/healthz')
def healthz():
    connection = get_db_connection()
    response = app.response_class(
        response=json.dumps(
            connection and {"result" : "OK - healthy"} or {"result" : "ERROR - unhealthy"}), 
            status= connection and 200 or 500, 
            mimetype="application/json"
        )
    return response

@app.route('/metric')
def metric():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    app.config["total_posts"] = len(posts)

    response = app.response_class(
            response = json.dumps({"db_connection_count" : app.config["total_conn"], "post_count":app.config["total_posts"]}), status=200, mimetype="application/json"
    )
    return response



# start the application on port 3111
if __name__ == "__main__":
    app_logger = logging.getLogger(__name__)
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.DEBUG,
        datefmt='%Y-%m-%d %H:%M:%S')
    log_handler1 = logging.StreamHandler(sys.stdout)
    log_handler2 = logging.StreamHandler(sys.stderr)
    log_handler1.setLevel(logging.DEBUG)
    log_handler2.setLevel(logging.DEBUG)

    app_logger.addHandler(log_handler1)
    app_logger.addHandler(log_handler2)
    app.run(host='0.0.0.0', port='3111')
