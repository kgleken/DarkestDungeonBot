Monsters = {
    # Shared
    "Large Corpse": {"hp": [15], "size": 2, "threat": 0, "stun_resist": [200]},
    "Corpse": {"hp": [7], "size": 1, "threat": 0, "stun_resist": [200]},
    "Cultist Brawler": {"hp": [15, 21, 29], "size": 1, "threat": 2, "stun_resist": [25, 45, 65]},
    "Cultist Acolyte": {"hp": [13, 18, 25], "size": 1, "threat": 7, "stun_resist": [25, 45, 65]},
    "Brigand Cutthroat": {"hp": [12, 17, 23], "size": 1, "threat": 2, "stun_resist": [25, 45, 65]},
    "Brigand Fusilier": {"hp": [12, 17, 23], "size": 1, "threat": 2, "stun_resist": [25, 45, 65]},
    "Brigand Bloodletter": {"hp": [35, 49, 68], "size": 2, "threat": 4, "stun_resist": [50, 70, 90]},
    "Brigand Raider": {"hp": [25, 25, 25], "size": 1, "threat": 2, "stun_resist": [72.5, 72.5, 72.5]},
    "Brigand Hunter": {"hp": [25, 25, 25], "size": 1, "threat": 7, "stun_resist": [72.5, 72.5, 72.5]},
    "Madman": {"hp": [14, 20, 27], "size": 1, "threat": 8, "stun_resist": [10, 30, 50]},
    "Maggot": {"hp": [6, 8, 12], "size": 1, "threat": 7, "stun_resist": [100, 120, 140]},
    "Webber": {"hp": [7, 10, 14], "size": 1, "threat": 2, "stun_resist": [25, 45, 60]},
    "Spitter": {"hp": [7, 10, 14], "size": 1, "threat": 3, "stun_resist": [25, 45, 60]},
    "Bone Rabble": {"hp": [8, 11, 16], "size": 1, "threat": 1, "stun_resist": [10, 30, 50]},
    "Ghoul": {"hp": [41, 41, 57], "size": 2, "threat": 5, "stun_resist": [70, 70, 90]},
    "Gargoyle": {"hp": [10, 10, 14], "size": 1, "threat": 1, "stun_resist": [30, 30, 50]},
    "Supplicant": {"hp": [12, 17, 23], "size": 1, "threat": 5, "stun_resist": [150, 170, 190]},
    "Sycophant": {"hp": [12, 17, 23], "size": 1, "threat": 8, "stun_resist": [15, 35, 55]},
    "GateKeeper": {"hp": [12, 17, 23], "size": 1, "threat": 9, "stun_resist": [50, 70, 90]},
    "Chevalier": {"hp": [29, 29, 41], "size": 2, "threat": 6, "stun_resist": [40, 40, 60]},
    "Pliskin": {"hp": [12, 17, 23], "size": 1, "threat": 5, "stun_resist": [25, 45, 65]},
    "Rattler": {"hp": [24, 34, 47], "size": 1, "threat": 4, "stun_resist": [25, 45, 65]},
    "Adder": {"hp": [45, 63, 88], "size": 2, "threat": 6, "stun_resist": [50, 70, 90]},

    # Ruins
    "Bone Soldier": {"hp": [10, 15, 21], "size": 1, "threat": 2, "stun_resist": [25, 45, 70]},
    "Bone Courtier": {"hp": [10, 15, 21], "size": 1, "threat": 7, "stun_resist": [10, 30, 55]},
    "Bone Arbalist": {"hp": [15, 22, 31], "size": 1, "threat": 1, "stun_resist": [10, 30, 55]},
    "Bone Defender": {"hp": [15, 22, 31], "size": 1, "threat": 1, "stun_resist": [25, 45, 70]},
    "Bone Spearman": {"hp": [22, 22, 31], "size": 1, "threat": 4, "stun_resist": [45, 45, 70]},
    "Bone Captain": {"hp": [49, 49, 68], "size": 2, "threat": 5, "stun_resist": [70, 70, 90]},
    "Bone Bearer": {"hp": [45, 45, 45], "size": 1, "threat": 9, "stun_resist": [245, 245, 245]},

    # Bosses
    "Shambler": {"hp": [77, 116, 158], "size": 2, "threat": None, "stun_resist": [100, 120, 140]},
    "Shambler Tentacle": {"hp": [8, 12, 16], "size": 1, "threat": None, "stun_resist": [50, 70, 90]},
    "The Collector": {"hp": [70, 98, 137], "size": 1, "threat": None, "stun_resist": [50, 70, 90]},
    "Collected Highwayman": {"hp": [16, 22, 31], "size": 1, "threat": None, "stun_resist": [25, 45, 65]},
    "Collected Man-at-Arms": {"hp": [16, 22, 31], "size": 1, "threat": None, "stun_resist": [25, 45, 65]},
    "Collected Vestal": {"hp": [16, 22, 31], "size": 1, "threat": None, "stun_resist": [25, 45, 65]},
    "The Fanatic": {"hp": [99, 149, 203], "size": 2, "threat": None, "stun_resist": [45, 65, 90]},
    "Pyre": {"hp": [70, 70, 70], "size": 2, "threat": None, "stun_resist": [200, 220, 245]},
    "Thing From The Stars": {"hp": [106, 148, 191], "size": 2, "threat": None, "stun_resist": [85, 105, 125]},

    "Necromancer": {"hp": [105, 158, 215], "size": 1, "threat": None, "stun_resist": [75, 95, 115]},
    "Prophet": {"hp": [105, 158, 215], "size": 1, "threat": None, "stun_resist": [100, 120, 145]},
    "Small Pew": {"hp": [25, 38, 51], "size": 1, "threat": None, "stun_resist": [200, 220, 245]},
    "Medium Pew": {"hp": [40, 40, 82], "size": 1, "threat": None, "stun_resist": [200, 220, 245]},
    "Large Pew": {"hp": [55, 83, 113], "size": 1, "threat": None, "stun_resist": [200, 220, 245]},
}
