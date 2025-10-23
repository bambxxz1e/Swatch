from flask import Flask, render_template, request, redirect, flash, url_for
from DBManager import DBManager
from dotenv import load_dotenv
import os

load_dotenv()
SECRET_KEY = os.environ.get('SECRET_KEY')

app = Flask(__name__)
app.secret_key = SECRET_KEY
db = DBManager()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        user_id = request.form['user_id']
        password = request.form['password']

        success, msg = db.signup(user_id, password)

        if success:
            flash(msg)  # 메시지를 flash로 저장
            return redirect(url_for('index'))
        else:
            flash(msg)
            return redirect(url_for('signup'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        user_id = request.form['user_id']
        password = request.form['password']

        if db.login(user_id, password):
            flash("로그인 성공!")
            return render_template('main.html')
        else:
            flash("아이디 또는 비밀번호가 틀렸습니다.")
            return redirect(url_for('login'))
    return render_template('login.html')

if __name__ == "__main__":
    app.run(debug=True)
