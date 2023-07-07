from bingo_card import BingoCard
import mysql.connector


class User:

    def __init__(self, id, nickname, win, lose):
        self.id = id
        self.nickname = nickname
        self.bingo_card = None
        self.sid = None
        self.record = {'win': win, 'lose': lose}
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
        self.update_win_in_db()

    def update_win_in_db(self):
        try:
            conn = mysql.connector.connect(
                host='localhost',
                user='root',
                password='enfj3913',
                database='bingo'
            )
            cursor = conn.cursor()

            # Increase the win count in the database for the user_id
            query = "UPDATE user SET win = win + 1 WHERE user_id = %s"
            values = (self.id,)
            cursor.execute(query, values)
            conn.commit()

            cursor.close()
            conn.close()
        except mysql.connector.Error as error:
            print("Error while updating win count in the database:", error)

    def lose(self):
        self.record['lose'] += 1
        self.update_lose_in_db()

    def update_lose_in_db(self):
        try:
            conn = mysql.connector.connect(
                host='localhost',
                user='root',
                password='enfj3913',
                database='bingo'
            )
            cursor = conn.cursor()

            # Increase the lose count in the database for the user_id
            query = "UPDATE user SET lose = lose + 1 WHERE user_id = %s"
            values = (self.id,)
            cursor.execute(query, values)
            conn.commit()

            cursor.close()
            conn.close()
        except mysql.connector.Error as error:
            print("Error while updating lose count in the database:", error)

    def generate_bingo_card(self):
        self.bingo_card = BingoCard()

    def check_number(self, number):
        return self.bingo_card.check_number(number)

    def check_bingo(self):
        return self.bingo_card.check_bingo()

