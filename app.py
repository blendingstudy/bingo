from flask import Flask, render_template, request, session, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room, close_room, rooms, disconnect
from flask_session import Session  # for server-side sessions
import os
import threading
import time
from queue import Queue
from user import User

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
SESSION_TYPE = 'filesystem'
app.config.from_object(__name__)
Session(app)

socketio = SocketIO(app, manage_session=False)

client_sessions = {}
bingo_game = None

# Matchmaking queue
queue = Queue()

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/mypage')
def mypage():
    return render_template('mypage.html')

@app.route('/waiting')
def waiting():
    return render_template('waiting.html')

@app.route('/game')
def game():
    return render_template('game.html')

# 로그인
@app.route('/login', methods=['POST'])
def loginApi():
    data = request.get_json()

    nickname = data.get("username")
    print(f"로그인 시도: {nickname} - 세션id: {session.sid}")

    if nickname in client_sessions.keys():
        print(f"이미 로그인된 유저: {nickname}")
    else:
        client_sessions[nickname] = User(nickname)
        # emit('loginResponse', {'success': True})
        print(f"로그인 성공: {nickname}")

    print('현재 접속된 유저:')
    for nickname in client_sessions.keys():
        print(f"유저 ID: {nickname}")
        # print(f"Session ID: {sid}, Nickname: {session.get('nickname')}")
    print('Total number of users:', len(client_sessions))

    response = {'message': 'POST 로그인 요청 처리 완료'}
    return jsonify(response)

# 유저정보
@app.route('/user', methods=['GET'])
def userInfo():
    nickname = request.args.get('nickname')

    print(f"유저정보 요청 시도: {nickname}")

    if nickname in client_sessions.keys():
        userInfo = client_sessions[nickname]
        print("유저정보 발견:", userInfo)
        response = {'nickname': userInfo.get_nickname(), 'record': userInfo.get_record()}
        return jsonify(response)
    else:
        print("유저정보 발견 실패")
        error_message = {'error': '유저정보 발견 실패.'}
        return jsonify(error_message), 500


@app.route('/test', methods=['GET'])
def test():
    response = {'message': 'TEST 요청 처리 완료'}
    return jsonify(response)


# -----소켓통신------

@socketio.on('connect', namespace='/')
def on_connect():
    # Add a ready state to the client's session when they connect
    # client_sessions[request.sid] = {'ready': False}
    print('Client connected')

@socketio.on('disconnect', namespace='/')
def on_disconnect():
    # Remove the disconnected client's session and record
    # if request.sid in client_sessions:
    #     del client_sessions[request.sid]
    print('Client disconnected')

# 게임방-준비
@socketio.on('ready', namespace='/')
def ready(data):

    nickname = data['nickname']
    print(f"game ready: {nickname}, sid: {request.sid}")

    if nickname not in client_sessions.keys():
        print("유저정보 발견 실패")
        error_message = {'error': '유저정보 발견 실패.'}
        return jsonify(error_message), 500

    player = client_sessions[nickname]
    player.set_session_id(request.sid)

    queue.put(player)

    if queue.qsize() >= 2:
        start_game()

    # print(queue)

def start_game():
    #플레이어 a 정보 꺼냄
    player_a = queue.get()
    #플레이어 b 정보 꺼냄
    player_b = queue.get()

    #플레이어 a에겐 b 정보 건내줌
    response_data = {"reader": True, "opp_nickname": player_b.get_nickname(), "opp_record": player_b.get_record()}
    emit('startGame', response_data, room=player_a.get_session_id())
    print(f"send to a-sid: {player_a.get_session_id()}")
    #플레이어 b에겐 a 정보 건내줌
    response_data = {"reader": False, "opp_nickname": player_a.get_nickname(), "opp_record": player_a.get_record()}
    emit('startGame', response_data, room=player_b.get_session_id())
    print(f"send to b-sid: {player_b.get_session_id()}")

    #게임 시작해야함


@socketio.on('gameOver', namespace='/')
def on_game_over(data):
    # Update the player's game record based on the game result
    if data['isUserVictory']:
        client_sessions[request.sid]['record']['win'] += 1
    else:
        client_sessions[request.sid]['record']['lose'] += 1

    # Notify the client to update the displayed record
    emit('fetchRecordResponse', {'record': client_sessions[request.sid]['record']})


if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)

# @socketio.on('ready', namespace='/')
# def on_ready():
#     # Mark the user as ready when they emit the 'ready' event
#     client_sessions[request.sid]['ready'] = True
#     # Check if the user's matched opponent is ready
#     # If they are, start the game
#     # Otherwise, wait until they are ready
#     emit('startGame', room=request.sid)


# @socketio.on('login', namespace='/')
# def on_login(data):
#     nickname = data['nickname']

#     print(f"Trying to login with nickname: {nickname}")
#     # Check if nickname is already in use
#     if any(session.get('nickname') == nickname for session in client_sessions.values()):
#         print(f"Nickname {nickname} is already in use")
#         emit('loginResponse', {'success': False})
#     else:
#         # Store the nickname and initial game record in the client's session
#         client_sessions[request.sid] = {
#             'nickname': nickname,
#             'record': {'win': 0, 'lose': 0}
#         }
#         emit('loginResponse', {'success': True})
#         print(f"Logged in with nickname: {nickname}")
    
#     # After the user has logged in, print the current number of users and their nicknames
#     print('Current users:')
#     for sid, session in client_sessions.items():
#         print(f"Session ID: {sid}, value: {session}")
#         # print(f"Session ID: {sid}, Nickname: {session.get('nickname')}")
#     print('Total number of users:', len(client_sessions))


# @socketio.on('fetchNickname', namespace='/')
# def on_fetch_nickname(data):
#     nickname = data['nickname']
#     print("닉네임 찾기:", nickname)
#     for sid, session in client_sessions.items():
#         print("닉네임 찾는중:", session.get('nickname'))
#         if session.get('nickname') == nickname:
#             print("닉네임 발견:", session.get('nickname'))
#             emit('fetchNicknameResponse', {'nickname': session.get('nickname')})
#             break

# @socketio.on('fetchRecord', namespace='/')
# def on_fetch_record(data):
#     nickname = data['nickname']
#     for sid, session in client_sessions.items():
#         if session.get('nickname') == nickname:
#             emit('fetchRecordResponse', {'record': session.get('record')})
#             break

# @socketio.on('joinQueue', namespace='/')
# def on_join_queue():
#     if queue:
#         # Match found
#         opponent_sid = queue.popleft()
#         opponent_nickname = client_sessions[opponent_sid]['nickname']
#         opponent_record = client_sessions[opponent_sid]['record']

#         emit('matchFound', {
#             'nickname': opponent_nickname,
#             'record': opponent_record
#         }, room=request.sid)

#         emit('matchFound', {
#             'nickname': client_sessions[request.sid]['nickname'],
#             'record': client_sessions[request.sid]['record']
#         }, room=opponent_sid)
#     else:
#         queue.append(request.sid)

# @socketio.on('leaveQueue', namespace='/')
# def on_leave_queue():
#     if request.sid in queue:
#         queue.remove(request.sid)



# @socketio.on('notReady', namespace='/')
# def on_not_ready():
#     # Mark the user as not ready
#     client_sessions[request.sid]['ready'] = False
#     # Remove the user from the match and put them back into the queue
#     queue.append(request.sid)