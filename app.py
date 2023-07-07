from flask import Flask, render_template, request, session, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room, close_room, rooms, disconnect
from flask_session import Session  # for server-side sessions
import os
import threading
import time
from queue import Queue
from user import User
from bingo_game import BingoGame
from bingo_data import BingoData
from flask_mysqldb import MySQL
from MySQLdb.cursors import DictCursor

app = Flask(__name__)

app.config['SECRET_KEY'] = os.urandom(24)
# MySQL 설정
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'enfj3913'
app.config['MYSQL_DB'] = 'bingo'

SESSION_TYPE = 'filesystem'
app.config.from_object(__name__)
Session(app)

socketio = SocketIO(app, manage_session=False)
mysql = MySQL(app)

client_sessions = {}
bingo_games = {}
GAME_ROOM_CNT = 1

# Matchmaking queue
waiting_queue = []

# 로그인 페이지
@app.route('/')
def index():
    return render_template('login.html')

# 마이페이지
@app.route('/mypage')
def mypage():
    return render_template('mypage.html')

# 대기 페이지
@app.route('/waiting')
def waiting():
    return render_template('waiting.html')

# 게임 페이지
@app.route('/game')
def game():
    return render_template('game.html')

# [GET] /login
# 로그인
@app.route('/login', methods=['POST'])
def loginApi():
    data = request.get_json()

    # json 데이터에서 'nickname'값 가져옴
    nickname = data.get("nickname")
    user_id = None  # 초기화

    # 이미 로그인된 유저인지 확인
    if nickname in client_sessions.keys():
        print(f"already signin user(이미 가입된 유저): {nickname}")
    else:
        # 데이터베이스에서 해당 nickname을 가진 유저 조회
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM user WHERE nickname = %s", (nickname,))
        user_data = cur.fetchone()

        if user_data:
            # 조회된 유저 정보를 사용하여 User 객체 생성 및 등록
            user_id = user_data[0]  # 첫 번째 열(user_id)의 인덱스 0 사용
            user = User(user_id, nickname, user_data[2], user_data[3])
            client_sessions[nickname] = user
            print(f"existing user login success(기존 유저 로그인 성공): {nickname}")
        else:
            # 조회된 유저가 없을 경우 새로운 유저로 등록
            cur.execute("INSERT INTO user (nickname, win, lose) VALUES (%s, %s, %s)", (nickname, 0, 0))
            mysql.connection.commit()
            user_id = cur.lastrowid
            user = User(user_id, nickname, 0, 0)
            client_sessions[nickname] = user
            print(f"new user login success(새로운 유저 로그인 성공): {nickname}")

        cur.close()

    print('current signin user(현재 접속된 유저):')
    for nickname in client_sessions.keys():
        print(f"nickname(유저 ID): {nickname}")
    print('Total number of users:', len(client_sessions))

    # 응답
    response = {'user_id': user_id}  # user_id를 JSON 응답에 포함
    return jsonify(response)



# [GET] /user?nickname=
# 유저정보
@app.route('/user', methods=['GET'])
def userInfo():
    # query string으로부터 데이터 가져옴
    nickname = request.args.get('nickname')

    # 유저를 찾음
    user = find_user(nickname)

    if user:
        # 조회된 유저 정보 반환
        response = {'nickname': user.get_nickname(), 'record': user.get_record()}
        print("find user info(유저정보 발견):", response)
        return jsonify(response)
    else:
        print("fail to find user info(유저정보 발견 실패)")
        error_message = {'error': '유저정보 발견 실패.'}
        return jsonify(error_message), 500


@app.route('/userRead')
def user_read():
    # 데이터베이스 쿼리
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM user')
    results = cur.fetchall()
    cur.close()

    # 결과 출력
    for row in results:
        print(row)

    return 'MySQL 연동 예시'


# [GET] /test
# 테스트 API
@app.route('/test', methods=['GET'])
def test():
    response = {'message': 'TEST 요청 처리 완료'}
    return jsonify(response)

def find_user(nickname):
    # client_sessions에서 해당 nickname 유저 찾기
    if nickname in client_sessions.keys():
        return client_sessions[nickname]

    # 데이터베이스에서 해당 nickname을 가진 유저 조회
    cur = mysql.connection.cursor(cursorclass=DictCursor)
    cur.execute("SELECT * FROM user WHERE nickname = %s", (nickname,))
    user_data = cur.fetchone()
    cur.close()

    if user_data:
        # 조회된 유저 정보를 사용하여 User 객체 생성
        user_id = user_data['user_id']
        win = user_data['win']
        lose = user_data['lose']
        user = User(user_id, nickname, win, lose)
        client_sessions[nickname] = user  # client_sessions에 추가
        return user

    # 유저를 찾지 못한 경우 None 반환
    return None


# -----소켓통신------

@socketio.on('connect', namespace='/')
def on_connect():
    print('Client connected')

@socketio.on('disconnect', namespace='/')
def on_disconnect():
    print('Client disconnected')

@socketio.on("out", namespace='/')
def out():
    print("게임 강제 종료")

# [SOCKET] waiting
# 게임대기
@socketio.on('waiting', namespace='/')
def ready(data):

    nickname = data['nickname']
    print(f"game ready: {nickname}, sid: {request.sid}")

    if nickname not in client_sessions.keys():
        print("fail to find user(유저정보 발견 실패)")
        return

    # 게임대기를 요청한 유저를 대기리스트(큐)에 추가.
    player = client_sessions[nickname]
    if not player.get_is_waiting():
        player.set_is_waiting(True)
        waiting_queue.append(player)

    # 큐에 2명 이상이 들어가면 게임 생성.
    if len(waiting_queue) >= BingoData.MIN_PLAYER_SIZE:
        bingo_game = create_game_room()
        send_match_player_info(bingo_game)


def create_game_room():
    #게임방 만들어야함.
    global GAME_ROOM_CNT
    bingo_game = BingoGame(GAME_ROOM_CNT)

    for i in range(BingoData.MIN_PLAYER_SIZE):
        player = waiting_queue[i]
        bingo_game.add_player(player)

    bingo_game.generate_players_bingo_card()
    bingo_games[GAME_ROOM_CNT] = bingo_game

    GAME_ROOM_CNT += 1

    return bingo_game

def send_match_player_info(bingo_game):
    # 상대 플레이어 정보 전달.
    leader = True # -> 먼저 들어온 사람이 방장이 되어, 게임시작 권한을 갖게됨.
    for player in bingo_game.get_players().values():
        for opp in bingo_game.get_players().values():
            if opp != player:
                response_data = {"leader": leader, "game_room_num": bingo_game.get_game_room_num(), "opp_nickname": opp.get_nickname(), "opp_record": opp.get_record()}
                emit('readyGame', response_data, room=player.get_sid())
                # print(f"send to a-sid: {player_a.get_sid()}")
        leader = False


# [SOCKET] startGame
# 유저의 게임 시작 요청
@socketio.on('startGame', namespace='/')
def start_game(data):

    game_room_num = data["game_room_num"]
    bingo_game = bingo_games[game_room_num]
    
    # 모든 플레이어를 게임페이지로 이동시키기
    for player in bingo_game.get_players().values():
        waiting_queue.pop(0)
        player.set_is_waiting(False)
        emit("moveGamePage", room=player.get_sid())

# [SOCKET] resetSID
# 유저의 sid 다시 설정
@socketio.on("resetSID", namespace='/')
def reset_sid(data):
    nickname = data["nickname"]
    user = find_user(nickname)  # 유저를 find_user() 메소드로 찾음

    if user:
        user.set_sid(request.sid)
        print(f"Reset SID for user: {nickname}, SID: {request.sid}")
    else:
        print(f"User not found: {nickname}")


# [SOCKET] enterGameRoom
# 플레이어가 게임방에 들어왔음을 알림
@socketio.on("enterGameRoom", namespace='/')
def enter_game_room(data):
    game_room_num = data["gameRoomNum"]
    bingo_game = bingo_games[game_room_num]

    nickname = data["nickname"]
    player = find_user(nickname)  # 유저를 find_user() 메소드로 찾음

    if player:
        bingo_game.player_ready()

        # 플레이어 정보, 상대방 정보, 내 빙고판 정보 넘겨주기.
        response_data = {
            "player": bingo_game.get_my_info(player),
            "opp_player": bingo_game.get_opp_info(player),
            "bingo_card": bingo_game.get_my_bingo_card(player)
        }
        emit("bingoGameInfo", response_data, room=request.sid)

        print(bingo_game.get_my_bingo_card(nickname))

        # 다 게임방에 들어왔으면 게임 시작하기.
        if bingo_game.is_every_player_ready():
            bingo_game.start_game()
    else:
        print(f"User not found: {nickname}")



# 빙고 버튼 클릭.
# 빙고가 맞으면 게임 끝
# 아니면 계속 게임하기.
@socketio.on("bingo", namespace='/')
def bingo(data):
    print("player click bingo button!!")

    game_room_num = data["gameRoomNum"]
    bingo_game = bingo_games[game_room_num]

    nickname = data["nickname"]
    player = find_user(nickname)  # 유저를 find_user() 메소드로 찾음

    if player:
        result = bingo_game.check_bingo(player)

        response_data = {"result": result}
        emit("bingoGameResult", response_data, room=player.get_sid())
    else:
        print(f"User not found: {nickname}")



if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)