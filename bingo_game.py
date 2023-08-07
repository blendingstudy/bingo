import random
from bingo_card import BingoCard
from bingo_data import BingoData

class BingoGame:
    def __init__(self, game_room_num, players, tickets):
        self.game_room_num = game_room_num
        self.players = players
        self.bingo_cards = self.create_bingo_cards(tickets)
        self.game_over = False
        self.created_random_nums = []

    def create_bingo_cards(self, tickets):
        random_numbers = random.sample(range(1, BingoData.BINGO_MAX_NUMBER + 1), BingoData.BINGO_MAX_NUMBER)  # 10개의 중복 없는 랜덤한 숫자 생성
        bingo_cards = {}
        last_idx = 0
        
        for player_sid, ticket_num in tickets.items():
            bingo_card = BingoCard(ticket_num)
            bingo_card.create_card(random_numbers[last_idx:ticket_num*5])
            last_idx += ticket_num*5

            bingo_cards[player_sid] = bingo_card
            

        return bingo_cards

    def create_random_num(self):
        # 1~50사이 중복없이 랜덤 숫자 발표
        number = random.sample([x for x in range(1, BingoData.BINGO_MAX_NUMBER + 1) if x not in  self.created_random_nums], 1)[0]
        self.random_numbers.append(number)
