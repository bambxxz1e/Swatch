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
app.secret_key = SECRET_KEY # 세션 암호화 용도
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True) # 업로드 폴더 자동 생성

db = DBManager()

# 로그인 / 회원가입 페이지
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == "POST":
        user_id = request.form['user_id']
        password = request.form['password']
        action = request.form.get('action') # login 또는 signup 선택

        if action == "login":
            if db.login(user_id, password):
                session['user_id'] = user_id # 세션 저장
                flash(f"{user_id}님, 환영합니다!")
                return redirect(url_for('main'))
            else:
                flash("아이디 또는 비밀번호가 틀렸습니다.")

        elif action == "signup":
            success, msg = db.signup(user_id, password)
            flash(msg)
            if success:
                return redirect(url_for('/'))  # 가입 성공 시 로그인 페이지로

    return render_template('login.html')

# 메인 페이지 (게시글 목록)
@app.route('/main')
def main():
    user_id = session.get('user_id')

    # 로그인 되어 있지 않으면 로그인 페이지로 이동
    if not user_id:
        flash("로그인이 필요합니다.")
        return redirect(url_for('index'))

    try:
        posts = db.get_all_posts(user_id=user_id)
        print(f"[DEBUG] 가져온 게시물 수: {len(posts)}")
    except Exception as e:
        print("[ERROR] main() DB 조회 실패:", e)
        posts = []

    return render_template('main.html', posts=posts, user_id=user_id)

# 게시물 작성 페이지
@app.route('/create', methods=['GET', 'POST'])
def create_post():
    uploaded_image = None

    if 'user_id' not in session:
        flash("로그인이 필요합니다.")
        return redirect(url_for('index'))

    # POST 요청이면 게시물 저장 처리
    if request.method == 'POST':
        try:
            user_id = session['user_id']
            title = request.form.get('title', '').strip()
            song_title = request.form.get('music_title', '').strip()
            artist = request.form.get('music_artist', '').strip()

            print(f"[DEBUG] user_id: {user_id}, title: {title}, song: {song_title}, artist: {artist}")

            # 이미지 업로드
            file = request.files.get('image')
            if file and file.filename:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                uploaded_image = filepath.replace("\\", "/")
                print(f"[DEBUG] 이미지 업로드 성공: {uploaded_image}")
            else:
                print("[DEBUG] 업로드할 이미지 없음")

            # 색상 팔레트 값 4개 받기
            colors = [
                request.form.get('color1', ''),
                request.form.get('color2', ''),
                request.form.get('color3', ''),
                request.form.get('color4', '')
            ]
            print(f"[DEBUG] 색상 팔레트: {colors}")

            # DB 저장
            db.connect()
            db.save_post(
                user_id=user_id,
                title=title,
                song_title=song_title,
                artist=artist,
                ootd_image_url=uploaded_image,
                color_palette=colors
            )
            db.close()
            print("[DEBUG] 게시물 저장 성공!")

            flash('게시물이 성공적으로 등록되었습니다!')
            return redirect(url_for('main'))

        except Exception as e:
            print("[ERROR] 게시물 저장 실패:", e)
            flash(f"게시물 저장 중 오류 발생: {e}")

    return render_template('create_post.html', uploaded_image=uploaded_image)

# 게시물 삭제
@app.route('/delete_post/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    if 'user_id' not in session:
        return {"success": False, "msg": "로그인이 필요합니다."}

    try:
        db.delete_post(post_id, session['user_id'])
        return {"success": True}
    except Exception as e:
        print("삭제 실패:", e)
        return {"success": False}

# Spotify API 인증
def get_spotify_token():
    # client_id:client_secret을 base64(데이터를 텍스트 문자열로)로 인코딩
    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()

    url = "https://accounts.spotify.com/api/token"
    headers = {"Authorization": f"Basic {b64_auth_str}"}
    data = {"grant_type": "client_credentials"}

    # Spotify 서버에서 access token 요청
    response = requests.post(url, headers=headers, data=data)
    return response.json().get("access_token")

@app.route("/search_music")
def search_music():
    q = request.args.get("q") # 검색어
    if not q:
        return {"results": []}

    token = get_spotify_token()
    headers = {"Authorization": f"Bearer {token}"}

    url = "https://api.spotify.com/v1/search"
    params = {"q": q, "type": "track", "limit": 4} # 4개씩 가져오기

    # Spotify 검색 요청
    res = requests.get(url, headers=headers, params=params).json()
    tracks = []

    # 필요한 정보(곡 제목, 가수, 앨범 커버)만 추출
    for t in res.get("tracks", {}).get("items", []):
        tracks.append({
            "title": t["name"],
            "artist": ", ".join(a["name"] for a in t["artists"]),
            "album_img": t["album"]["images"][0]["url"] if t["album"]["images"] else ""
        })
    return {"results": tracks}

# 서버 실행
if __name__ == "__main__":
    app.run(debug=True)
