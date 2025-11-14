from flask import Flask, render_template, request, redirect, flash, url_for, session
from DBManager import DBManager
from werkzeug.utils import secure_filename
import base64
import requests
from dotenv import load_dotenv
import os

load_dotenv()
SECRET_KEY = os.environ.get('SECRET_KEY')
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')

app = Flask(__name__)
app.secret_key = SECRET_KEY
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = DBManager()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == "POST":
        user_id = request.form['user_id']
        password = request.form['password']
        action = request.form.get('action')  # login or signup

        if action == "login":
            if db.login(user_id, password):
                session['user_id'] = user_id
                flash(f"{user_id}님, 환영합니다!")
                return redirect(url_for('main'))
            else:
                flash("아이디 또는 비밀번호가 틀렸습니다.")
        elif action == "signup":
            success, msg = db.signup(user_id, password)
            flash(msg)
            if success:
                return redirect(url_for('/'))  # 가입 후 로그인 페이지로

    return render_template('login.html')

@app.route('/main')
def main():
    if 'user_id' not in session:
        flash("로그인이 필요합니다.")
        return redirect(url_for('/'))
    return render_template('main.html', user_id=session['user_id'])

# 게시물 작성
@app.route('/create', methods=['GET', 'POST'])
def create_post():
    uploaded_image = None
    if 'user_id' not in session:
        flash("로그인이 필요합니다.")
        return redirect(url_for('/'))

    if request.method == 'POST':
        user_id = session['user_id']
        title = request.form.get('title', '').strip()
        song_title = request.form.get('music_title', '').strip()
        artist = request.form.get('music_artist', '').strip()

        # 이미지 업로드
        file = request.files.get('image')
        if file and file.filename:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            uploaded_image = filepath.replace("\\", "/")

        # JS에서 보낸 색상 4개 변수 받기
        colors = [
            request.form.get('color1', ''),
            request.form.get('color2', ''),
            request.form.get('color3', ''),
            request.form.get('color4', '')
        ]

        # DB 저장
        db.save_post(
            user_id=user_id,
            title=title,
            song_title=song_title,
            artist=artist,
            ootd_image_url=uploaded_image,
            color_palette=colors
        )

        flash('게시물이 성공적으로 등록되었습니다!')
        return redirect(url_for('main'))

    return render_template('create_post.html', uploaded_image=uploaded_image)

# Spotify API
def get_spotify_token():
    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()
    url = "https://accounts.spotify.com/api/token"
    headers = {"Authorization": f"Basic {b64_auth_str}"}
    data = {"grant_type": "client_credentials"}
    response = requests.post(url, headers=headers, data=data)
    return response.json().get("access_token")

@app.route("/search_music")
def search_music():
    q = request.args.get("q")
    if not q:
        return {"results": []}

    token = get_spotify_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = "https://api.spotify.com/v1/search"
    params = {"q": q, "type": "track", "limit": 4}

    res = requests.get(url, headers=headers, params=params).json()
    tracks = []
    for t in res.get("tracks", {}).get("items", []):
        tracks.append({
            "title": t["name"],
            "artist": ", ".join(a["name"] for a in t["artists"]),
            "album_img": t["album"]["images"][0]["url"] if t["album"]["images"] else ""
        })
    return {"results": tracks}

if __name__ == "__main__":
    app.run(debug=True)
