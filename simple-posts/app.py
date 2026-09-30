from flask import Flask, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from html import escape
import sqlite3

app = Flask(__name__)
app.secret_key = "mysecretkey123"


def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, text TEXT)")
    conn.commit()
    conn.close()


@app.route("/")
def index():
    conn = get_db()
    posts = conn.execute("SELECT * FROM posts ORDER BY id DESC").fetchall()
    conn.close()

    html = "<h1>Мой сайт</h1>"

    if "username" in session:
        html += "<p>Привет, " + escape(session["username"]) + "! <a href='/logout'>Выйти</a></p>"
        html += "<form method='post' action='/add'>"
        html += "<textarea name='text'></textarea><br>"
        html += "<button type='submit'>Опубликовать</button>"
        html += "</form>"
    else:
        html += "<p><a href='/login'>Войти</a> | <a href='/register'>Регистрация</a></p>"

    html += "<h2>Все посты</h2>"
    if len(posts) == 0:
        html += "<p>Постов пока нет</p>"
    for post in posts:
        html += "<p><b>" + escape(post["username"]) + "</b>: " + escape(post["text"]) + "</p>"

    return html


@app.route("/register", methods=["GET", "POST"])
def register():
    message = ""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "" or password == "":
            message = "Заполните все поля"
        else:
            conn = get_db()
            user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            if user:
                message = "Такой пользователь уже есть"
            else:
                conn.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                             (username, generate_password_hash(password)))
                conn.commit()
                conn.close()
                return redirect("/login")
            conn.close()

    html = "<h1>Регистрация</h1>"
    html += "<p>" + message + "</p>"
    html += "<form method='post'>"
    html += "Логин: <input name='username'><br>"
    html += "Пароль: <input name='password' type='password'><br>"
    html += "<button type='submit'>Зарегистрироваться</button>"
    html += "</form>"
    html += "<a href='/'>На главную</a>"
    return html


@app.route("/login", methods=["GET", "POST"])
def login():
    message = ""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["username"] = username
            return redirect("/")
        else:
            message = "Неправильный логин или пароль"

    html = "<h1>Вход</h1>"
    html += "<p>" + message + "</p>"
    html += "<form method='post'>"
    html += "Логин: <input name='username'><br>"
    html += "Пароль: <input name='password' type='password'><br>"
    html += "<button type='submit'>Войти</button>"
    html += "</form>"
    html += "<a href='/'>На главную</a>"
    return html


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect("/")


@app.route("/add", methods=["POST"])
def add():
    if "username" not in session:
        return redirect("/login")

    text = request.form["text"]
    if text != "":
        conn = get_db()
        conn.execute("INSERT INTO posts (username, text) VALUES (?, ?)", (session["username"], text))
        conn.commit()
        conn.close()
    return redirect("/")


if __name__ == "__main__":
    init_db()
    app.run(debug=True)