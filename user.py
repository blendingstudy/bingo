from bingo_card import BingoCard
from bingo_data import BingoData
import pymysql.cursors


class User:

    def __init__(self, id, nickname, profile_img):
        self.id = id
        self.nickname = nickname
        self.bingo_card = None
        self.profile_img = profile_img
        self.game_match_num = 0

    def get_nickname(self):
        return self.nickname

    def get_record(self):
        return self.record

    def get_bingo_card(self):
        return self.bingo_card.get_card()

    def get_id(self):
        return self.id

    def get_profile_img(self):
        return self.profile_img

    def get_game_match_num(self):
        return self.game_match_num

    def set_game_match_num(self, game_match_num):
        print("game match num:", game_match_num)
        self.game_match_num = game_match_num

    def generate_bingo_card(self):
        self.bingo_card = BingoCard()

    def check_number(self, number):
        return self.bingo_card.check_number(number)

    def check_bingo(self):
        return self.bingo_card.check_bingo()

