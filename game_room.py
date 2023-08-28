import random
from bingo_card import BingoCard
from bingo_data import BingoData
from flask_socketio import SocketIO, emit, join_room, leave_room, close_room, rooms, disconnect
from flask_session import Session  # for server-side sessions
import sched
import time

class GameRoom:
    def __init__(self, id):
        self.id = id 
        self.players = {} # 키=player_sid / 값=User.class
        self.tickets = {} # 키=player_sid / 값=구매한 티켓 개수
        self.bingo_cards = None # 키=player_sid / 값=BingoCard.class
        self.ticket_list = [0,0,0,0,0,0,0,0,0,0]
        self.left_ticket = 10
        self.waiting = True
        self.game_over = False
        self.created_random_nums = []
        self.scheduler = sched.scheduler(time.time, time.sleep)

    def get_players(self):
        return self.players

    def get_id(self):
        return self.id

    def get_tickets(self):
        return self.tickets
    
    def get_ticket_list(self):
        return self.ticket_list
    
    def get_left_ticket_num(self):
        return self.left_ticket

    def is_waiting(self):
        return self.waiting

    def num_of_wating_player(self):
        return len(self.players)

    def is_game_over(self):
        return self.game_over


    # 플레이어 추가
    def add_player(self, player_sid, player):
        self.players[player_sid] = player
        self.tickets[player_sid] = 0
        print(f"{player}is add to match at matching {self.id}")


    # 플레이어 삭제
    def remove_player(self, player_sid):
        if player_sid in self.players.keys():
            del self.players[player_sid]
            del self.tickets[player_sid]
            print(f"{player_sid}is remove at match!!!!")
        else:
            print(f"{player_sid}can't find at match!!!")


    # 티켓 구매
    def buy_ticket(self, player_sid, ticket_id):
        if self.tickets[player_sid] >= 5: # 5개 이하까지만 구매 가능
            return False
        if self.ticket_list[ticket_id]: # 이미 구매된 티켓
            return False

        self.tickets[player_sid] += 1
        self.ticket_list[ticket_id] = 1
        self.left_ticket -= 1

        return True


    # 게임 시작
    def game_start(self):
        self.waiting = False
        self.bingo_cards = self.create_bingo_cards()

        # 카운트 다운 시작
        for player_sid in self.players.keys():
            emit("gameCountDownStart", room=player_sid)

        # 4초 후에 게임 시작
        time.sleep(4)

        # 빙고 게임 정보 전달
        for player_sid in self.bingo_cards.keys():
            response = {}
            opp_player_info = []

            for opp_sid, opp_bingo_card in self.bingo_cards.items():
                if player_sid == opp_sid: # 나일 경우
                    response["myBingoCard"] = opp_bingo_card.get_cards()
                else: # 상대 플레이어일 경우
                    opp_player = self.players[opp_sid]
                    opp_player_info.append({
                        "oppId" : opp_player.get_id(), 
                        "oppBingoCard" : opp_bingo_card.get_cards()
                    })
                
            response["oppInfo"] = opp_player_info
            emit("gameStartInfo", response, room=player_sid)

        # 1초 후 랜덤 숫자 발표 시작
        time.sleep(1)
        self.start_create_random_num()


    # 각 플레이어별 빙고 카드 생성
    def create_bingo_cards(self):
        random_numbers = random.sample(range(1, BingoData.BINGO_MAX_NUMBER + 1), BingoData.BINGO_MAX_NUMBER)  # 50개의 중복 없는 랜덤한 숫자 생성
        bingo_cards = {}
        last_idx = 0
        
        for player_sid, ticket_num in self.tickets.items():
            bingo_card = BingoCard(ticket_num)
            print("random number list:", random_numbers[last_idx:last_idx+ticket_num*5]) # 티켓개수*5 씩 자르기
            bingo_card.create_card(random_numbers[last_idx:last_idx+ticket_num*5])
            last_idx += (ticket_num*5)

            bingo_cards[player_sid] = bingo_card
            

        return bingo_cards


    # 랜덤 숫자 발표
    def create_random_num(self):
        # 1~50사이 중복없이 랜덤 숫자 발표
        number = random.choice([x for x in range(1, BingoData.BINGO_MAX_NUMBER+1) if x not in self.created_random_nums])
        self.created_random_nums.append(number)

        print("create random num(랜덤 숫자 생성)=", number)

        # 플레이어들에게 숫자 전달
        self.send_created_number_to_player(number)

        # 50개 다 발표하면 종료 || 게임이 종료되면
        if len(self.created_random_nums) == BingoData.BINGO_MAX_NUMBER or self.game_over:
            print("stop create random num(랜덤 숫자 생성 종료)")
            return
        else:
            self.scheduler.enter(2, 1, self.create_random_num, ())

    # 랜덤 숫자 생성 시작
    def start_create_random_num(self):
        print("bingo game start(게임 시작): game_room_num=", self.id)

        # 2초마다 랜덤 숫자 발표
        self.scheduler.enter(0, 1, self.create_random_num, ())  # 함수 호출 시작
        self.scheduler.run()


    def send_created_number_to_player(self, number):
        # 모든 플레이어에게 숫자 알림
        for player_sid in self.players.keys():
            response_data = {
                "num" : number
            }
            emit("announceRandomNumber", response_data, room=player_sid)

        # 빙고판에 숫자가 있는지 확인
        for player_sid, player_bingo_card in self.bingo_cards.items():
            isChecked, x, y = player_bingo_card.check(number)

            # 내 빙고판에 숫자가 있다면
            if isChecked:
                # 나한테 알려주기
                response_data = {
                    "num" : number,
                    "x": x,
                    "y": y
                }
                emit("checkRandomNumber", response_data, room=player_sid)

                player_id = self.players[player_sid].get_id()
                
                # 상대 플레이어에게 알려주기
                for opp_sid, opp in self.players.items():
                    if opp_sid != player_sid:
                        response_data = {
                            "oppId" : player_id,
                            "num" : number,
                            "x": x,
                            "y": y
                        }
                        emit("checkOppRandomNumber", response_data, room=opp_sid)

                # 빙고 확인
                self.check_game_over(player_sid, player_bingo_card)

                break # 나한테 숫자가 있다면, 다른 모든 빙고판에는 똑같은 숫자가 없으니까 찾는걸 멈춰도 됨.


    # 빙고 끝났는지 확인
    def check_game_over(self, player_sid, player_bingo_card):
        if player_bingo_card.check_bingo():
            self.game_over = True

            response_data = {"winner": True}
            emit("gameOver", response_data, room=player_sid)
                
            # 상대 플레이어에게 알려주기
            for opp_sid, opp in self.players.items():
                if opp_sid != player_sid:
                    response_data = {"winner": False}
                    emit("gameOver", response_data, room=opp_sid)
