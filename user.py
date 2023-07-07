from bingo_card import BingoCard


class User:

    def __init__(self, nickname):
        self.nickname = nickname
        self.bingo_card = None
        self.sid = None
        self.record = {'win': 0, 'lose': 0}
        self.is_waiting = False

    def get_nickname(self):
        return self.nickname

    def get_record(self):
        return self.record

    def get_bingo_card(self):
        return self.bingo_card.get_card()

    def get_sid(self):
        return self.sid

    def get_is_waiting(self):
        return self.is_waiting

    def set_sid(self, sid):
        self.sid = sid

    def set_is_waiting(self, is_waiting):
        self.is_waiting = is_waiting

    def win(self):
        self.record['win'] += 1

    def lose(self):
        self.record['lose'] += 1

    def generate_bingo_card(self):
        self.bingo_card = BingoCard()

    def check_number(self, number):
        return self.bingo_card.check_number(number)

    def check_bingo(self):
        return self.bingo_card.check_bingo()

