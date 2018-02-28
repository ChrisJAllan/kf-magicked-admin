from web_admin.model.map import Map


class Game(object):
    def __init__(self, game_id):
        self.game_id = game_id
        self.game_mode = ""
        self.difficulty = ""

        self.map_title = ""
        self.map_name = ""

        self.zeds_total = 0
        self.zeds_dead = 0

        self.wave = 0
        self.length = ""

        self.trader_open = False

        self.max_players = 0

        self.map = Map()
