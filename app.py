from flask import Flask, render_template, request, session, jsonify, send_from_directory, redirect, url_for
from flask_socketio import SocketIO, emit
from flask_session import Session  # for server-side sessions
import os
from queue import Queue
from user import User
from bingo_data import BingoData
import pymysql.cursors
from game_room import GameRoom
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
player_sessions = {} # [key]player_sid = [value]User.class 
game_rooms = {} # [key]id = [value]GameMatch.class 

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
    for game_id, game in game_rooms.items():
        # 게임 끝난건 제외
        if game.is_game_over():
            continue

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
    
    print("create new game(새 게임 생성)")
    game_room_num = bingoDao.save_game_room_ver2()
    game_room = GameRoom(game_room_num)
    game_rooms[game_room_num] = game_room
    response = {
        "gameRoomNum" : game_room_num
    }
    
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
    game_room_num = data["game_room_num"]
    print("enter game room!(게임방 입장) ID=", game_room_num)

    game_room = game_rooms[game_room_num]
    player = player_sessions[request.sid]

    if game_room.num_of_wating_player() < BingoData.MAX_PLAYER_SIZE and game_room.is_waiting():
        print("add player at match=", game_room_num)
        game_room.add_player(request.sid, player)
        send_match_player_info(request.sid, player, game_room)
    else:
        print("can't enter game room!(해당 게임방에 들어갈 수 없음), ID=", game_room_num)
        return redirect(url_for('/gameroom/list')) # 게임방 리스트로 리다이렉트


def send_match_player_info(player_sid, player, game_room):
    
    # 다른 플레이어들에겐 새로운 플레이어의 정보 전달
    for opp_sid in game_room.get_players().keys():
        if opp_sid != player_sid and player_sessions[opp_sid]:
            opp = player_sessions[opp_sid]
            response = {"gameRoomNum": game_room.get_id(), "oppNickname": player.get_nickname(), "oppProfileImg": player.get_profile_img(), "idx": game_room.num_of_wating_player()}
            emit('newPlayerMatched', response, room=opp_sid) # 여기 room번호가 다름!
            
    
    # 새로운 플레이어에겐 이전 매칭된 플레이어들의 정보 전달
    opp_player_list = []
    for opp_sid in game_room.get_players().keys():
        # 이전 매칭된 플레이어의 정보 모으기
        if opp_sid != player_sid and player_sessions[opp_sid]: 
            opp = player_sessions[opp_sid]
            opp_player_data = {"gameRoomNum": game_room.get_id(), "oppNickname": opp.get_nickname(), "oppProfileImg": opp.get_profile_img()}
            opp_player_list.append(opp_player_data)
        
    if len(opp_player_list) != 0:
        response = {"oppPlayersInfo": opp_player_list} 
        emit('MatchedGamePlayerInfo', response, room=player_sid) # 여기 room번호가 다름!

    # 새로운 플레이어에겐 팔린티켓정보 전달
    response = {
        "ticket_list" : game_room.get_ticket_list()
    }
    emit("soldTicketList", response, room=player_sid)


# [SOCKET] buyTicket
# 티켓 구매
@socketio.on('buyTicket', namespace='/')
def buy_ticket(data):
    game_room_num = data["game_room_num"]
    ticket_id = data["ticket_id"]

    print("게임룸 넘버:", game_room_num)

    game_room = game_rooms[game_room_num]

    ticket_buy_success = game_room.buy_ticket(request.sid, ticket_id)

    if ticket_buy_success:
        for player_sid in game_room.get_players().keys():
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
    if game_room.get_left_ticket_num() == 0:
        print("all ticket sold out(티켓 다 팔림): game_room_num=", game_room_num)
        game_room.game_start()

    return



if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)