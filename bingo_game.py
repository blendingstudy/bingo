from flask import Flask, render_template, request, session, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room, close_room, rooms, disconnect
from flask_session import Session  # for server-side sessions
import random
from bingo_data import BingoData
import sched
import time
import pymysql.cursors
from bingo_dao import BingoDao

class BingoGame:
    def __init__(self, game_room_num):
        self.game_room_num = game_room_num
        self.players = {}
        self.ready_cnt = 0
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.random_numbers = []
        self.is_game_over = False
        self.bingoDao = BingoDao()

    def get_game_room_num(self):
        return self.game_room_num
    
    def get_players(self):
        return self.players
        
    # 내 정보
    def get_my_info(self, sid):
        if sid in self.players.keys():
            player = self.players[sid]
            response_data = {
                "nickname" : player.get_nickname(),
                "record" : player.get_record(),
                "profile_img": player.get_profile_img()
            }

            return response_data
        
    # 상대 플레이어 정보
    def get_opp_info(self, player_sid):
        responses = []
        for opp_sid in self.players.keys():
            if(opp_sid != player_sid):
                opp = self.players[opp_sid]
                response_data = {
                    "id" : opp.get_id(),
                    "nickname" : opp.get_nickname(),
                    "record" : opp.get_record(),
                    "profile_img": opp.get_profile_img()
                }
                responses.append(response_data)

        return responses

    # 내 빙고판  
    def get_my_bingo_card(self, sid):
        if sid in self.players.keys():
            player = self.players[sid]
            if player.get_bingo_card() != None:
                return player.get_bingo_card()
            else :
                return "빙고판 nullㅠㅠ"


    # 플레이어 추가
    def add_player(self, sid, player):
        self.players[sid] = player
        self.generate_players_bingo_card()

    # 플레이어 설정
    def set_players(self, players):
        for player in players.values():
            self.players[player.get_sid()] = player
        self.generate_players_bingo_card()

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

        if len(self.players) < BingoData.MIN_PLAYER_SIZE:
            raise ValueError("Error: Not enough players to start the game.")

        #2초마다 랜덤 넘버 뽑고, 빙고판에 있는지 확인.
        self.scheduler.enter(0, 1, self.generate_random_number, ())  # 함수 호출 시작
        self.scheduler.run()

    def generate_random_number(self):
        # 1~99사이 중복없이 랜덤 숫자 발표
        number = random.sample([x for x in range(1, BingoData.BINGO_MAX_NUMBER + 1) if x not in  self.random_numbers], 1)[0]
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
                        response_data = {"playerId":  player.get_id(), "x": x, "y": y}
                        emit("oppCheckBingoCell", response_data, room=opp.get_sid())

        # 99개 다 발표하면 종료 || 게임이 종료되면
        if len(self.random_numbers) == BingoData.BINGO_MAX_NUMBER or self.is_game_over:
            return
        else:
            self.scheduler.enter(2, 1, self.generate_random_number, ())


    # 빙고가 됐는지 확인
    def check_bingo(self, player):
        if player in self.players.values():
            result = player.check_bingo()

            # 두줄 빙고 완성
            if result:
                self.game_over(player)

            return result


    # 게임 끝
    def game_over(self, winner):
        self.is_game_over = True
        self.bingoDao.game_over(self.game_room_num)

        for player in self.players.values():
            if player == winner:
                winner.win()
                emit("bingoGameOver", {"isWin": True}, room=player.get_sid())

                self.bingoDao.win_bingo_game(winner, self.game_room_num)
            else:
                player.lose()
                emit("bingoGameOver", {"isWin": False}, room=player.get_sid())
