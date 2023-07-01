from flask import Flask, render_template, request, session, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room, close_room, rooms, disconnect
from flask_session import Session  # for server-side sessions
import random
from user import User
from bingo_card import BingoCard

class BingoGame:
    def __init__(self, game_room_num):
        self._players = {}
        self._game_room_num = game_room_num
        self._ready_cnt = 0

        self.generate_players_bingo_card()

    def generate_random_number(self):
        # used_numbers = [player.number for player in self._players]
        # number = random.choice([i for i in range(1, 51) if i not in used_numbers])
        # 바꿔야함!
        number = random.choice()
        return number

    def add_player(self, player):
        self._players[player.get_nickname()] = player

    def start_game(self):
        if len(self._players) < 2:
            raise ValueError("Error: Not enough players to start the game.")

        #2초마다 랜덤 넘버 뽑고, 빙고판에 있는지 확인.


    def get_game_room_num(self):
        return self._game_room_num
    
    def get_players(self):
        return self._players


    def generate_players_bingo_card(self):
        for player in self._players:
            player.generate_bingo_card()
            print(player.get_bingo_card())

            response_data = {"bingo_card":player.get_bingo_card()}
            # emit("createBingoCard", response_data, room=player.get_session_id())

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

            return player.get_bingo_card()