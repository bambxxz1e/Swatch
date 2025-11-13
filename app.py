from flask import Flask, render_template, request, redirect, flash, url_for
from DBManager import DBManager
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os

load_dotenv()
SECRET_KEY = os.environ.get('SECRET_KEY')

app = Flask(__name__)
app.secret_key = SECRET_KEY
db = DBManager()
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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
            return render_template('main.html')
        else:
            flash("아이디 또는 비밀번호가 틀렸습니다.")
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/main')
def main():
    return render_template('main.html')

@app.route('/create', methods=['GET', 'POST'])
def create_post():
    uploaded_image = None

    if request.method == 'POST':
        title = request.form.get('title')
        music_query = request.form.get('music_query')

        file = request.files.get('image')
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)
            file.save(filepath)
            uploaded_image = filepath

        # DB 저장 로직
        # db.save_post(title=title, music_query=music_query, image_path=uploaded_image)

        flash('게시물이 성공적으로 등록되었습니다!')
        return redirect(url_for('create_post'))

    return render_template('create_post.html', uploaded_image=uploaded_image)

if __name__ == "__main__":
    app.run(debug=True)
