class GameMatch:
    def __init__(self, id):
        self.id = id
        self.players = {}
        self.tickets = {}
        self.left_ticket = 10
        self.match_complete = False
        # 나중에 리더는 삭제해줘야함
        self.leader = None
        self.leader_sid = None

    def get_players(self):
        return self.players

    def get_id(self):
        return self.id

    def get_leader(self):
        return self.leader

    def get_leader_sid(self):
        return self.leader_sid

    def get_tickets(self):
        return self.tickets

    def is_match_complete(self):
        return self.match_complete

    def game_start(self):
        self.match_complete = True

    def num_of_wating_player(self):
        return len(self.players)

    def add_player(self, sid, player):
        self.players[sid] = player
        self.tickets[sid] = 0
        print(f"{player}is add to match at matching {self.id}")

    def remove_player(self, sid):
        if sid in self.players.keys():
            del self.players[sid]
            print(f"{sid}is remove at match!!!!")
        else:
            print(f"{sid}can't find at match!!!")

    def display_players(self):
        if self.players:
            print("현재 매칭에 참여 중인 플레이어들:")
            for player in self.players:
                print(player)
        else:
            print("매칭에 참여 중인 플레이어가 없습니다.")

    def buy_ticket(self, player_sid):
        if self.tickets[player_sid] > 5: # 5개 이상
            return

        self.tickets[player_sid] += 1
        self.left_ticket -= 1

        # 티켓 다 팔리면 게임 시작해야하는데