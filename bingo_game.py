from flask import Flask, render_template, request, session, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room, close_room, rooms, disconnect
from flask_session import Session  # for server-side sessions
import random
from user import User
from bingo_card import BingoCard
import threading
import sched
import time

class BingoGame:

    MAX_PLAYER_SIZE = 2
    MIN_PLAYER_SIZE = 2

    def __init__(self, game_room_num):
        self.players = {}
        self.game_room_num = game_room_num
        self.ready_cnt = 0
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.random_numbers = []
        self.is_game_over = False

        self.generate_players_bingo_card()

    # 플레이어 추가
    def add_player(self, player):
        self.players[player.get_nickname()] = player


    # 플레이어들의 빙고판 생성
    def generate_players_bingo_card(self):
        for player in self.players.values():
            player.generate_bingo_card()
            # print("crate bingo card: ", player.get_bingo_card())


    def player_ready(self):
        self.ready_cnt += 1


    # 모든 플레이어가 게임방에 들어왔는지 확인
    def is_every_player_ready(self):
        if(self.ready_cnt == len(self.players)):
            return True
        else:
            return False


    # 게임 시작
    def start_game(self):
        print("-----bingo game start!!-----")

        if len(self.players) < BingoGame.MIN_PLAYER_SIZE:
            raise ValueError("Error: Not enough players to start the game.")

        #2초마다 랜덤 넘버 뽑고, 빙고판에 있는지 확인.
        self.scheduler.enter(0, 1, self.generate_random_number, ())  # 함수 호출 시작
        self.scheduler.run()


    def generate_random_number(self):
        # 1~99사이 중복없이 랜덤 숫자 발표
        number = random.sample([x for x in range(1, BingoCard.BINGO_MAX_NUMBER + 1) if x not in  self.random_numbers], 1)[0]
        self.random_numbers.append(number)

        # 내 빙고판에 숫자가 있는지 확인.
        for player in self.players.values():
            isChecked, x, y = player.check_number(number)
            response_data = {"num":number, "isChecked":isChecked, "x":x, "y":y}
            emit("generateRandomNumber", response_data, room=player.get_sid())

            #내 빙고판에 숫자가 있으면 상대방에게 알려줘야함.
            if isChecked:
                for opp in self.players.values():
                    if opp != player :
                        response_data = {"x": x, "y": y}
                        emit("oppCheckBingoCell", response_data, room=opp.get_sid())

        # 99개 다 발표하면 종료 || 게임이 종료되면
        if len(self.random_numbers) == BingoCard.BINGO_MAX_NUMBER or self.is_game_over:
            return
        else:
            self.scheduler.enter(2, 1, self.generate_random_number, ())


    # 빙고가 됐는지 확인
    def check_bingo(self, player):
        result = player.check_bingo()

        if result:
            self.game_over(player)

        return result


    # 게임 끝
    def game_over(self, winner):
        self.is_game_over = True

        for player in self.players.values():
            if player == winner:
                winner.win()
                emit("bingoGameOver", {"isWin": True}, room=player.get_sid())
            else:
                player.lose()
                emit("bingoGameOver", {"isWin": False}, room=player.get_sid())


    def get_game_room_num(self):
        return self.game_room_num
    
    def get_players(self):
        return self.players
        
    # 내 정보
    def get_my_info(self, nickname):
        if nickname in self.players.keys():
            player = self.players[nickname]

            response_data = {
                "nickname" : player.get_nickname(),
                "record" : player.get_record()
            }

            return response_data
        
    # 상대 플레이어 정보
    def get_opp_info(self, nickname):
        for key in self.players.keys():
            if(key != nickname):
                opp_player = self.players[key]

                response_data = {
                    "nickname" : opp_player.get_nickname(),
                    "record" : opp_player.get_record()
                }

                return response_data

    # 내 빙고판  
    def get_my_bingo_card(self, nickname):
        if nickname in self.players.keys():
            player = self.players[nickname]

            if player.get_bingo_card() != None:
                return player.get_bingo_card()
            else :
                return "빙고판 nullㅠㅠ"