from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import desc
import cgi
import os
import re
from hashz import make_pw_hash, check_pw_hash

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://get-it-done:beproductive@localhost:8889/blogz'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.config['SECRET_KEY'] = b'\xc6\xce\x18\xd2\x89l9\xc2\x85v4\xa2\xdf\xa7\x83\x91'

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.Text)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    pub_date = db.Column(db.DateTime)
    

    #id = db.Column(db.Integer, primary_key=True)
    #title = db.Column(db.String(120))
    #body = db.Column(db.String(1200))
    #completed = db.Column(db.DateTime)

      
    def __init__(self, title, body, owner, pub_date=None):
        self.title = title
        self.body = body
        self.owner = owner
        if pub_date is None:
            pub_date = datetime.utcnow()
        self.pub_date = pub_date
    
    #def __init__(self, title, body):
        #self.title = title
        #self.body = body
        #self.completed = datetime.utcnow()

    #def is_valid(self):
        #if self.title and self.body and self.completed:
            #return True
        #else:
            #return False

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    pw_hash = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.pw_hash = make_pw_hash(password)

@app.before_request
def require_login():
    allowed_routes = ['login', 'signup', 'index', 'blog']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')

@app.route('/')
def index():
    users = User.query.all()
    return render_template('index.html', users=users)

 
@app.route('/login', methods=['POST','GET'])
def login():
    username_error = ""
    password_error = ""

    if request.method == 'POST':
        password = request.form['password']
        username = request.form['username']
        user = User.query.filter_by(username=username).first()

        if user and check_pw_hash(password, user.pw_hash):
            session['username'] = username
            return redirect('/newpost')
        if not user:
            return render_template('login.html', username_error="Username does not exist.")
        else:
            return render_template('login.html', password_error="Your username or password was incorrect.")

    return render_template('login.html')

@app.route("/signup", methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']
        exist = User.query.filter_by(username=username).first()

        username_error = ""
        password_error = ""
        verify_error = ""

        if username == "":
            username_error = "Please enter a username."
        elif len(username) <= 3 or len(username) > 20:
            username_error = "Username must be between 3 and 20 characters long."
        elif " " in username:
            username_error = "Username cannot contain any spaces."
        if password == "":
            password_error = "Please enter a password."
        elif len(password) <= 3:
            password_error = "Password must be greater than 3 characters long."
        elif " " in password:
            password_error = "Password cannot contain any spaces."
        if password != verify or verify == "":
            verify_error = "Passwords do not match."
        if exist:
            username_error = "Username already taken."
        
        if len(username) > 3 and len(password) > 3 and password == verify and not exist:
            new_user = User(username, password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            return redirect('/newpost')
        else:
            return render_template('signup.html',)
            username=username,
            username_error=username_error,
            password_error=password_error,
            verify_error=verify_error
            

    return render_template('signup.html')

@app.route('/blog', methods=['POST', 'GET'])
def blog():
    blog_id = request.args.get('id')
    user_id = request.args.get('userid')
    posts = Blog.query.order_by(Blog.pub_date.desc())

    if blog_id:
        post = Blog.query.filter_by(id=blog_id).first()
        return render_template("post.html", title=post.title, body=post.body, user=post.owner.username, pub_date=post.pub_date, user_id=post.owner_id)
    if user_id:
        entries = Blog.query.filter_by(owner_id=user_id).all()
        return render_template('singleuser.html', entries=entries)

    return render_template('blog.html', posts=posts)


@app.route('/newpost')
def post():
    return render_template('newpost.html', title="New Post")

@app.route('/newpost', methods=['POST', 'GET'])
def newpost():
    title = request.form['title']
    body = request.form["body"]
    owner = User.query.filter_by(username=session['username']).first()

    title_error = ""
    body_error = ""

    if title == "":
        title_error = "Title required."
    if body == "":
        body_error = "Content required."

    if not title_error and not body_error:
        new_post = Blog(title, body, owner)
        db.session.add(new_post)
        db.session.commit()
        page_id = new_post.id
        return redirect("/blog?id={0}".format(page_id))
    else:
        return render_template("newpost.html",
            title = title,
            body = body,
            title_error = title_error,
            body_error = body_error
        )

@app.route('/logout')
def logout():
    del session['username']
    return redirect('/blog')

if __name__ == '__main__':
    app.run()

#@app.route('/')
#def index():
    #return redirect('/blog')


#@app.route('/blog')
#def blog_index():
    #blog_id = request.args.get('id')
    #blogs = Blog.query.all()

    #if blog_id:
        #post = Blog.query.get(blog_id)
        #blog_title = post.title
        #blog_body = post.body
        #return render_template('entry.html', title="Blog Entry #" + blog_id, blog_title=blog_title, blog_body=blog_body)

    #sort = request.args.get('sort')

    #if (sort=="newest"):
        #blogs = Blog.query.order_by(Blog.completed.desc()).all()
    #elif (sort=="oldest"):
        #blogs = Blog.query.order_by(Blog.completed.asc()).all()
    #else:
        #blogs = Blog.query.all()
    #return render_template('blog.html', title="Build A Blog", blogs=blogs)

#@app.route('/post')
#def new_post():
    #return render_template('post.html', title="Add New Blog Entry")

#@app.route('/post', methods=['POST'])
#def verify_post():
    #blog_title = request.form['title']
    #blog_body = request.form['body']
    #title_error = ''
    #body_error = ''

    #date_posted='Month Day, Year'

    #if blog_title == "":
        #title_error = "Title required."
    #if blog_body == "":
        #body_error = "Content required."


    #if not title_error and not body_error:
        #new_blog = Blog(blog_title, blog_body)
        #db.session.add(new_blog)
        #db.session.commit()
        #blog = new_blog.id
        
        #return redirect('/blog?id={0}'.format(blog))
    #else:
        
        #return render_template('post.html', title="Add New Blog Entry", blog_title = blog_title, blog_body = blog_body, title_error = title_error, body_error = body_error, date_posted = date_posted())
    #tasks = Task.query.filter_by(completed=False).all()
    #completed_tasks = Task.query.filter_by(completed=True).all()
    #return render_template('todos.html',title="Get It Done!", 
        #tasks=tasks, completed_tasks=completed_tasks)