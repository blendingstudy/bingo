import pymysql.cursors
from bingo_data import BingoData
import random

class BingoDao:

    def __init__(self):
        # Connect to the database
        self.connection = pymysql.connect(host=BingoData.MYSQL_HOST,
                                    user=BingoData.MYSQL_USER,
                                    password=BingoData.MYSQL_PW,
                                    db=BingoData.MYSQL_DB,
                                    charset='utf8mb4',
                                    cursorclass=pymysql.cursors.DictCursor,
                                    autocommit=True)

    #---------유저----------#

    # 회원가입
    def save_user(self, nickname, password, referral):
        # 프로필 이미지 설정
        random_number = random.randint(0, len(BingoData.PROFILE_IMG_LIST)-1)
        random_profile_img = BingoData.PROFILE_IMG_LIST[random_number]

        # 회원가입
        with self.connection.cursor() as cursor:
            cursor.execute("INSERT INTO user (nickname, password, referral, profile_img) VALUES (%s, %s, %s, %s)", (nickname, password, referral, random_profile_img, ))
            self.connection.commit()

        user_id = cursor.lastrowid

        return self.find_user_by_id(user_id)

    # 로그인
    def login(self, nickname, password):
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT * FROM user WHERE nickname = %s and password = %s", (nickname, password, ))
        
        user = cursor.fetchone()
        return user

    # id로 유저 조회
    def find_user_by_id(self, id):
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT * FROM user WHERE user_id = %s", (id, ))
        
        user = cursor.fetchone()
        return user
    
    # 닉네임으로 유저 조회
    def find_user_by_nickname(self, nickname):
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT * FROM user WHERE nickname = %s", (nickname, ))
        
        user = cursor.fetchone()
        return user
    
    #---------유저 끝----------#

    #---------게임----------#

    # 게임방 리스트 조회
    def find_game_room_list(self):
        with self.connection.cursor() as cursor:
            cursor.execute("select * from bingo_game_room")
        
        bingo_game_room_list = cursor.fetchall()
        return bingo_game_room_list

    # 게임 참여자 조회
    def fing_game_member_list(self, game_room_id):
        with self.connection.cursor() as cursor:
            cursor.execute("select player_id, sid, nickname, profile_img from game_member member join user  on user_id = player_id where bingo_game_room_id = %s", (game_room_id, ))
        
        game_member_list = cursor.fetchall()
        return game_member_list

    # 게임방 생성 + 플레이어까지 저장
    def save_game_room(self, players):
        status = "WAITING"
        with self.connection.cursor() as cursor:
            # 게임방 저장
            cursor.execute("INSERT INTO bingo_game_room (status) VALUES (%s)", (status,))
            self.connection.commit()
            
            game_room_id = cursor.lastrowid

            # 게임 플레이어 저장
            for player in players.values():
                cursor.execute("INSERT INTO game_member (bingo_game_room_id, player_id) VALUES (%s, %s)", (game_room_id, player.get_id()))
            self.connection.commit()

        return game_room_id

    # 게임방 생성
    def save_game_room_ver2(self):
        status = "WAITING"
        with self.connection.cursor() as cursor:
            # 게임방 저장
            cursor.execute("INSERT INTO bingo_game_room (status) VALUES (%s)", (status,))
            self.connection.commit()
            
            game_room_id = cursor.lastrowid

        return game_room_id


    # 게임 종료
    def game_over(self, game_room_num):
        with self.connection.cursor() as cursor:
            sql_query = "UPDATE bingo_game_room SET status='GAMEOVER' WHERE bingo_game_room_id = %s"
            values = (game_room_num, )
            cursor.execute(sql_query, values)
            self.connection.commit()