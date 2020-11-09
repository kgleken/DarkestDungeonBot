"""[0 - ally ranks, 1 - enemy ranks, 2 - stun skill chance or blight damage]"""
AttackSkills = {
    'wicked_slice': [[1, 2, 3], [1, 2]],
    'opened_vein': [[1, 2, 3], [1, 2]],
    'pistol_shot': [[2, 3, 4], [2, 3, 4]],
    'duelist_advance': [[2, 3, 4], [1, 2, 3]],
    'point_blank_shot': [[1], [1]],
    'smite': [[1, 2], [1, 2]],
    'stunning_blow': [[1, 2], [1, 2], [100, 110, 120, 130, 140]],
    'noxious_blast': [[2, 3, 4], [1, 2], [5, 5, 6, 6, 7]],
    'plague_grenade': [[3, 4], [3, 4], [4, 4, 5, 5, 6]],
    'blinding_gas': [[3, 4], [3, 4], [100, 110, 120, 130, 140]],
    'incision': [[1, 2, 3], [1, 2]],
    'battlefield_medicine': [[3, 4], [1, 2, 3, 4]],
    'emboldening_vapors': [[3, 4], [1, 2, 3, 4]],
    'disorienting_blast': [[2, 3, 4], [2, 3, 4], [100, 110, 120, 130, 140]],
    'judgement': [[3, 4], [1, 2, 3, 4]],
    'dazzling_light': [[2, 3, 4], [1, 2, 3], [100, 110, 120, 130, 140]],
    'divine_grace': [[3, 4], [1, 2, 3, 4]],
    'gods_comfort': [[2, 3, 4], [1, 2, 3, 4]],  # divine comfort
    'gods_hand': [[1, 2], [1, 2, 3]],  # hand of light
    'gods_illumination': [[1, 2, 3], [1, 2, 3, 4]],  # illumination
}
