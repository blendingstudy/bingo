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
game_room_cnt = 1

# Matchmaking queue
waiting_queue = Queue()

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
    nickname = data.get("username")
    print(f"로그인 시도: {nickname} - 세션id: {session.sid}")

    # 이미 로그인된 유저인지 확인
    if nickname in client_sessions.keys():
        print(f"이미 로그인된 유저: {nickname}")
    else: 
        # 새로운 유저면, 등록
        client_sessions[nickname] = User(nickname)
        print(f"로그인 성공: {nickname}")

    print('현재 접속된 유저:')
    for nickname in client_sessions.keys():
        print(f"유저 ID: {nickname}")
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

    print(f"유저정보 요청 시도: {nickname}")

    # 등록된 유저이면, 해당 유저정보 반환
    if nickname in client_sessions.keys():
        userInfo = client_sessions[nickname]
        print("유저정보 발견:", userInfo)
        response = {'nickname': userInfo.get_nickname(), 'record': userInfo.get_record()}
        return jsonify(response)
    else:
        print("유저정보 발견 실패")
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

# [SOCKET] ready
# 게임대기
@socketio.on('waiting', namespace='/')
def ready(data):

    nickname = data['nickname']
    print(f"game ready: {nickname}, sid: {request.sid}")

    if nickname not in client_sessions.keys():
        print("유저정보 발견 실패")
        error_message = {'error': '유저정보 발견 실패.'}
        return jsonify(error_message), 500

    # 게임대기를 요청한 유저를 대기리스트(큐)에 추가.
    player = client_sessions[nickname]
    player.set_session_id(request.sid)
    waiting_queue.put(player)

    # 큐에 2명 이상이 들어가면 게임 생성.
    if waiting_queue.qsize() >= 2:
        create_game_room()


def create_game_room():
    #플레이어 a 정보 꺼냄 -> 먼저 들어온 사람이 방장이 되어, 게임시작 권한을 갖게됨.
    player_a = waiting_queue.get()
    #플레이어 b 정보 꺼냄
    player_b = waiting_queue.get()

    #게임방 만들어야함.
    global game_room_cnt
    bingo_game = BingoGame(game_room_cnt)
    bingo_game.add_player(player_a)
    bingo_game.add_player(player_b)

    bingo_games[game_room_cnt] = bingo_game

    game_room_cnt += 1

    #플레이어 a에겐 b 정보 건내줌
    response_data = {"reader": True, "game_room_num": bingo_game.get_game_room_num(), "opp_nickname": player_b.get_nickname(), "opp_record": player_b.get_record()}
    emit('readyGame', response_data, room=player_a.get_session_id())
    print(f"send to a-sid: {player_a.get_session_id()}")
    #플레이어 b에겐 a 정보 건내줌
    response_data = {"reader": False, "game_room_num": bingo_game.get_game_room_num(), "opp_nickname": player_a.get_nickname(), "opp_record": player_a.get_record()}
    emit('readyGame', response_data, room=player_b.get_session_id())
    print(f"send to b-sid: {player_b.get_session_id()}")


# [SOCKET] startGame
# 유저의 게임 시작 요청
@socketio.on('startGame', namespace='/')
def start_game(data):

    game_room_num = data["game_room_num"]
    bingo_game = bingo_games[game_room_num]
    print(f"----bingoGame! {bingo_game}")
    
    for user in bingo_game.get_players().values():
        print("게임방으로 페이지 이동 요청")
        emit("moveGamePage", room=user.get_session_id())

# [SOCKET] resetSID
# 유저의 sid 다시 설정
@socketio.on("resetSID", namespace='/')
def reset_sid(data):

    nickname = data["nickname"]
    if nickname in client_sessions.keys():
        userInfo = client_sessions[nickname]
        userInfo.set_session_id(request.sid)
        print("sid 바꿈")

# [SOCKET] enterGameRoom
# 플레이어가 게임방에 들어왔음을 알림
@socketio.on("enterGameRoom", namespace='/')
def enter_game_room(data):

    # print("플레이어 들어옴", data)

    game_room_num = data["gameRoomNum"]

    print("게임방 번호", game_room_num, type(game_room_num))
    print(bingo_games.keys())
    bingo_game = bingo_games[game_room_num]

    bingo_game.player_ready()

    # 플레이어 정보, 상대방 정보, 내 빙고판 정보 넘겨주기.
    nickname = data["nickname"]
    response_data = {
        "player" : bingo_game.get_my_info(nickname),
        "opp_player" : bingo_game.get_opp_info(nickname),
        # "bingo_card" : bingo_game.get_my_bingo_card(nickname)
    }
    emit("bingoGameInfo", response_data, room=request.sid)

    print(bingo_game.get_my_bingo_card(nickname))

    # 다 게임방에 들어왔으면 게임 시작하기.



if __name__ == '__main__':
    socketio.run(app, debug=True)