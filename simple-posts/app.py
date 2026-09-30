from flask import Flask, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from html import escape
import sqlite3

app = Flask(__name__)
app.secret_key = "mysecretkey123"

texts = {
    "ru": {
        "site_title": "Мой сайт",
        "hello": "Привет",
        "logout": "Выйти",
        "login": "Войти",
        "register": "Регистрация",
        "publish": "Опубликовать",
        "all_posts": "Все посты",
        "no_posts": "Постов пока нет",
        "username": "Логин",
        "password": "Пароль",
        "do_register": "Зарегистрироваться",
        "login_title": "Вход",
        "to_main": "На главную",
        "fill_all": "Заполните все поля",
        "user_exists": "Такой пользователь уже есть",
        "wrong_login": "Неправильный логин или пароль",
    },
    "en": {
        "site_title": "My site",
        "hello": "Hello",
        "logout": "Log out",
        "login": "Log in",
        "register": "Sign up",
        "publish": "Publish",
        "all_posts": "All posts",
        "no_posts": "No posts yet",
        "username": "Username",
        "password": "Password",
        "do_register": "Sign up",
        "login_title": "Log in",
        "to_main": "Home",
        "fill_all": "Please fill in all fields",
        "user_exists": "This user already exists",
        "wrong_login": "Wrong username or password",
    },
}


def t(key):
    lang = session.get("lang", "ru")
    return texts[lang][key]


def lang_links():
    return "<p><a href='/lang/ru'>RU</a> | <a href='/lang/en'>EN</a></p>"


@app.route("/lang/<code>")
def change_lang(code):
    if code in texts:
        session["lang"] = code
    # возвращаемся на ту страницу, где были
    return redirect(request.referrer or "/")


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

    html = lang_links()
    html += "<h1>" + t("site_title") + "</h1>"

    if "username" in session:
        html += "<p>" + t("hello") + ", " + escape(session["username"]) + "! <a href='/logout'>" + t("logout") + "</a></p>"
        html += "<form method='post' action='/add'>"
        html += "<textarea name='text'></textarea><br>"
        html += "<button type='submit'>" + t("publish") + "</button>"
        html += "</form>"
    else:
        html += "<p><a href='/login'>" + t("login") + "</a> | <a href='/register'>" + t("register") + "</a></p>"

    html += "<h2>" + t("all_posts") + "</h2>"
    if len(posts) == 0:
        html += "<p>" + t("no_posts") + "</p>"
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
            message = t("fill_all")
        else:
            conn = get_db()
            user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            if user:
                message = t("user_exists")
            else:
                conn.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                             (username, generate_password_hash(password)))
                conn.commit()
                conn.close()
                return redirect("/login")
            conn.close()

    html = lang_links()
    html += "<h1>" + t("register") + "</h1>"
    html += "<p>" + message + "</p>"
    html += "<form method='post'>"
    html += t("username") + ": <input name='username'><br>"
    html += t("password") + ": <input name='password' type='password'><br>"
    html += "<button type='submit'>" + t("do_register") + "</button>"
    html += "</form>"
    html += "<a href='/'>" + t("to_main") + "</a>"
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
            message = t("wrong_login")

    html = lang_links()
    html += "<h1>" + t("login_title") + "</h1>"
    html += "<p>" + message + "</p>"
    html += "<form method='post'>"
    html += t("username") + ": <input name='username'><br>"
    html += t("password") + ": <input name='password' type='password'><br>"
    html += "<button type='submit'>" + t("login") + "</button>"
    html += "</form>"
    html += "<a href='/'>" + t("to_main") + "</a>"
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