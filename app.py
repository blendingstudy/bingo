from flask import Flask, render_template, request, session, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room, close_room, rooms, disconnect
from flask_session import Session  # for server-side sessions
import os
import threading
import time
from queue import Queue
from user import User
from bingo_game import BingoGame

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
SESSION_TYPE = 'filesystem'
app.config.from_object(__name__)
Session(app)

socketio = SocketIO(app, manage_session=False)

client_sessions = {}
bingo_games = {}
GAME_ROOM_CNT = 1
MIN_PLAYER_SIZE = 2

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

    # json 데이터에서 'username'값 가져옴
    nickname = data.get("nickname")

    # 이미 로그인된 유저인지 확인
    if nickname in client_sessions.keys():
        print(f"already signin user(이미 가입된 유저): {nickname}")
    else: 
        # 새로운 유저면, 등록
        client_sessions[nickname] = User(nickname)
        print(f"new user login success(로그인 성공): {nickname}")

    print('current signin user(현재 접속된 유저):')
    for nickname in client_sessions.keys():
        print(f"nickname(유저 ID): {nickname}")
    print('Total number of users:', len(client_sessions))

    # 응답
    response = {'message': 'POST 로그인 요청 처리 완료'}
    return jsonify(response)

# [GET] /user?nickname=
# 유저정보
@app.route('/user', methods=['GET'])
def userInfo():
    # query string으로부터 데이터 가져옴
    nickname = request.args.get('nickname')

    # 등록된 유저이면, 해당 유저정보 반환
    if nickname in client_sessions.keys():
        user = client_sessions[nickname]
        print("find user info(유저정보 발견):", user)
        response = {'nickname': user.get_nickname(), 'record': user.get_record()}
        return jsonify(response)
    else:
        print("fail to find user info(유저정보 발견 실패)")
        error_message = {'error': '유저정보 발견 실패.'}
        return jsonify(error_message), 500


# [GET] /test
# 테스트 API
@app.route('/test', methods=['GET'])
def test():
    response = {'message': 'TEST 요청 처리 완료'}
    return jsonify(response)


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
    global MIN_PLAYER_SIZE
    if len(waiting_queue) >= MIN_PLAYER_SIZE:
        create_game_room()


def create_game_room():

    #게임방 만들어야함.
    global GAME_ROOM_CNT
    bingo_game = BingoGame(GAME_ROOM_CNT)

    global MIN_PLAYER_SIZE
    for i in range(MIN_PLAYER_SIZE):
        player = waiting_queue[i]
        bingo_game.add_player(player)

    bingo_game.generate_players_bingo_card()
    bingo_games[GAME_ROOM_CNT] = bingo_game

    GAME_ROOM_CNT += 1

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
    if nickname in client_sessions.keys():
        user = client_sessions[nickname]
        user.set_sid(request.sid)

# [SOCKET] enterGameRoom
# 플레이어가 게임방에 들어왔음을 알림
@socketio.on("enterGameRoom", namespace='/')
def enter_game_room(data):

    game_room_num = data["gameRoomNum"]
    bingo_game = bingo_games[game_room_num]

    bingo_game.player_ready()

    # 플레이어 정보, 상대방 정보, 내 빙고판 정보 넘겨주기.
    nickname = data["nickname"]
    response_data = {
        "player" : bingo_game.get_my_info(nickname),
        "opp_player" : bingo_game.get_opp_info(nickname),
        "bingo_card" : bingo_game.get_my_bingo_card(nickname)
    }
    emit("bingoGameInfo", response_data, room=request.sid)

    print(bingo_game.get_my_bingo_card(nickname))

    # 다 게임방에 들어왔으면 게임 시작하기.
    if bingo_game.is_every_player_ready():
        bingo_game.start_game()


# 빙고 버튼 클릭.
# 빙고가 맞으면 게임 끝
# 아니면 계속 게임하기.
@socketio.on("bingo", namespace='/')
def bingo(data):
    print("player click bingo button!!")

    game_room_num = data["gameRoomNum"]
    bingo_game = bingo_games[game_room_num]

    nickname = data["nickname"]
    if nickname in client_sessions.keys():
        result = bingo_game.check_bingo(nickname)

        player = client_sessions[nickname]
        response_data = {"result":result}
        emit("bingoGameResult", response_data, room=player.get_sid())


if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)