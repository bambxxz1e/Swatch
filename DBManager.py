import pymysql
from dotenv import load_dotenv
import os
import json

load_dotenv()
DB_KEY = os.environ.get('DB_KEY')

class DBManager:
    def __init__(self):
        self.conn = None

    # DB 연결
    def connect(self):
        try:
            self.conn = pymysql.connect(
                host='localhost',
                user='root',
                password=DB_KEY,
                db='swatch',
                charset='utf8mb4',
                cursorclass = pymysql.cursors.DictCursor # 결과를 딕셔너리 형태로 변환(원래는 튜플)
            )
            return self.conn
        except pymysql.MySQLError as e:
            print("MySQL 연결 실패:", e)
            return None

    # DB 연결 종료
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
        
        # 새 사용자 저장
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
        
        # 아이디 비번 일치 확인
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
                
                # 컬러 팔레트 리스트를 JSON 문자열로 변환
                color_json = json.dumps(color_palette)

                cursor.execute(sql, (user_id, title, song_title, artist, ootd_image_url, color_json))

            self.conn.commit()
        except Exception as e:
            print("레코드 저장 실패:", e)

    # 모든 게시물 가져오기
    def get_all_posts(self, user_id=None, limit=None):
        conn = self.connect()
        if not conn:
            return []

        try:
            with conn.cursor() as cursor:
                sql = """
                    SELECT record_id, user_id, title, song_title, artist, ootd_image_url, color_palette, created_at
                    FROM records
                """
                params = []

                if user_id:  # 로그인한 계정만 가져오기
                    sql += " WHERE user_id=%s"
                    params.append(user_id)

                # 최신순 정렬
                sql += " ORDER BY created_at DESC"

                # 가져올 게시물 개수 제한
                if limit:
                    sql += " LIMIT %s"
                    params.append(limit)

                cursor.execute(sql, tuple(params))
                posts = cursor.fetchall()

                # color_palette JSON을 다시 리스트로 반환
                for post in posts:
                    if post['color_palette']:
                        post['color_palette'] = json.loads(post['color_palette'])

                return posts

        except Exception as e:
            print("게시물 조회 실패:", e)
            return []
        finally:
            if conn:
                conn.close()

    # 선택 게시물 삭제하기
    def delete_post(self, post_id, user_id):
        conn = self.connect()
        if not conn:
            print("DB 연결 실패")
            return

        try:
            with conn.cursor() as cursor:
                # record_id와 user_id 둘 다 일치할 때만 삭제
                sql = "DELETE FROM records WHERE record_id=%s AND user_id=%s"
                cursor.execute(sql, (post_id, user_id))

            conn.commit()
            print(f"DB 삭제 완료: {post_id}")

        except Exception as e:
            print("게시물 삭제 실패:", e)
        finally:
            conn.close()