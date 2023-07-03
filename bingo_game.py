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
    def __init__(self, game_room_num):
        self._players = {}
        self._game_room_num = game_room_num
        self._ready_cnt = 0
        self._scheduler = sched.scheduler(time.time, time.sleep)
        self._random_numbers = []

        self.generate_players_bingo_card()

    def generate_random_number(self):
        # used_numbers = [player.number for player in self._players]
        # number = random.choice([i for i in range(1, 51) if i not in used_numbers])
        # 바꿔야함!
        # 필드로 배열 만들고, 거기에 여지껏 나온 숫자 저장해놓아야 함.
        number = random.sample([x for x in range(1, 51) if x not in  self._random_numbers], 1)[0]
        self._random_numbers.append(number)
        response_data = {"num":number}

        for player in self._players.values():
            emit("generateRandomNumber", response_data, room=player.get_session_id())

        # 50개 다 발표하면 종료
        # 50개로 수정해야 함!!
        if len(self._random_numbers) == 15:
            return
        else:
            self._scheduler.enter(2, 1, self.generate_random_number, ())

        


    def add_player(self, player):
        self._players[player.get_nickname()] = player

    def start_game(self):
        print("-----bingo game start!!-----")

        if len(self._players) < 2:
            raise ValueError("Error: Not enough players to start the game.")

        #3초마다 랜덤 넘버 뽑고, 빙고판에 있는지 확인.
        self._scheduler.enter(0, 1, self.generate_random_number, ())  # 함수 호출 시작
        self._scheduler.run()
        
    def generate_players_bingo_card(self):
        for player in self._players.values():
            player.generate_bingo_card()
            # print("crate bingo card: ", player.get_bingo_card())

    def get_game_room_num(self):
        return self._game_room_num
    
    def get_players(self):
        return self._players

    def player_ready(self):
        self._ready_cnt += 1

    def is_every_player_ready(self):
        # 모든 플레이어가 게임방에 들어왔다면
        if(self._ready_cnt == len(self._players)):
            return True
        else:
            return False
        
    def get_my_info(self, nickname):
        if nickname in self._players.keys():
            player = self._players[nickname]

            response_data = {
                "nickname" : player.get_nickname(),
                "record" : player.get_record()
            }

            return response_data
        
    def get_opp_info(self, nickname):
        for key in self._players.keys():
            if(key != nickname):
                opp_player = self._players[key]

                response_data = {
                    "nickname" : opp_player.get_nickname(),
                    "record" : opp_player.get_record()
                }

                return response_data
            
    def get_my_bingo_card(self, nickname):
        if nickname in self._players.keys():
            player = self._players[nickname]

            if player.get_bingo_card() != None:
                return player.get_bingo_card()
            else :
                return "빙고판 nullㅠㅠ"