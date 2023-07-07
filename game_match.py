class GameMatch:
    def __init__(self, id):
        self.id = id
        self.players = {}

    def get_players(self):
        return self.players

    def get_id(self):
        return self.id

    def add_player(self, player):
        self.players[player.get_nickname()] = player
        print(f"{player}is add to match")

    def remove_player(self, player):
        if player in self.players:
            self.players.remove(player)
            print(f"{player}이(가) 매칭에서 제거되었습니다.")
        else:
            print(f"{player}을(를) 찾을 수 없습니다.")

    def display_players(self):
        if self.players:
            print("현재 매칭에 참여 중인 플레이어들:")
            for player in self.players:
                print(player)
        else:
            print("매칭에 참여 중인 플레이어가 없습니다.")