import pymysql
from dotenv import load_dotenv
import os
import json

load_dotenv()
DB_KEY = os.environ.get('DB_KEY')

class DBManager:
    def __init__(self):
        self.conn = None

    def connect(self):
        try:
            self.conn = pymysql.connect(
                host='localhost',
                user='root',
                password=DB_KEY,
                db='swatch',
                charset='utf8mb4',
                cursorclass = pymysql.cursors.DictCursor
            )
            return self.conn
        except pymysql.MySQLError as e:
            print("MySQL 연결 실패:", e)
            return None

    def close(self):
        if self.conn:
            self.conn.close()

    # 회원가입
    def signup(self, user_id, password):
        conn = self.connect()
        if not conn:
            return False, "DB 연결 실패"
        cur = conn.cursor()
        # 중복 체크
        cur.execute("SELECT * FROM users WHERE user_id=%s", (user_id,))
        if cur.fetchone():
            conn.close()
            return False, "이미 존재하는 아이디입니다."
        # 저장
        cur.execute("INSERT INTO users (user_id, password) VALUES (%s, %s)", (user_id, password))
        conn.commit()
        conn.close()
        return True, "회원가입 완료!"

    # 로그인
    def login(self, user_id, password):
        conn = self.connect()
        if not conn:
            return False
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE user_id=%s AND password=%s", (user_id, password))
        user = cur.fetchone()
        conn.close()
        return bool(user)

    # 게시물 저장
    def save_post(self, user_id, title=None, song_title=None, artist=None, ootd_image_url=None, color_palette=[]):
        if not self.conn:
            self.connect()
        try:
            with self.conn.cursor() as cursor:
                sql = """
                    INSERT INTO records (user_id, title, song_title, artist, ootd_image_url, color_palette, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW())
                """
                # JSON으로 변환
                color_json = json.dumps(color_palette)
                cursor.execute(sql, (user_id, title, song_title, artist, ootd_image_url, color_json))
            self.conn.commit()
        except Exception as e:
            print("레코드 저장 실패:", e)

    # 모든 게시물 가져오기
    def get_all_posts(self, limit=None):
        try:
            conn = self.connect()
            if not conn:
                return []

            with conn.cursor() as cursor:
                if limit:
                    sql = """
                        SELECT user_id, title, song_title, artist, ootd_image_url, color_palette, created_at
                        FROM records
                        ORDER BY created_at DESC
                        LIMIT %s
                    """
                    cursor.execute(sql, (limit,))
                else:
                    sql = """
                        SELECT user_id, title, song_title, artist, ootd_image_url, color_palette, created_at
                        FROM records
                        ORDER BY created_at DESC
                    """
                    cursor.execute(sql)

                posts = cursor.fetchall()

                # JSON 문자열을 파이썬 객체로 변환
                for post in posts:
                    if post['color_palette']:
                        post['color_palette'] = json.loads(post['color_palette'])

            return posts

        except Exception as e:
            print("게시물 조회 실패:", e)
            return []

        finally:
            if conn:
                conn.close()  # 사용 후 항상 닫기
