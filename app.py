from flask import Flask, render_template, request, session, jsonify, send_from_directory, redirect, url_for
from flask_socketio import SocketIO, emit
from flask_session import Session  # for server-side sessions
import os
from queue import Queue
from user import User
from bingo_game import BingoGame
from bingo_data import BingoData
import pymysql.cursors
from game_match import GameMatch
from bingo_dao import BingoDao
import time

app = Flask(__name__)

app.config['SECRET_KEY'] = os.urandom(24)

SESSION_TYPE = 'filesystem'
app.config.from_object(__name__)
Session(app)

socketio = SocketIO(app, manage_session=False)
bingoDao = BingoDao()

client_sessions = {} # [key]nickname = [value]User.class 
player_sessions = {} # [key]sid = [value]User.class 
bingo_games = {} # [key]id = [value]BingoGame.class 
game_matchs = {} # [key]id = [value]GameMatch.class 

GAME_MATCH_CNT = 1

connection = pymysql.connect(host=BingoData.MYSQL_HOST,
                                    user=BingoData.MYSQL_USER,
                                    password=BingoData.MYSQL_PW,
                                    db=BingoData.MYSQL_DB,
                                    charset='utf8mb4',
                                    cursorclass=pymysql.cursors.DictCursor,
                                    autocommit=True)


# 로그인 페이지
@app.route('/')
def index_page():
    return render_template('login.html')

# 회원가입 페이지
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

# 게임 페이지
@app.route('/game')
def game2_page():
    return render_template('game.html')


# 티켓 이미지
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
        user = User(user_data["user_id"], nickname, user_data['profile_img'])
        client_sessions[nickname] = user
        print(f"login success(로그인 성공): {nickname}")
        # 응답
        response = {'userId': user_data["user_id"]}  # user_id를 JSON 응답에 포함
        return jsonify(response)
    else:
        print("no user")
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
        client_sessions[nickname] = User(signupUser['user_id'], nickname, signupUser['profile_img'])
        print(f"new user signup success(회원가입 성공): {nickname}")

        # 응답
        response = {"userId" : signupUser['user_id']}
        return jsonify(response)


# [GET] /user/duplicate?nickname=
# 닉네임 중복 확인
@app.route('/user/duplicate', methods=['GET'])
def checkNicknameDuplicate():
    nickname = request.args.get('nickname')

    user_data = bingoDao.find_user_by_nickname(nickname)

    if user_data:
        response = {"isDuplicate" : True}
        return jsonify(response)
    else:
        response = {"isDuplicate" : False}
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
        print("find user info(유저정보 발견):", nickname)
        response = {'nickname': user.get_nickname(), "profileIMG": user.get_profile_img()}
        return jsonify(response)
    else:
        print("fail to find user info(유저정보 발견 실패)")
        error_message = {'error': '유저정보 발견 실패.'}
        return jsonify(error_message), 500


# [GET] /gameroom/list/info
# 게임방 리스트 정보
@app.route('/gameroom/list/info', methods=['GET'])
def game_room_list():
    
    game_room_list = []
    for game_id, game in game_matchs.items():
        # 게임 플레이어
        players = []
        for member in game.get_players().values():
            user_data = {
                "playerId": member.get_id(),
                "nickname": member.get_nickname(),
                "profileImg": member.get_profile_img()
            }

            players.append(user_data)

        game_room_data = {
            "gameRoomId": game_id,
            "status": "WAITING" if game.is_waiting() else "PLAYING",
            "players": players
        }

        game_room_list.append(game_room_data)

    response = {
        "gameRoomList" : game_room_list
    }

    return jsonify(response)


# [POST] /gameroom
# 새 게임방 생성
@app.route('/gameroom', methods=['POST'])
def createNewGameroom():
    data = request.get_json()

    nickname = data.get("nickname")

    global GAME_MATCH_CNT
    
    print("create new game(새 게임 생성)")
    game_match = GameMatch(GAME_MATCH_CNT)
    game_matchs[GAME_MATCH_CNT] = game_match
    response = {
        "gameMatchNum" : GAME_MATCH_CNT
    }

    GAME_MATCH_CNT += 1
    
    return jsonify(response)


# [GET] /userRead
# 유저 데이터베이스 확인
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


# DB or 로컬섹션에서 닉네임으로 유저찾기
def find_user(nickname):
    # client_sessions에서 해당 nickname 유저 찾기
    if nickname in client_sessions.keys():
        return client_sessions[nickname]

    # 데이터베이스에서 해당 nickname을 가진 유저 조회
    user_data = bingoDao.find_user_by_nickname(nickname)

    if user_data:
        # 조회된 유저 정보를 사용하여 User 객체 생성
        user = User(user_data['user_id'], nickname, user_data['profile_img'])
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
    # 플레이어 섹션에서 제외

    print('Client disconnected', request.sid)


# [SOCKET] setSID
# 유저의 sid 설정
@socketio.on("setSID", namespace='/')
def set_sid(data):
    nickname = data["nickname"]
    user = find_user(nickname)  # 유저를 find_user() 메소드로 찾음

    if user:
        player_sessions[request.sid] = user
        print(f"Set SID for user(sid 세팅): {nickname}, SID: {request.sid}")
    else:
        print(f"User not found: {nickname}")



# [SOCKET] enterGameRoom
# 게임 매칭방 입장
@socketio.on('enterGameRoom', namespace='/')
def enter_game_room(data):
    game_match_num = data["game_match_num"]
    print("enter game room!(게임방 입장) ID=", game_match_num)

    game_match = game_matchs[game_match_num]
    player = player_sessions[request.sid]

    if game_match.num_of_wating_player() < BingoData.MAX_PLAYER_SIZE and game_match.is_waiting():
        print("add player at match=", game_match_num)
        game_match.add_player(request.sid, player)
        send_match_player_info(request.sid, player, game_match)
    else:
        print("can't enter game room!(해당 게임방에 들어갈 수 없음), ID=", game_match_num)
        return redirect(url_for('/gameroom/list')) # 게임방 리스트로 리다이렉트


def send_match_player_info(sid, player, game_match):
    
    # 다른 플레이어들에겐 새로운 플레이어의 정보 전달
    for opp_sid in game_match.get_players().keys():
        if opp_sid != sid and player_sessions[opp_sid]:
            opp = player_sessions[opp_sid]
            response = {"gameMatchNum": game_match.get_id(), "oppNickname": player.get_nickname(), "oppProfileImg": player.get_profile_img(), "idx": game_match.num_of_wating_player()}
            emit('newPlayerMatched', response, room=opp_sid) # 여기 room번호가 다름!
            
    
    # 새로운 플레이어에겐 이전 매칭된 플레이어들의 정보 전달
    opp_player_list = []
    for opp_sid in game_match.get_players().keys():
        # 이전 매칭된 플레이어의 정보 모으기
        if opp_sid != sid and player_sessions[opp_sid]: 
            opp = player_sessions[opp_sid]
            opp_player_data = {"gameMatchNum": game_match.get_id(), "oppNickname": opp.get_nickname(), "oppProfileImg": opp.get_profile_img()}
            opp_player_list.append(opp_player_data)
        # 새로운 플레이어에게 티켓정보 전달
        else: 
            response = {
                "ticket_list" : game_match.get_ticket_list()
            }

            emit("soldTicketList", response, room=sid)

    if len(opp_player_list) != 0:
        response = {"oppPlayersInfo": opp_player_list} 
        emit('MatchedGamePlayerInfo', response, room=sid) # 여기 room번호가 다름!


# [SOCKET] buyTicket
# 티켓 구매
@socketio.on('buyTicket', namespace='/')
def buy_ticket(data):
    game_match_num = data["game_match_num"]
    ticket_id = data["ticket_id"]

    print("게임룸 넘버:", game_match_num)

    game_match = game_matchs[game_match_num]

    ticket_buy_success = game_match.buy_ticket(request.sid, ticket_id)

    if ticket_buy_success:
        for player_sid in game_match.get_players().keys():
            # 구매자에게 구매성공 알림.
            if player_sid == request.sid:
                response = {
                    "ticketId" : ticket_id
                }
                emit("successTicketBuy", response, room=player_sid)
                continue

            # 구매 완료시, 모든 플레이어들에게 emit해줘야함.
            response = {
                "ticketId" : ticket_id
            }
            emit("ticketSold", response, room=player_sid)


    # 티켓 다 팔리면 게임 시작해야함.
    if game_match.get_left_ticket_num() == 0:
        print("all ticket sold out(티켓 다 팔림): game_match_num=", game_match_num)
        game_match.game_start()
        game_start(game_match.get_players(), game_match.get_tickets())

    return


# 게임 시작
def game_start(players, tickets):
    # 빙고게임 만들기
    game_room_num = bingoDao.save_game_room(players)

    bingo_game = BingoGame(game_room_num, players, tickets)

    bingo_games[game_room_num] = bingo_game 
            
    for player_sid in players.keys():
        emit("gameCountDownStart", room=player_sid)

    # 4초 후에 게임 시작
    time.sleep(4)

    # 빙고 게임 정보 전달
    bingo_cards = bingo_game.get_bingo_cards()
    for player_sid in bingo_cards.keys():
        response = {}
        opp_player_info = []

        for opp_sid, opp_bingo_card in bingo_cards.items():
            if player_sid == opp_sid: # 나일 경우
                response["myBingoCard"] = opp_bingo_card.get_cards()
            else: # 상대 플레이어일 경우
                opp_player = player_sessions[opp_sid]
                opp_player_info.append({
                    "oppId" : opp_player.get_id(), 
                    "oppBingoCard" : opp_bingo_card.get_cards()
                })
            
        response["oppInfo"] = opp_player_info
        emit("gameStartInfo", response, room=player_sid)

    # 1초 후 게임 시작
    time.sleep(1)
    bingo_game.game_start()


if __name__ == '__main__':
    socketio.run(app, debug=True)