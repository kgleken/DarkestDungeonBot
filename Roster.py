StartingPartyOrder = None


class Party:
    def __init__(self, roster_info, party_order=None, turn_order=None):
        global StartingPartyOrder

        _heroes = []
        for roster_index, hero in roster_info['heroes'].items():
            hero_data = hero['hero_file_data']['raw_data']['base_root']
            already_moved = \
                next((turn_order[i]['already_moved'] for i, turn in enumerate(turn_order) if 'hero_id' in turn_order[i]
                      and turn_order[i]['hero_id'] == roster_index), None) if turn_order is not None else None
            rank = self.get_rank(roster_index, party_order)
            _heroes.append(Hero(hero_data, roster_index, rank, already_moved))
        self.heroes = _heroes
        self.partyOrder = party_order

        if StartingPartyOrder is None:
            StartingPartyOrder = party_order
        self.startingPartyOrder = StartingPartyOrder

    @staticmethod
    def get_rank(roster_index, party_order):
        for i in range(len(party_order)):  # ex. [3,1,2]
            if party_order[i] == int(roster_index):
                return i + 1
        return 0


class Hero:
    def __init__(self, hero_data, roster_index, rank, already_moved=None):
        self.roster_index = roster_index
        self.name = hero_data['actor']['name']
        self.heroClass = hero_data['heroClass']
        self.resolveLevel = 0  # hero_data['resolveXp'] ??
        self.maxHp = HeroClasses[self.heroClass]['maxHp'][self.resolveLevel]
        self.stress = hero_data['m_Stress']
        self.currentHp = hero_data['actor']['current_hp']
        self.rank = rank
        self.stunned = False if hero_data['actor']['stunned'] == 0 else True
        self.already_moved = already_moved
        buff_group = hero_data['actor']['buff_group']
        self.blightAmount = sum((buff['amount'] for buff in buff_group.values() if buff['stat_type'] == 4), 0)
        self.blightDuration = max(buff['duration'] for buff in buff_group.values() if buff['stat_type'] == 4) \
            if any(buff['stat_type'] == 4 for buff in buff_group.values()) else 0
        self.bleedAmount = sum((buff['amount'] for buff in buff_group.values() if buff['stat_type'] == 5), 0)
        self.bleedDuration = max(buff['duration'] for buff in buff_group.values() if buff['stat_type'] == 5) \
            if any(buff['stat_type'] == 5 for buff in buff_group.values()) else 0
        self.damageOnNextTurn = self.bleedAmount + self.blightAmount
        self.effectiveHp = self.currentHp - self.damageOnNextTurn
        self.percentHp = (self.effectiveHp / self.maxHp) * 100
        self.buff = None
        self.diseases = None
        self.campingSkills = hero_data['skills']['selected_camping_skills']
        self.quirks = hero_data['quirks']
        self.trinkets = None
        self.skills = hero_data['skills']['selected_combat_skills']
        self.traps_skill = HeroClasses[self.heroClass]['traps_base']  # future - take items into account
        self.crimsonCurse = None
        self.darkestDungeon = hero_data['number_of_successful_darkest_dungeon_quests']


HeroClasses = {
    'abomination': {'maxHp': [26, 31, 36, 41, 46], 'traps_base': 10},
    'antiquarian': {'maxHp': [17, 20, 23, 26, 29], 'traps_base': 10},
    'arbalest': {'maxHp': [27, 32, 37, 42, 47], 'traps_base': 10},
    'bounty_hunter': {'maxHp': [25, 30, 35, 40, 45], 'traps_base': 40},
    'crusader': {'maxHp': [33, 40, 47, 54, 61], 'traps_base': 10},
    'grave_robber': {'maxHp': [20, 24, 28, 32, 36], 'traps_base': 50},
    'hellion': {'maxHp': [26, 31, 36, 41, 46], 'traps_base': 20},
    'highwayman': {'maxHp': [23, 28, 33, 38, 43], 'traps_base': 40},
    'houndmaster': {'maxHp': [21, 25, 29, 33, 37], 'traps_base': 40},
    'jester': {'maxHp': [19, 23, 27, 31, 35], 'traps_base': 30},
    'leper': {'maxHp': [35, 42, 49, 56, 63], 'traps_base': 10},
    'man-at-arms': {'maxHp': [31, 37, 43, 49, 55], 'traps_base': 10},
    'occultist': {'maxHp': [19, 23, 27, 31, 35], 'traps_base': 10},
    'plague_doctor': {'maxHp': [22, 26, 30, 34, 38], 'traps_base': 20},
    'vestal': {'maxHp': [24, 29, 34, 39, 44], 'traps_base': 10},
    'flagellant': {'maxHp': [22, 26, 30, 34, 38], 'traps_base': 0},
    'shieldbreaker': {'maxHp': [20, 24, 28, 32, 36], 'traps_base': 20},
}
