from flask import Flask
app = Flask(__name__)

from flask import Flask, flash, jsonify, redirect, render_template, request, session, json
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date
from helpers import login_required
from flask_session import Session
from datetime import datetime, timedelta, date
import pandas as pd
import sqlite3

TODAY = str(datetime.today().strftime('%Y-%m-%d'))
print(TODAY)
RECORD = False

# Create sqlite3 database
import sqlite3
db = sqlite3.connect('database.db')

# Creating tables
#db.execute('CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT, hash TEXT)')
#db.execute('CREATE TABLE habits (habit_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, user_id INTEGER NOT NULL, habit TEXT, rating INTEGER, date TEXT)')
#db.execute('CREATE TABLE habitlist (habit_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, user_id INTEGER NOT NULL, habit TEXT, type TEXT)')

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

# Log new habit
@app.route('/log', methods=["GET", "POST"])
@login_required
def log():
    connection = sqlite3.connect('database.db')
    db = connection.cursor()
    habit_list = list(set(list(db.execute("SELECT habit from habitlist WHERE user_id = ?", (session["user_id"],)))))
   
    if request.method == "POST":
        habit = request.form.get("habit")
        rating = request.form.get("rating")
        db.execute('INSERT INTO habits(user_id,habit,rating, date) VALUES(?,?,?,?)', (session["user_id"], habit, rating, TODAY))
        connection.commit()
        connection.close()

    return render_template("log.html", habit_list = habit_list)

# Add new habit
@app.route('/new', methods=["GET", "POST"])
@login_required
def new():
    connection = sqlite3.connect('database.db')
    db = connection.cursor()
    if request.method == "POST":
        
        habit = request.form.get("habit")
        habit_type = "binary"


        db.execute('INSERT INTO habitlist(user_id,habit,type) VALUES(?,?,?)', (session["user_id"], habit, habit_type))
        connection.commit()
        #onnection.close()

    return render_template("new.html")

# Delete current habit
@app.route('/delete', methods=["GET", "POST"])
@login_required
def delete():
    connection = sqlite3.connect('database.db')
    db = connection.cursor()

    # show list of current habits
    habit_list = list(set(list(db.execute("SELECT habit from habitlist WHERE user_id = ?", (session["user_id"],)))))
    # db.execute('DELETE FROM habitlist WHERE user_id = 1')
    # db.execute('DELETE FROM habits WHERE user_id = 1')

    #connection.commit()

    if request.method == "POST":
        habit = request.form.get("habit")
        
        db.execute("DELETE FROM habitlist WHERE user_id = ? AND habit = ?", (session["user_id"], habit))

        connection.commit()
        #connection.close()

        return redirect("/delete")
    else:
        return render_template("delete.html", habit_list = habit_list)

# Homepage - show dashboard
@app.route('/', methods=["GET", "POST"])
@login_required
def index():
    connection = sqlite3.connect('database.db')
    db = connection.cursor()

    # Get time period; default is 7 days
    time = 7
    if request.form.get("days"):
        time = int(request.form.get("days"))

    date_list = pd.date_range(end = TODAY, periods = time).to_pydatetime().tolist()
    dates = [str(i.strftime('%Y-%m-%d')) for i in date_list]

    # Dictionary to hold habits' data; to be converted to json
    data_dict = {}

    # List of all habits we have (set)
    habit_list = list(set(list(db.execute("SELECT habit from habitlist WHERE user_id = ?", (session["user_id"],)))))

    # For every habit
    for h in habit_list:
        # Get rating and date
        data_list = list(db.execute("SELECT rating, date from habits WHERE user_id = ? AND habit = ?", (session["user_id"], h[0])))
        # Create temp list of dates for which ratings are collected
        dates_temp = [i[1] for i in data_list]
        # If today is not logged yet, add point at end
        if TODAY not in dates_temp:
            data_list.append((0,))
        # Iterate over dates list that determines x-axis; check if date is in dates_temp; if not, create 0 rating
        for d in dates:
            if d not in dates_temp:
                data_list.insert(0, (None, d))

        if data_list != []:
            #print(h[0], [i[0] for i in data_list])
            #print(list(data_list[0]))
            data_dict[h[0]] = [i[0] for i in data_list]

    connection.commit()
    connection.close()

    return render_template("index.html.j2", data=json.dumps(data_dict), habit_list=habit_list, dates=dates)

#Register as a new user
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
        rows = db.execute("SELECT * FROM users WHERE username = ?", (username,) )
        print("Username exists!")

        # Ensure password was submitted
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

# Login as current user
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

        # Remember which user has logged in
        session["user_id"] = results[0][0]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    return render_template("login.html")

# Logout of session
@app.route("/logout")
def logout():
    """Log user out"""
    # Forget any user_id
    session.clear()
    # Redirect user to login form
    return redirect("/")




    #git push -u origin main
    # git push origin HEAD:master
    #git push heroku