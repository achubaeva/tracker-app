from flask import Flask
app = Flask(__name__)

from flask import Flask, flash, jsonify, redirect, render_template, request, session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date
from helpers import login_required
from flask_session import Session
from datetime import datetime
import sqlite3

TODAY = datetime.today().strftime('%Y-%m-%d')
print(TODAY)
RECORD = False

# add column to users that stores dictionary with habits and types

# Create sqlite3 database
import sqlite3
db = sqlite3.connect('database.db')
#db.execute('DROP TABLE habits')
#db.execute('CREATE TABLE habits (habit_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, user_id INTEGER NOT NULL, habit TEXT, rating INTEGER, date TEXT)')


# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route('/log', methods=["GET", "POST"])
@login_required
def log():
    connection = sqlite3.connect('database.db')
    db = connection.cursor()
    habit_list = list(db.execute("SELECT habit from habits WHERE user_id = ?", (session["user_id"],)))
    
    habit = request.form.get("habit")
    rating = request.form.get("rating")


    db.execute('INSERT INTO habits(user_id,habit,rating, date) VALUES(?,?,?,?)', (session["user_id"], "habit", rating, '2020-11-15'))
    connection.commit()
    connection.close()
    
    return render_template("log.html", habit_list = habit_list)


@app.route('/')
@login_required
def index():
    return render_template("index.html")

@app.route('/new', methods=["GET", "POST"])
@login_required
def new():
    connection = sqlite3.connect('database.db')
    db = connection.cursor()
    if request.method == "POST":
        
        habit = request.form.get("habit")
        habit_type = request.form.get("type")


        db.execute('INSERT INTO habits(user_id,habit) VALUES(?,?)', (session["user_id"], habit))
        connection.commit()
        connection.close()

    return render_template("new.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    connection = sqlite3.connect('database.db')
    db = connection.cursor()
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            print("No username provided")

        username=request.form.get("username")

        # Ensure username does not exist
        # TO DO
        rows = db.execute("SELECT * FROM users WHERE username = ?", (username,) )
        print("Username exists!")

        # Ensure password was submitted
        # TO DO
        if not request.form.get("password"):
            print("Password not provided")

        # Ensure password matches confirmation
        if request.form.get("password") != request.form.get("confirmation"):
             print("Passwords do not match")
        
        password=generate_password_hash(request.form.get("password"))

        # Add new user (username, id, password, hash password)
        db.execute('INSERT INTO users(username, hash) VALUES(?,?)', (username, password))
        connection.commit()
        connection.close()
        return redirect("/")
    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    connection = sqlite3.connect('database.db')
    db = connection.cursor()

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return "need username"
        
        username=request.form.get("username")

        # Ensure password was submitted
        if not request.form.get("password"):
            return "need password"

        password=request.form.get("password")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", (username,) )
        results = list(rows)
        given_username = results[0][1]

              # Ensure username exists and password is correct
        if not check_password_hash(results[0][2], password):
            print("invalid username and/or password")
    #     # Ensure username exists and password is correct
    #     if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
    #         return apology("invalid username and/or password", 403)

    #     # Remember which user has logged in
        session["user_id"] = results[0][0]

        #Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    # else:
    return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""
    # Forget any user_id
    session.clear()
    # Redirect user to login form
    return redirect("/")




    #git push -u origin main