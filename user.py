from bingo_card import BingoCard

class User:
    def __init__(self, nickname):
        self._nickname = nickname
        self._bingo_card = None
        self._session_id = None
        self._record = {'win': 0, 'lose': 0}

    def get_nickname(self):
        return self._nickname

    def get_record(self):
        return self._record

    def get_bingo_card(self):
        return self._bingo_card.get_card()

    def get_session_id(self):
        return self._session_id

    def set_session_id(self, session_id):
        self._session_id = session_id

    def win(self):
        self._record['win'] += 1

    def lose(self):
        self._record['lose'] += 1

    def generate_bingo_card(self):
        self._bingo_card = BingoCard()