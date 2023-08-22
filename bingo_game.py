import random
from bingo_card import BingoCard
from bingo_data import BingoData
from flask_socketio import SocketIO, emit, join_room, leave_room, close_room, rooms, disconnect
from flask_session import Session  # for server-side sessions
import sched
import time

class BingoGame:
    # def __init__(self, game_room_num, players, tickets):
    #     self.game_room_num = game_room_num
    #     self.players = players # 키=player_sid / 값=User.class
    #     self.bingo_cards = self.create_bingo_cards(tickets) # 키=player_sid / 값=BingoCard.class
    #     self.game_over = False
    #     self.created_random_nums = []
    #     self.scheduler = sched.scheduler(time.time, time.sleep)

    #     ### 버전2 시작
    #     self.tickets = {} # 키=player_sid / 값=구매한 티켓 개수
    #     self.ticket_list = [0,0,0,0,0,0,0,0,0,0]
    #     self.left_ticket = 10
    #     self.match_complete = False
    #     ### 버전2 끝

    def __init__(self, game_room_num, players):
        self.game_room_num = game_room_num
        self.players = players # 키=player_sid / 값=User.class
        self.bingo_cards = None# 키=player_sid / 값=BingoCard.class
        self.game_over = False
        self.created_random_nums = []
        self.scheduler = sched.scheduler(time.time, time.sleep)

        ### 버전2 시작
        self.tickets = {} # 키=player_sid / 값=구매한 티켓 개수
        self.ticket_list = [0,0,0,0,0,0,0,0,0,0]
        self.left_ticket = 10
        self.match_complete = False
        ### 버전2 끝

    ### 버전2 시작

    def add_player(self, sid, player):
        self.players[sid] = player
        self.tickets[sid] = 0
        print(f"{player}is add to match at matching {self.id}")

    def remove_player(self, sid):
        if sid in self.players.keys():
            del self.players[sid]
            del self.tickets[sid]
            print(f"{sid}is remove at match!!!!")
        else:
            print(f"{sid}can't find at match!!!")

    def buy_ticket(self, player_sid, ticket_id):
        if self.tickets[player_sid] >= 5: # 5개 이하까지만 구매 가능
            return False
        if self.ticket_list[ticket_id]: # 이미 구매된 티켓
            return False

        self.tickets[player_sid] += 1
        self.ticket_list[ticket_id] = 1
        self.left_ticket -= 1

        return True

    ### 버전2 끝

    def get_bingo_cards(self):
        return self.bingo_cards

    # 각 플레이어별 빙고 카드 생성
    def create_bingo_cards(self, tickets):
        random_numbers = random.sample(range(1, BingoData.BINGO_MAX_NUMBER + 1), BingoData.BINGO_MAX_NUMBER)  # 10개의 중복 없는 랜덤한 숫자 생성
        bingo_cards = {}
        last_idx = 0
        
        for player_sid, ticket_num in tickets.items():
            bingo_card = BingoCard(ticket_num)
            print("random number list:", random_numbers[last_idx:last_idx+ticket_num*5])
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

        # 99개 다 발표하면 종료 || 게임이 종료되면
        if len(self.created_random_nums) == BingoData.BINGO_MAX_NUMBER or self.game_over:
            print("stop create random num(랜덤 숫자 생성 종료)")
            return
        else:
            self.scheduler.enter(2, 1, self.create_random_num, ())

    # 빙고게임 시작
    def game_start(self):
        print("bingo game start(게임 시작): game_room_num=", self.game_room_num)

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

    # 게임이 끝났는지 확인
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

