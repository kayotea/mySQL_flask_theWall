#server for The Wall
from flask import Flask, request, redirect, render_template, session, flash
from mysqlconnection import MySQLConnector
import re
import md5

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
app = Flask(__name__)
mysql = MySQLConnector(app,'the_wall')
app.secret_key = "dontyouknowthatyouretoxic"

@app.route('/')
def index():
    session['error_message'] = ""
    session['login_message'] = ""
    return render_template('index.html')

#login route
@app.route('/login', methods=['POST'])
def login():
    session['login_message'] = ""
    email = request.form['email']
    password = md5.new(request.form['password']).hexdigest()

    query = "SELECT email, password FROM users"
    logins = mysql.query_db(query)
    print logins

    for person in logins:
        if person['email'] == email and person['password'] == password:
            query = "SELECT id FROM users WHERE users.email = :the_email"
            query_data = {'the_email': email}
            session['login'] = mysql.query_db(query, query_data)[0]['id']

            session['login_message'] = "login success!"
            return redirect('/the_wall')

    session['login_message'] = "login failed"
    return redirect('/')

@app.route('/success')
def success():
    return render_template('success.html')

# registration form page
@app.route('/register')
def register():
    return render_template('register.html')

# take user input, validate
@app.route('/register/process', methods=['POST'])
def processRegistration():
    session['error_message'] = ""
    first = request.form['first']
    last = request.form['last']
    email = request.form['email']
    pw = request.form['pw']
    cpw = request.form['cpw']

    # if first name invalid, update error message
    if len(first) < 2 or not first.isalpha():
        session['error_message'] += "First name invalid. "
    # if last name invalid, update error message
    if len(first) < 2 or not last.isalpha():
        session['error_message'] += "Last name invalid. "
    #if email is invalid, update error message
    if not EMAIL_REGEX.match(email):
        session['error_message'] += "Email is not valid. "
    #if email is invalid, update error message
    if len(pw) < 8:
        session['error_message'] += "Password must be at least 8 characters. "
    #if email does not match confirmation email, update error message
    if pw != cpw:
        session['error_message'] += "Passwords do not match."

    # if there is an error message, redirect to register page
    if session['error_message']:
        return redirect('/register')
    # if there is no error message, add user into database
    else:
        query = "INSERT INTO users (first_name, last_name, email, password, created_at, updated_at) VALUES (:first_name, :last_name, :email, :password, NOW(), NOW())"
        data = {
            'first_name' : first,
            'last_name' : last,
            'email' : email,
            'password' : md5.new(pw).hexdigest()
        }
        mysql.query_db(query, data)
        # user is now registered and logged in
        query = "SELECT id FROM users WHERE users.email = :the_email"
        query_data = {'the_email': email}
        session['login'] = mysql.query_db(query, query_data)[0]['id']

        return redirect('/the_wall')
        # return redirect('/success')

#displays the wall of a particular user
@app.route('/the_wall')
def wall():
    query = "SELECT * FROM users WHERE id = :user_id"
    data = {'user_id' : session['login']}
    user = mysql.query_db(query, data)

    query = "SELECT id, user_id, message, DATE_FORMAT(created_at, '%b %D, %Y') AS date FROM messages"
    messages = mysql.query_db(query)

    query = "SELECT id, user_id, message_id, comment, DATE_FORMAT(created_at, '%b %D, %Y') AS date FROM comments"
    comments = mysql.query_db(query)

    query = "SELECT id, first_name, last_name FROM users"
    users = mysql.query_db(query)

    return render_template('wall.html', user=user[0], messages=messages, users=users, comments=comments)

@app.route('/post', methods=['POST'])
def post():
    query = "INSERT INTO messages (user_id, message, created_at, updated_at) VALUES (:user_id, :message, NOW(), NOW())"
    data = {
        'user_id' : session['login'],
        'message' : request.form['add_post']
    }
    mysql.query_db(query, data)
    return redirect('/the_wall')

@app.route('/comment', methods=['POST'])
def comment():
    query = "INSERT INTO comments (user_id, message_id, comment, created_at, updated_at) VALUES (:user_id, :message_id, :comment, NOW(), NOW())"
    data = {
        'user_id' : session['login'],
        'message_id' : request.form['mess_id'],
        'comment' : request.form['comment']
    }
    mysql.query_db(query, data)
    return redirect('/the_wall')

@app.route('/logoff')
def logoff():
    session['login'] = 0
    return render_template('index.html')

#used for debugging - directs to page that shows database contents
@app.route('/show')
def show():
    users = mysql.query_db("SELECT * FROM users")
    return render_template('show.html', users=users)

# delete comment
@app.route('/delete/comment/<comment_id>')
def delcomment(comment_id):
    query = "DELETE FROM comments WHERE id = :id"
    data = {"id": comment_id}
    mysql.query_db(query, data)
    return redirect('/the_wall')

# delete message
@app.route('/delete/message/<message_id>')
def delmessage(message_id):

    # FIRST: find the comments that belong to this message
    # and DELETE them
    query =  "SELECT * FROM messages"
    message_list = mysql.query_db(query)
    query = "SELECT * FROM comments"
    comment_list = mysql.query_db(query)
    print comment_list
    # print "message id:",message_id
    for message in message_list:
        # print message['id']
        if int(message['id']) == int(message_id):
            for comment in comment_list:
                if int(comment['message_id']) == int(message['id']):
                    print comment['message_id']
                    print comment['id']
                    del_comment(comment['id'])

    # NEXT: delete the message itself
    data = {'id' : message_id}
    query = "DELETE FROM messages WHERE id = :id"
    mysql.query_db(query, data)
    return redirect('/the_wall')

def del_comment(comment_id):
    query = "DELETE FROM comments WHERE id = :id"
    data = {"id": comment_id}
    mysql.query_db(query, data)
    return redirect('/the_wall')

app.run(debug=True)