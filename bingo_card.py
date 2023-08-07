class BingoCard:
    def __init__(self, num):
        self.cards = []
        self.checks = [[0 for _ in range(5)] for _ in range(num)]
        self.num_of_ticket = num
        
    def get_cards(self):
        return self.cards
    
    def get_checks(self):
        return self.checks
    
    def get_num_of_ticket(self):
        return self.num_of_ticket

    def create_card(self, num_list):
        if len(num_list) != self.num_of_ticket*5:
            raise ValueError("num_list should contain ticket number*5")
        self.cards = [num_list[i:i+5] for i in range(0, len(num_list), 5)]

    def check(self, num):
        for row_idx, row in enumerate(self.cards):
            if num in row:
                col_idx = row.index(num)
                self.checks[row_idx][col_idx] = 1
                return True
        return False

    def check_bingo(self):
        for row in self.checks:
            if all(cell == 1 for cell in row):
                return True
        return False
