import random

class BingoCard:

    def create_card(self):
        numbers = random.sample(range(1, 51), 25)  # 1부터 50까지 중복없이 25개의 숫자를 선택
        for i in range(5):
            for j in range(5):
                self.card[i][j] = numbers[i * 5 + j]


    def __init__(self):
        self.card = [[0] * 5 for _ in range(5)]  # 빙고판
        self.check = [[0] * 5 for _ in range(5)]  # 빙고판 체크

        self.create_card()

    def get_card(self):
        return self.card

    def get_check(self):
        return self.check

    def check_number(self, number):
        for i in range(5):
            for j in range(5):
                if self.card[i][j] == number:
                    self.check[i][j] = 1
                    return

    def check_bingo(self):
        # 가로 빙고 체크
        horizontal_bingo = 0
        for i in range(5):
            if all(self.check[i]):
                horizontal_bingo += 1

        # 세로 빙고 체크
        vertical_bingo = 0
        for j in range(5):
            if all(self.check[i][j] for i in range(5)):
                vertical_bingo += 1

        # 대각선 빙고 체크
        diagonal_bingo = 0
        if all(self.check[i][i] for i in range(5)):
            diagonal_bingo += 1
        if all(self.check[i][4-i] for i in range(5)):
            diagonal_bingo += 1

        total_bingo = horizontal_bingo + vertical_bingo + diagonal_bingo
        return total_bingo >= 2

    def display_card(self):
        for i in range(5):
            for j in range(5):
                print(f'{self.card[i][j]:2}', end=' ')
            print()

    def display_check(self):
        for i in range(5):
            for j in range(5):
                print(f'{self.check[i][j]:2}', end=' ')
            print()
