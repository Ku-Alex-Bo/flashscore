from statistics import mean


class Team:
    def __init__(self, ru_title, title, team_id):
        self.ru_title = ru_title
        self.title = title
        self.team_id = team_id

        self.team_corners = []
        self.enemy_corners = []
        self.total_corners = []

    @property
    def avg_team_corners(self):
        return round(mean(self.team_corners[:10]), 2) if self.team_corners else 0.0

    @property
    def avg_enemy_corners(self):
        return round(mean(self.enemy_corners[:10]), 2) if self.enemy_corners else 0.0

    @property
    def avg_total_corners(self):
        return round(mean(self.total_corners[:10]), 2) if self.total_corners else 0.0
