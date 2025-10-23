import pymysql
from dotenv import load_dotenv
import os

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
                charset='utf8mb4'
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
