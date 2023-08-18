from flask import Flask, render_template, request, session, jsonify, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room, close_room, rooms, disconnect
from flask_session import Session  # for server-side sessions
import os
from queue import Queue
from user import User
from bingo_game import BingoGame
from bingo_data import BingoData
import pymysql.cursors
from game_match import GameMatch
import random
from bingo_dao import BingoDao
import time

app = Flask(__name__)

app.config['SECRET_KEY'] = os.urandom(24)

SESSION_TYPE = 'filesystem'
app.config.from_object(__name__)
Session(app)

socketio = SocketIO(app, manage_session=False)

client_sessions = {}
player_sessions = {}
bingo_games = {}
game_matchs = {}
GAME_MATCH_CNT = 1

connection = pymysql.connect(host=BingoData.MYSQL_HOST,
                                    user=BingoData.MYSQL_USER,
                                    password=BingoData.MYSQL_PW,
                                    db=BingoData.MYSQL_DB,
                                    charset='utf8mb4',
                                    cursorclass=pymysql.cursors.DictCursor,
                                    autocommit=True)

bingoDao = BingoDao()

# Matchmaking queue
waiting_queue = Queue()

# 로그인 페이지
@app.route('/')
def index_page():
    return render_template('login.html')

@app.route('/signup')
def signup_page():
    return render_template('signup.html')

# 마이페이지
@app.route('/mypage')
def mypage_page():
    return render_template('mypage.html')

# 게임방 리스트 페이지
@app.route('/gameroom/list')
def game_room_list_page():
    return render_template('game_room_list.html')

# 대기 페이지
# @app.route('/waiting')
# def waiting_page():
#     return render_template('waiting.html')

# 게임 페이지
@app.route('/game')
def game_page():
    return render_template('game.html')

@app.route('/game2')
def game2_page():
    return render_template('game2.html')

@app.route('/img/ticket')
def show_image():
    # 이미지 파일이 있는 폴더 경로
    image_folder = 'img'
    
    # 이미지 파일명
    image_filename = 'game_ticket.png'  # 이미지 파일명을 적절하게 변경하세요
    
    return send_from_directory(image_folder, image_filename)


# [GET] /login
# 로그인
@app.route('/login', methods=['POST'])
def loginApi():
    data = request.get_json()

    # json 데이터에서 nickname, password값 가져옴
    nickname = data.get("nickname")
    password = data.get("password")

    # 데이터베이스에서 해당 nickname과 pw를 가진 유저 조회
    user_data = bingoDao.login(nickname, password)
    
    print(user_data)
    if user_data:
        # 조회된 유저 정보를 사용하여 User 객체 생성 및 등록
        user = User(user_data["user_id"], nickname, user_data["win"], user_data["lose"], user_data['profile_img'])
        client_sessions[nickname] = user
        print(f"login success(로그인 성공): {nickname}")
        # 응답
        response = {'user_id': user_data["user_id"]}  # user_id를 JSON 응답에 포함
        return jsonify(response)
    else:
        print("no user!!!!!")
        return "404 user not found", 404


# [POST] /signup
# 회원가입
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()

    nickname = data.get("nickname")
    password = data.get("password")
    referral = data.get("referral")

    # 데이터베이스에서 해당 nickname을 가진 유저 조회
    user_data = bingoDao.find_user_by_nickname(nickname)

    print(user_data)
    if user_data: # 이미 가입된 유저 닉네임
        print("user is already exist")
        return "404 user is already exist", 404
    else:
        # 추천인 조회
        referral_user_id = None
        if referral:
            referral_user_data = bingoDao.find_user_by_nickname(referral)
            if referral_user_data:
                referral_user_id = referral_user_data['user_id']
        
        # 회원가입
        signupUser = bingoDao.save_user(nickname, password, referral_user_id)
        client_sessions[nickname] = User(signupUser['user_id'], nickname, 0, 0, signupUser['profile_img'])
        print(f"new user signup success(회원가입 성공): {nickname}")

        # 응답
        response_data = {"userId" : signupUser['user_id']}
        return jsonify(response_data)


# [GET] /user/duplicate?nickname=
# 닉네임 중복 확인
@app.route('/user/duplicate', methods=['GET'])
def checkNicknameDuplicate():
    nickname = request.args.get('nickname')

    user_data = bingoDao.find_user_by_nickname(nickname)

    if user_data:
        response_data = {"isDuplicate" : True}
        return jsonify(response_data)
    else:
        response_data = {"isDuplicate" : False}
        return jsonify(response_data)


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
        print("find user info(유저정보 발견):", nickname)
        response = {'nickname': user.get_nickname(), 'record': user.get_record(), "profileIMG": user.get_profile_img()}
        return jsonify(response)
    else:
        print("fail to find user info(유저정보 발견 실패)")
        error_message = {'error': '유저정보 발견 실패.'}
        return jsonify(error_message), 500


# [GET] /user?nickname=
# 게임방 리스트 정보
@app.route('/gameroom/list/info', methods=['GET'])
def game_room_list():

    game_room_list_data = bingoDao.find_game_room_list()

    game_room_list = []
    for game in game_room_list_data:
        print(game)
        game_room_list_data = bingoDao.fing_game_member_list(game["bingo_game_room_id"])

        players = {}

        

        players2 = []

        for member in game_room_list_data:
            print(member)
            players[member["sid"]] = User(member["player_id"], member["nickname"], 0, 0, member["profile_img"])
            user_data = {
                "player_id": member["player_id"],
                "nickname": member["nickname"],
                "profile_img": member["profile_img"]
            }

            players2.append(user_data)

        bingo_game = BingoGame(game["bingo_game_room_id"], players)

        game_room_data = {
            "game_room_id": game["bingo_game_room_id"],
            "players": players2
        }

        game_room_list.append(game_room_data)

    response_data = {
        "game_room_list" : game_room_list
    }

    return jsonify(response_data)




@app.route('/userRead')
def user_read():
    # 데이터베이스 쿼리
    with connection.cursor() as cursor:
        cursor.execute('SELECT * FROM user')
        results = cursor.fetchall()

    # 결과 출력
    response = []
    for row in results:
        print(row)
        response.append(row)

    return jsonify(response)


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
    user_data = bingoDao.find_user_by_nickname(nickname)

    if user_data:
        # 조회된 유저 정보를 사용하여 User 객체 생성
        user = User(user_data['user_id'], nickname, user_data['win'], user_data['lose'], user_data['profile_img'])
        client_sessions[nickname] = user  # client_sessions에 추가
        return user

    # 유저를 찾지 못한 경우 None 반환
    return None


# -----소켓통신------

@socketio.on('connect', namespace='/')
def on_connect():
    player_sessions[request.sid] = None
    print('Client connected:', request.sid)

@socketio.on('disconnect', namespace='/')
def on_disconnect():
    # 게임 매칭에서 제외
    if player_sessions[request.sid]:
        player = player_sessions[request.sid]
        if player.get_game_match_num() in game_matchs.keys():
            game_match = game_matchs[player.get_game_match_num()]
            game_match.remove_player(request.sid)
            print("Remove player at match by Client disconneted")

            for player_sid in game_match.get_players().keys():
                emit("playerOutOfMatch", room=player_sid)
                print("out player!!!!")
                
    if request.sid in player_sessions.keys() or player_sessions[request.sid]:
        print("Remove player at sessions by Client disconneted")
        del player_sessions[request.sid]

    print('Client disconnected', request.sid)

# [SOCKET] resetSID
# 유저의 sid 다시 설정
# @socketio.on("resetSID", namespace='/')
# def reset_sid(data):
#     nickname = data["nickname"]
#     user = find_user(nickname)  # 유저를 find_user() 메소드로 찾음

#     if user:
#         user.set_sid(request.sid)
#         print(f"Reset SID for user: {nickname}, SID: {request.sid}")
#     else:
#         print(f"User not found: {nickname}")


# [SOCKET] setSID
# 유저의 sid 설정
@socketio.on("setSID", namespace='/')
def set_sid(data):
    nickname = data["nickname"]
    user = find_user(nickname)  # 유저를 find_user() 메소드로 찾음

    if user:
        player_sessions[request.sid] = user
        print(f"Set SID for user: {nickname}, SID: {request.sid}")
    else:
        print(f"User not found: {nickname}")


# 게임 매칭정보 요청
@socketio.on('resendPlayerMathcInfo', namespace='/')
def resend_player_match_info(data):
    game_match_num = data["game_match_num"]
    game_match = game_matchs[game_match_num]

    player = player_sessions[request.sid]

    for opp_sid in game_match.get_players().keys():
        if opp_sid != request.sid and player_sessions[opp_sid]:
            opp = player_sessions[opp_sid]
            response_data = {"leader": game_match.get_leader_sid() == opp_sid, "game_match_num": game_match.get_id(), "opp_nickname": player.get_nickname(), "opp_record": player.get_record(), "opp_profile_img": player.get_profile_img(), "idx": game_match.num_of_wating_player()}
            emit('newPlayerMatched', response_data, room=opp_sid)


# [SOCKET] waiting
# 게임 매칭
@socketio.on('waiting', namespace='/')
def ready(data):

    nickname = data['nickname']
    print(f"game ready: {nickname}, sid: {request.sid}")

    if request.sid not in player_sessions.keys():
        print("fail to find user(유저정보 발견 실패)")
        return

    player = player_sessions[request.sid]

    global GAME_MATCH_CNT

    # 이전 매칭에 플레이어 추가
    if GAME_MATCH_CNT-1 in game_matchs.keys():
        prev_game_match = game_matchs[GAME_MATCH_CNT-1]
        if prev_game_match.num_of_wating_player() < BingoData.MAX_PLAYER_SIZE and not prev_game_match.is_match_complete():
            print("add player at prev_matcing")
            player.set_game_match_num(GAME_MATCH_CNT-1)
            prev_game_match.add_player(request.sid, player)
            send_match_player_info(request.sid, player, prev_game_match)
    # 새로운 매칭 만들기
    else:
        print("new matching")
        player.set_game_match_num(GAME_MATCH_CNT)
        game_match = GameMatch(GAME_MATCH_CNT)
        game_match.add_player(request.sid, player)
        game_matchs[GAME_MATCH_CNT] = game_match
        GAME_MATCH_CNT += 1


def send_match_player_info(sid, player, game_match):
    # 다른 플레이어들에겐 새로운 플레이어의 정보 전달
    for opp_sid in game_match.get_players().keys():
        if opp_sid != sid and player_sessions[opp_sid]:
            opp = player_sessions[opp_sid]
            response_data = {"leader": game_match.get_leader_sid() == opp_sid, "game_match_num": game_match.get_id(), "opp_nickname": player.get_nickname(), "opp_record": player.get_record(), "opp_profile_img": player.get_profile_img(), "idx": game_match.num_of_wating_player()}
            emit('newPlayerMatched', response_data, room=opp_sid)
    
    # 새로운 플레이어에게 이전 매칭된 플레이어들의 정보 전달
    for opp_sid in game_match.get_players().keys():
        if opp_sid != sid and player_sessions[opp_sid]:
            opp = player_sessions[opp_sid]
            response_data = {"leader": game_match.get_leader() == player, "game_match_num": game_match.get_id(), "opp_nickname": opp.get_nickname(), "opp_record": opp.get_record(), "opp_profile_img": opp.get_profile_img()}
            emit('gameMatchComplete', response_data, room=sid)
            # print(f"send to a-sid: {player_a.get_sid()}")
        else:
            send_sold_ticket_list(sid, game_match)

# 티켓 판매 현황
def send_sold_ticket_list(player_sid, game_match):
    ticket_list = game_match.get_ticket_list()

    response_data = {
        "ticket_list" : ticket_list
    }

    emit("soldTicketList", response_data, room=player_sid)



# 티켓 구매
@socketio.on('buyTicket', namespace='/')
def buy_ticket(data):
    # 필요한 데이터
    # 유저sid, 게임매칭id, 티켓id
    game_match_num = data["game_match_num"]
    ticket_id = data["ticket_id"]

    game_match = game_matchs[game_match_num]

    ticket_buy_success = game_match.buy_ticket(request.sid, ticket_id)

    if ticket_buy_success:
        for player_sid in game_match.get_players().keys():
            if player_sid == request.sid:
                response_data = {
                    "ticket_id" : ticket_id
                }
                emit("successTicketBuy", response_data, room=player_sid)
                continue

            # 구매 완료시, 모든 플레이어들에게 emit해줘야함.
            response_data = {
                "ticket_id" : ticket_id
            }
            emit("ticketSold", response_data, room=player_sid)


    # 티켓 다 팔리면 게임 시작해야함.
    if game_match.get_left_ticket_num() == 0:
        print("all ticket sold out(티켓 다 팔림): game_match_num=", game_match_num)
        print(game_match.get_players())
        del game_matchs[game_match_num] # 게임 매칭 데이터 삭제
        game_start(game_match.get_players(), game_match.get_tickets())

    return


# 게임 시작
def game_start(players, tickets):
    # 빙고게임 만들기
    game_room_num = bingoDao.save_game_room(players)

    bingo_game = BingoGame(game_room_num, players, tickets)

    bingo_games[game_room_num] = bingo_game 
            
    for player_sid in players.keys():
        emit("countDown", room=player_sid)

    # 4초 후에 게임 시작
    time.sleep(4)

    # 빙고 게임 정보 전달
    bingo_cards = bingo_game.get_bingo_cards()
    for player_sid in bingo_cards.keys():
        response_data = {}
        opp_player_info = []

        for opp_sid, opp_bingo_card in bingo_cards.items():
            if player_sid == opp_sid: # 나일 경우
                response_data["myBingoCard"] = opp_bingo_card.get_cards()
            else: # 상대 플레이어일 경우
                opp_player = player_sessions[opp_sid]
                opp_player_info.append({
                    "oppId" : opp_player.get_id(), 
                    "oppBingoCard" : opp_bingo_card.get_cards()
                })
            
        response_data["oppInfo"] = opp_player_info
        emit("gameStartInfo", response_data, room=player_sid)

    # 1초 후 게임 시작
    time.sleep(1)
    bingo_game.game_start()


if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)