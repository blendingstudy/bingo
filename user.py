from bingo_card import BingoCard


class User:

    def __init__(self, nickname):
        self.nickname = nickname
        self.bingo_card = None
        self._sid = None
        self._record = {'win': 0, 'lose': 0}


    def get_nickname(self):
        return self.nickname

    def get_record(self):
        return self._record

    def get_bingo_card(self):
        return self.bingo_card.get_card()

    def get_sid(self):
        return self._sid

    def set_sid(self, sid):
        self._sid = sid

    def win(self):
        self._record['win'] += 1

    def lose(self):
        self._record['lose'] += 1

    def generate_bingo_card(self):
        self.bingo_card = BingoCard()

    def check_number(self, number):
        return self.bingo_card.check_number(number)

    def check_bingo(self):
        return self.bingo_card.check_bingo()

