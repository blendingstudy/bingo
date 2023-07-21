from flask import Flask, render_template, request, session, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room, close_room, rooms, disconnect
from flask_session import Session  # for server-side sessions
import os
from queue import Queue
from user import User
from bingo_game import BingoGame
from bingo_data import BingoData
import pymysql.cursors
from game_match import GameMatch

app = Flask(__name__)

app.config['SECRET_KEY'] = os.urandom(24)

SESSION_TYPE = 'filesystem'
app.config.from_object(__name__)
Session(app)

socketio = SocketIO(app, manage_session=False)

# Connect to the database
connection = pymysql.connect(host=BingoData.MYSQL_HOST,
                             user=BingoData.MYSQL_USER,
                             password=BingoData.MYSQL_PW,
                             db=BingoData.MYSQL_DB,
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)

client_sessions = {}
bingo_games = {}
game_matchs = {}
GAME_MATCH_CNT = 1

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

    # json 데이터에서 'nickname'값 가져옴
    nickname = data.get("nickname")
    user_id = None  # 초기화

    # 이미 로그인된 유저인지 확인
    if nickname in client_sessions.keys():
        print(f"already signin user(이미 가입된 유저): {nickname}")
    else:
        # 데이터베이스에서 해당 nickname을 가진 유저 조회
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM user WHERE nickname = %s", (nickname,))
            user_data = cursor.fetchone()

        print(user_data)
        if user_data:
            # 조회된 유저 정보를 사용하여 User 객체 생성 및 등록
            user_id = user_data["user_id"]  # 첫 번째 열(user_id)의 인덱스 0 사용
            user = User(user_id, nickname, user_data["win"], user_data["lose"])
            client_sessions[nickname] = user
            print(f"existing user login success(기존 유저 로그인 성공): {nickname}")
        else:
            # 조회된 유저가 없을 경우 새로운 유저로 등록
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO user (nickname, win, lose) VALUES (%s, %s, %s)", (nickname, 0, 0,))
                connection.commit()
                user_id = cursor.lastrowid
                user = User(user_id, nickname, 0, 0)
                client_sessions[nickname] = user
                print(f"new user login success(새로운 유저 로그인 성공): {nickname}")


        cursor.close()

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
    with connection.cursor() as cursor:
        cursor.execute('SELECT * FROM user')
        results = cursor.fetchall()

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
    with connection.cursor() as cursor:
            sql_query = "SELECT * FROM user WHERE nickname = %s"
            cursor.execute(sql_query, (nickname,))
            user_data = cursor.fetchone()

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
    waiting_queue.put(player)
    matching_player()


def matching_player():
    global GAME_MATCH_CNT
    player = waiting_queue.get()

    if GAME_MATCH_CNT-1 in game_matchs.keys():
        prev_game_match = game_matchs[GAME_MATCH_CNT-1]
        if prev_game_match.num_of_wating_player() < BingoData.MAX_PLAYER_SIZE and not prev_game_match.is_match_complete():
            print("prev_matcing add player!!!!!")
            prev_game_match.add_player(player)
            send_match_player_info(player, prev_game_match)
            return

    print("new matching !!!!!")
    game_match = GameMatch(GAME_MATCH_CNT)
    game_match.add_player(player)
    game_matchs[GAME_MATCH_CNT] = game_match

    GAME_MATCH_CNT += 1


def send_match_player_info(player, game_match):
    # 새로운 플레이어의 정보 전달
    for opp in game_match.get_players().values():
        if opp != player:
            response_data = {"leader": game_match.get_leader() == opp, "game_match_num": game_match.get_id(), "opp_nickname": player.get_nickname(), "opp_record": player.get_record(), "idx": game_match.num_of_wating_player()}
            emit('newPlayerMatched', response_data, room=opp.get_sid())
    
    # 새로운 플레이어에게 이전 매칭된 플레이어 정보 전달
    for opp in game_match.get_players().values():
        if opp != player:
            response_data = {"leader": game_match.get_leader() == player, "game_match_num": game_match.get_id(), "opp_nickname": opp.get_nickname(), "opp_record": opp.get_record()}
            emit('gameMatchComplete', response_data, room=player.get_sid())
            # print(f"send to a-sid: {player_a.get_sid()}")


# [SOCKET] startGame
# 유저의 게임 시작 요청
@socketio.on('startGame', namespace='/')
def start_game(data):

    game_match_num = data["game_match_num"]
    game_match = game_matchs[game_match_num]

    game_match.game_start()

    # 여기서 게임 만들기.
    bingo_game = create_game_room(game_match)

    response_data = {"gameRoomNum" : bingo_game.get_game_room_num()}
    
    # 모든 플레이어를 게임페이지로 이동시키기
    for player in bingo_game.get_players().values():
        player.set_is_waiting(False)
        emit("moveGamePage", response_data, room=player.get_sid())

def create_game_room(game_match):
    # MySQL 데이터베이스에 게임방 생성
    title = "빙고게임 시작"
    with connection.cursor() as cursor:
        cursor.execute("INSERT INTO bingo_game_room (title) VALUES (%s)", (title,))
        connection.commit()
        game_room_id = cursor.lastrowid

    # 게임 멤버 테이블에 게임룸 ID와 유저 ID 추가
    with connection.cursor() as cursor:
        for player in game_match.get_players().values():
            cursor.execute("INSERT INTO game_member (bingo_game_room_id, player_id) VALUES (%s, %s)", (game_room_id, player.get_id()))
            connection.commit()

    # 게임방 만들기
    bingo_game = BingoGame(game_room_id)
    bingo_game.set_players(game_match.get_players())
    bingo_game.generate_players_bingo_card()
    bingo_games[game_room_id] = bingo_game

    return bingo_game

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
            "opp_players": bingo_game.get_opp_info(player),
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
    socketio.run(app, debug=True)