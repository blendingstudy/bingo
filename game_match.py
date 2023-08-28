class GameMatch:
    def __init__(self, id):
        self.id = id 
        self.players = {} # 키=player_sid / 값=User.class
        self.tickets = {} # 키=player_sid / 값=구매한 티켓 개수
        self.ticket_list = [0,0,0,0,0,0,0,0,0,0]
        self.left_ticket = 10
        self.waiting = True

    def get_players(self):
        return self.players

    def get_id(self):
        return self.id

    def get_tickets(self):
        return self.tickets
    
    def get_ticket_list(self):
        return self.ticket_list
    
    def get_left_ticket_num(self):
        return self.left_ticket

    def is_waiting(self):
        return self.waiting

    def game_start(self):
        self.waiting = False

    def num_of_wating_player(self):
        return len(self.players)

    # 플레이어 추가
    def add_player(self, sid, player):
        self.players[sid] = player
        self.tickets[sid] = 0
        print(f"{player}is add to match at matching {self.id}")

    # 플레이어 삭제
    def remove_player(self, sid):
        if sid in self.players.keys():
            del self.players[sid]
            del self.tickets[sid]
            print(f"{sid}is remove at match!!!!")
        else:
            print(f"{sid}can't find at match!!!")

    # 티켓 구매
    def buy_ticket(self, player_sid, ticket_id):
        if self.tickets[player_sid] >= 5: # 5개 이하까지만 구매 가능
            return False
        if self.ticket_list[ticket_id]: # 이미 구매된 티켓
            return False

        self.tickets[player_sid] += 1
        self.ticket_list[ticket_id] = 1
        self.left_ticket -= 1

        return True
