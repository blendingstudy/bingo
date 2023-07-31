class GameMatch:
    def __init__(self, id):
        self.id = id
        self.players = {}
        self.match_complete = False
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

    def is_match_complete(self):
        return self.match_complete

    def game_start(self):
        self.match_complete = True

    def num_of_wating_player(self):
        return len(self.players)

    def add_player(self, sid, player):
        # 먼저 들어온 사람이 방장이 되어, 게임시작 권한을 갖게됨.
        if not self.leader:
            self.leader = player
            self.leader_sid = sid
            print(f"{player}is leader at matching {self.id}")
        self.players[sid] = player
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