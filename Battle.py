import json
import pydirectinput
from pathlib import Path
import time

from SaveFileReader import SaveFileReader as sfr
from Monsters import Monsters
from Roster import Party
from AttackSkills import AttackSkills
from Controls import Controller, attack_target, swap_hero, heal_target

pydirectinput.FAILSAFE = True
Debug = False
attack_completed = False
SelectedHeroRank = 1
RoundNumber = 0
EnemyTurnOrder = []

BackLineClasses = ['jester', 'vestal', 'plague_doctor', 'arbalest', 'houndmaster']
FrontLineClasses = ['crusader', 'hellion', 'leper', 'flagellant', 'man_at_arms']


def battle(battle_speed_offset, debug):
    global Debug, SelectedHeroRank, RoundNumber, EnemyTurnOrder
    Debug = debug
    c = Controller(debug)
    print('Starting battle algorithm!')
    hero = None
    our_turn_to_move = False

    # wait to make sure character doesn't try to move before battle is loaded
    time.sleep(2.4)
    c.press(c.b, 2, interval=c.interval)  # important, this makes sure the wrong menu isn't selected

    while True:
        try:
            sfr.decrypt_save_info('persist.raid.json')
            f = open(Path(f'{sfr.save_editor_path()}/persist.raid.json'))
            raid_info = json.load(f)['base_root']
            f.close()
        except FileNotFoundError:
            SelectedHeroRank = hero.rank if hero is not None else 1
            break
        if not raid_info['inbattle']:
            SelectedHeroRank = hero.rank if hero is not None else 1
            break

        sfr.decrypt_save_info('persist.roster.json')
        f = open(Path(f'{sfr.save_editor_path()}/persist.roster.json'))
        roster_info = json.load(f)['base_root']
        f.close()

        turn_order = []
        round_number = raid_info['battle']['round']
        initiative = raid_info['battle']['initiative']

        # sort combatants in order of who has highest initiative and track which enemies have moved this round
        if RoundNumber != round_number:
            EnemyTurnOrder = []
            for each_monster in initiative['monsters'].values():
                EnemyTurnOrder.append({'monster_id': str(each_monster['battle_guid']),
                                       'initiative': each_monster['initiative'], 'already_moved': False})
            RoundNumber = round_number

        # determine which heroes have already moved
        for index, each_hero in initiative['heroes'].items():
            hero_id = str(each_hero['roster_guid'])
            hero_data = roster_info['heroes'][hero_id]['hero_file_data']['raw_data']['base_root']
            last_turn = hero_data['actor']['performing_turn']
            stunned = False if hero_data['actor']['stunned'] == 0 else True
            buff_group = hero_data['actor']['buff_group']
            stun_recovery_buff = True if any(buff['id'] == 'STUNRECOVERYBUFF' for buff in buff_group.values()) \
                else False
            # Warning - not confirmed, possible rare bug with turn order not being properly updated for heroes
            #   in save file. May need to manually track each hero that moves per round like with enemies
            turn_order.append({'hero_id': hero_id, 'initiative': each_hero['initiative'],
                               'already_moved': (round_number == last_turn) or
                                                (not stunned and stun_recovery_buff
                                                 and round_number == last_turn + 1) or
                                                (round_number == last_turn + 2 and stunned and stun_recovery_buff)})
        turn_order.extend(EnemyTurnOrder)
        turn_order.sort(key=lambda k: k['initiative'], reverse=True)

        # check if it is our turn to move
        hero_to_move = None
        for i, turn in enumerate(turn_order):
            if 'hero_id' in turn_order[i] and not turn_order[i]['already_moved']:
                hero_to_move = turn_order[i]['hero_id']
                our_turn_to_move = True
                break
            elif 'monster_id' in turn_order[i] and not turn_order[i]['already_moved']:
                monster_id = turn_order[i]['monster_id']
                for index, enemy_turn in enumerate(EnemyTurnOrder):
                    if monster_id == EnemyTurnOrder[index]['monster_id']:
                        EnemyTurnOrder[index]['already_moved'] = True
                time.sleep(3.8 - battle_speed_offset)  # wait for enemy turn to finish & battle to end
                break

        if our_turn_to_move:
            # use torch if less than 50% and not shambler (future - or 75% for sun trinkets)
            # torchlight = 0 if raid_info['torchlight'] == 0 else (raid_info['torchlight'] / 131072) - 8448
            # if torchlight < 50:
            #     pydirectinput.write(c.torch)  # need to use 'write' instead of 'press' for torch

            party_order = raid_info['party']['heroes']  # [front - back]
            party = Party(roster_info, party_order, turn_order).heroes
            our_turn_to_move = False
            hero = next((hero for hero in party if hero.roster_index == hero_to_move), None)
            take_battle_action(raid_info, party, hero, turn_order)
            time.sleep(3.5 - battle_speed_offset)  # give hero attack animation & battle time to end


def take_battle_action(raid_info, party, hero, turn_order):
    print('Taking battle action!')
    enemy_formation = get_enemy_formation(raid_info, turn_order)

    hero_class = hero.heroClass
    party.sort(key=lambda k: k.rank)  # sort by rank

    if hero_class == 'highwayman':
        highwayman_action(party, hero, raid_info, enemy_formation)
    elif hero_class == 'crusader':
        crusader_action(party, hero, raid_info, enemy_formation)
    elif hero_class == 'plague_doctor':
        plague_doctor_action(party, hero, raid_info, enemy_formation)
    elif hero_class == 'vestal':
        vestal_action(party, hero, raid_info, enemy_formation)


def vestal_attack_helper(hero, list_of_enemies, stun_chance, kill_stunned_enemy, cant_kill_enemy=False):
    attack, potential_targets = None, None
    if 'judgement' in hero.skills and (hero.rank == 3 or hero.rank == 4) \
            and any(enemy.canBeKilledIn1Hit and (not enemy.stunned or (enemy.stunned and kill_stunned_enemy))
                    for enemy in list_of_enemies):
        attack = 'judgement'
        potential_targets = list_of_enemies
    elif 'dazzling_light' in hero.skills \
            and any((1 in enemy.rank or 2 in enemy.rank or 3 in enemy.rank)
                    and stun_chance - enemy.stunResist > 50 and not enemy.stunned for enemy in list_of_enemies):
        attack = 'dazzling_light'
        potential_targets = list_of_enemies
    elif 'judgement' in hero.skills and cant_kill_enemy:
        attack = 'judgement'
        potential_targets = list_of_enemies
    return attack, potential_targets


def vestal_heal_helper(hero, party, enemies_not_dead_already, single_heal_thresh, multi_heal_thresh):
    """ Assumes percent hp threshold for when to use divine grace is lower than divine comfort """
    attack, target = None, None
    # if one ally hp percentage is less than divine_grace_thresh
    party.sort(key=lambda k: k.percentHp)
    ally = next((ally for ally in party
                 if ally.percentHp < single_heal_thresh and ally.currentHp < ally.maxHp
                 and ally.damageOnNextTurn < ally.maxHp), None)
    if ally is not None:
        # determine whether to use multi-target heal (divine comfort) or single target heal (divine grace)
        if 'gods_comfort' in hero.skills and (sum(hero.percentHp < multi_heal_thresh for hero in party) > 2
                                              or sum(hero.percentHp < 30 for hero in party) > 1):
            attack = 'gods_comfort'
        elif 'judgement' in hero.skills and ally is hero and len(enemies_not_dead_already) > 1:
            attack = 'judgement'
        elif 'divine_grace' in hero.skills and hero.rank == 3 or hero.rank == 4:
            attack = 'divine_grace'
            target = ally
    return attack, target


def vestal_action(party_sorted_by_rank, hero, raid_info, enemy_formation):
    """[ Ideal skill load-out: judgement, dazzling light, divine grace, divine comfort ]"""
    # current_round = raid_info['battle']['round']
    party = party_sorted_by_rank
    list_of_attacks = ['judgement', 'gods_hand', 'gods_illumination']
    attack, target, stun_chance = None, None, None
    enemies_not_dead_already, high_threat_enemies, very_high_threat_enemies = [], [], []
    very_high_threat_not_moved, high_threat_not_moved, potential_targets = [], [], []

    if hero.rank == 1:
        attack = 'swap'
    elif hero.rank == 2 or hero.rank == 3 or hero.rank == 4:

        for each_enemy in enemy_formation:
            if not each_enemy.alreadyGoingToDie:
                enemies_not_dead_already.append(each_enemy)
        for each_enemy in enemies_not_dead_already:
            if each_enemy.threat >= 4:
                high_threat_enemies.append(each_enemy)
        for each_enemy in high_threat_enemies:
            if each_enemy.threat >= 7:
                very_high_threat_enemies.append(each_enemy)
            if each_enemy.name == 'Bone Arbalist' and (3 in each_enemy.rank or 4 in each_enemy.rank):
                very_high_threat_enemies.append(each_enemy)
        for each_enemy in very_high_threat_enemies:
            if not each_enemy.alreadyMoved:
                very_high_threat_not_moved.append(each_enemy)
        for each_enemy in high_threat_enemies:
            if not each_enemy.alreadyMoved:
                high_threat_not_moved.append(each_enemy)

        if 'dazzling_light' in hero.skills:
            stun_level = hero.skills['dazzling_light']
            stun_chance = AttackSkills['dazzling_light'][2][stun_level]

        # ally is on death's door or going to die from poison or bleed (less than 1% effective hp)
        if attack is None:
            multi_thresh = 30 if 'gods_comfort' in hero.skills else 100
            attack, target = vestal_heal_helper(hero, party, enemies_not_dead_already, single_heal_thresh=1,
                                                multi_heal_thresh=multi_thresh)

        # can kill or stun very high threat enemies that haven't moved yet (>=7) and multiple enemies left
        if attack is None and len(enemies_not_dead_already) >= 1 and len(very_high_threat_not_moved) > 0:
            attack, potential_targets \
                = vestal_attack_helper(hero, very_high_threat_not_moved, stun_chance, kill_stunned_enemy=False)

        # one ally < 30% hp or multiple allies < 50% hp
        if attack is None:
            multi_thresh = 50 if 'gods_comfort' in hero.skills else 100
            attack, target = vestal_heal_helper(hero, party, enemies_not_dead_already, single_heal_thresh=30,
                                                multi_heal_thresh=multi_thresh)

        # can kill or stun very high threat enemies that haven't moved yet (>=7)
        if attack is None and len(very_high_threat_not_moved) > 0:
            attack, potential_targets \
                = vestal_attack_helper(hero, very_high_threat_not_moved, stun_chance, kill_stunned_enemy=False)

        # one ally < 50% hp or multiple allies < 70% hp
        if attack is None:
            multi_thresh = 70 if 'gods_comfort' in hero.skills else 100
            attack, target = vestal_heal_helper(hero, party, enemies_not_dead_already, single_heal_thresh=50,
                                                multi_heal_thresh=multi_thresh)

        # can kill or stun high threat enemies that haven't moved yet (>=4)
        if attack is None and len(high_threat_not_moved) > 0:
            attack, potential_targets \
                = vestal_attack_helper(hero, high_threat_not_moved, stun_chance, kill_stunned_enemy=False)

        # can kill or stun very high threat enemies (>=7)
        if attack is None and len(very_high_threat_enemies) > 0:
            attack, potential_targets \
                = vestal_attack_helper(hero, very_high_threat_enemies, stun_chance, kill_stunned_enemy=False)

        # swap if rank 2, can't stun, and (not back line hero in rank 3 or no rank 2 heal skill)
        if attack is None and hero.rank == 2:
            if 'dazzling_light' not in hero.skills or 'gods_comfort' not in hero.skills \
                    or (not any((1 in enemy.rank or 2 in enemy.rank or 3 in enemy.rank)
                                and stun_chance - enemy.stunResist > 50 and not enemy.stunned
                                for enemy in enemies_not_dead_already)
                        and party[2].heroClass not in BackLineClasses
                        and not (party[2].heroClass == 'crusader'
                                 and any(2 in enemy.rank or 3 in enemy.rank
                                         or 4 in enemy.rank for enemy in enemies_not_dead_already))):
                attack = 'swap'

        # can kill or stun high threat enemies (>=4)
        if attack is None and len(high_threat_enemies) > 0:
            attack, potential_targets \
                = vestal_attack_helper(hero, high_threat_enemies, stun_chance, kill_stunned_enemy=True)

        # one ally < 60% hp or multiple allies < 80% hp
        if attack is None:
            multi_thresh = 80 if 'gods_comfort' in hero.skills else 100
            attack, target = vestal_heal_helper(hero, party, enemies_not_dead_already, single_heal_thresh=60,
                                                multi_heal_thresh=multi_thresh)

        # one ally < 70% hp or multiple allies < 90% hp
        if attack is None:
            multi_thresh = 90 if 'gods_comfort' in hero.skills else 100
            attack, target = vestal_heal_helper(hero, party, enemies_not_dead_already, single_heal_thresh=70,
                                                multi_heal_thresh=multi_thresh)

        # more than one weak enemy left and party > 90% hp
        if attack is None and len(enemies_not_dead_already) > 1 and not any(ally.percentHp < 90 for ally in party):
            attack, potential_targets \
                = vestal_attack_helper(hero, enemies_not_dead_already, stun_chance,
                                       kill_stunned_enemy=False, cant_kill_enemy=True)

        # one ally < 100% hp or multiple allies < 100% hp
        if attack is None:
            attack, target = vestal_heal_helper(hero, party, enemies_not_dead_already, single_heal_thresh=100,
                                                multi_heal_thresh=100)

        # can stun enemy
        if attack is None:
            if 'dazzling_light' in hero.skills and any(stun_chance - enemy.stunResist > 50 and not enemy.stunned
                                                       for enemy in enemies_not_dead_already):
                attack = 'dazzling_light'
                potential_targets = enemies_not_dead_already

        # default to heal skill if doesn't have judgement
        if attack is None and 'judgement' not in hero.skills:
            if 'gods_comfort' in hero.skills:
                attack = 'gods_comfort'
            elif 'divine_grace' in hero.skills and hero.rank != 2:
                attack = 'divine_grace'
                party.sort(key=lambda k: k.stress, reverse=True)
                target = party[0]  # highest stress ally
            else:
                attack = 'swap'

    if attack == 'swap':
        swap_hero(hero, swap_distance=-1, debug=Debug)
    elif attack == 'dazzling_light':
        find_target_and_stun(hero, potential_targets, attack, stun_chance)
    elif attack == 'gods_comfort' or attack == 'divine_grace':
        heal_target(hero, target, attack, Debug)
    else:
        # Find target and attack enemy
        if attack is not None:
            list_of_attacks.insert(0, attack)
        find_target_and_attack(enemy_formation, hero, list_of_attacks)


def plague_doctor_attack_helper(hero, list_of_enemies):
    attack, stun_chance = None, None
    blinding_stun_chance, disorienting_stun_chance, noxious_poison_dmg, plague_poison_dmg = None, None, None, None

    if 'blinding_gas' in hero.skills:  # future - add battle counter for max number of uses
        blinding_stun_level = hero.skills['blinding_gas']
        blinding_stun_chance = AttackSkills['blinding_gas'][2][blinding_stun_level]
    if 'disorienting_blast' in hero.skills:
        disorienting_stun_level = hero.skills['disorienting_blast']
        disorienting_stun_chance = AttackSkills['disorienting_blast'][2][disorienting_stun_level]
    if 'noxious_blast' in hero.skills:
        noxious_skill_level = hero.skills['noxious_blast']
        noxious_poison_dmg = AttackSkills['noxious_blast'][2][noxious_skill_level]
    if 'plague_grenade' in hero.skills:
        plague_skill_level = hero.skills['plague_grenade']
        plague_poison_dmg = AttackSkills['plague_grenade'][2][plague_skill_level]

    # prioritize targets in the back ranks first
    for enemy in reversed(list_of_enemies):
        # can kill enemy in rank 3 or 4
        if (3 in enemy.rank or 4 in enemy.rank) and not enemy.stunned \
                and 'plague_grenade' in hero.skills and enemy.effectiveHp <= plague_poison_dmg + 1:
            attack = 'plague_grenade'
            break
        # can stun enemy in rank 3 or 4
        if (3 in enemy.rank or 4 in enemy.rank) and not enemy.stunned:
            if 'disorienting_blast' in hero.skills and disorienting_stun_chance - enemy.stunResist > 50:
                attack = 'disorienting_blast'
                stun_chance = disorienting_stun_chance
                break
            if 'blinding_gas' in hero.skills and blinding_stun_chance - enemy.stunResist > 50:
                attack = 'blinding_gas'
                stun_chance = blinding_stun_chance
                break
        # can kill enemy in rank 1 or 2
        if (1 in enemy.rank or 2 in enemy.rank) and not enemy.stunned:
            if 'noxious_blast' in hero.skills and enemy.effectiveHp <= noxious_poison_dmg + 1:
                attack = 'noxious_blast'
                break
            if 'incision' in hero.skills and not enemy.isTank and enemy.percentHpRemain <= 40:
                attack = 'incision'
                break
        # can stun enemy in rank 2
        if 2 in enemy.rank and not enemy.alreadyMoved and not enemy.stunned:
            if 'disorienting_blast' in hero.skills and disorienting_stun_chance - enemy.stunResist > 50:
                attack = 'disorienting_blast'
                stun_chance = disorienting_stun_chance
                break
    return attack, stun_chance, list_of_enemies


def plague_doctor_action(party_sorted_by_rank, hero, raid_info, enemy_formation):
    """[ Ideal skill load-out: noxious_blast,
            any 3 - plague_grenade, battlefield_medicine, blinding_gas, disorienting_blast ]"""
    global attack_completed
    # current_round = raid_info['battle']['round']
    party = party_sorted_by_rank
    list_of_attacks = ['plague_grenade', 'noxious_blast', 'incision']
    attack, stun_chance, target = None, None, None
    swap_distance = -1
    enemies_not_dead_already, high_threat_enemies, very_high_threat_enemies = [], [], []
    very_high_threat_not_moved, high_threat_not_moved = [], []
    potential_targets = enemy_formation

    for each_enemy in enemy_formation:
        if not each_enemy.alreadyGoingToDie:
            enemies_not_dead_already.append(each_enemy)
    for each_enemy in enemies_not_dead_already:
        if each_enemy.threat >= 4:
            high_threat_enemies.append(each_enemy)
    for each_enemy in high_threat_enemies:
        if each_enemy.threat >= 7:
            very_high_threat_enemies.append(each_enemy)
    for each_enemy in very_high_threat_enemies:
        if not each_enemy.alreadyMoved:
            very_high_threat_not_moved.append(each_enemy)
    for each_enemy in high_threat_enemies:
        if not each_enemy.alreadyMoved:
            high_threat_not_moved.append(each_enemy)

    blinding_stun_chance, disorienting_stun_chance, plague_poison_dmg = None, None, None
    if 'blinding_gas' in hero.skills:  # future - add battle counter for max number of uses
        blinding_stun_level = hero.skills['blinding_gas']
        blinding_stun_chance = AttackSkills['blinding_gas'][2][blinding_stun_level]
    if 'disorienting_blast' in hero.skills:
        disorienting_stun_level = hero.skills['disorienting_blast']
        disorienting_stun_chance = AttackSkills['disorienting_blast'][2][disorienting_stun_level]
    if 'plague_grenade' in hero.skills:
        plague_skill_level = hero.skills['plague_grenade']
        plague_poison_dmg = AttackSkills['plague_grenade'][2][plague_skill_level]

    if hero.rank == 1:
        if 'incision' in hero.skills:
            if party[1].heroClass not in BackLineClasses:
                attack = 'swap'
            elif party[1].heroClass in BackLineClasses:
                attack = 'incision'
    elif hero.rank == 2:
        enemy_in_rank2 = True if (len(enemy_formation) == 1 and 2 in enemy_formation[0].rank) \
                                 or len(enemy_formation) > 1 else False
        # future - use disorienting blast if appropriate and don't need to switch right away
        if party[2].heroClass == 'highwayman' or party[2].heroClass == 'shield_breaker' \
                or (party[2].heroClass == 'crusader' and enemy_in_rank2):
            attack = 'noxious_blast'
        else:
            attack = 'swap' if party[2].heroClass not in BackLineClasses else None
    elif hero.rank == 3 or hero.rank == 4:
        rank3_enemy = next((enemy for enemy in enemy_formation if 3 in enemy.rank), None)
        rank4_enemy = next((enemy for enemy in enemy_formation if 4 in enemy.rank and enemy is not rank3_enemy), None)

        # two enemies on ranks 3 & 4 and at least 1 very high threat or skeleton archer
        if rank3_enemy is not None and rank4_enemy is not None:
            back_rank_targets = [rank3_enemy, rank4_enemy]
            priority_target = next((enemy for enemy in back_rank_targets
                                    if (enemy.threat >= 7 or enemy.name == 'Bone Arbalist')
                                    and not enemy.alreadyGoingToDie and not enemy.alreadyMoved), None)
            if priority_target is None:
                priority_target = next((enemy for enemy in back_rank_targets
                                        if (enemy.threat >= 7 or enemy.name == 'Bone Arbalist')
                                        and not enemy.alreadyGoingToDie), None)
            if priority_target is not None and not rank3_enemy.alreadyGoingToDie and not rank4_enemy.alreadyGoingToDie:
                # can stun the priority target with blinding gas and possibly another
                if 'blinding_gas' in hero.skills and not rank3_enemy.stunned and not rank4_enemy.stunned \
                            and (blinding_stun_chance - priority_target.stunResist > 50):
                    attack = 'blinding_gas'
                    stun_chance = blinding_stun_chance
                    target = priority_target
                # can hit priority target and another with plague grenade
                elif 'plague_grenade' in hero.skills:
                    attack = 'plague_grenade'

        # can kill or stun a very high threat enemy that hasn't moved (>= 7)
        if attack is None and len(very_high_threat_not_moved) > 0:
            attack, stun_chance, potential_targets = plague_doctor_attack_helper(hero, very_high_threat_not_moved)

        # can kill or stun a very high threat enemy (>= 7)
        if attack is None and len(very_high_threat_enemies) > 0:
            attack, stun_chance, potential_targets = plague_doctor_attack_helper(hero, very_high_threat_enemies)

        # can pull or stun a skeleton archer on rank 3 or 4
        if attack is None:
            skeleton_archer = next((enemy for enemy in enemies_not_dead_already if enemy.name == 'Bone Arbalist'
                                    and (3 in enemy.rank or 4 in enemy.rank) and not enemy.alreadyMoved), None)
            if skeleton_archer is None:
                skeleton_archer = next((enemy for enemy in enemies_not_dead_already if enemy.name == 'Bone Arbalist'
                                        and (3 in enemy.rank or 4 in enemy.rank)), None)
            if skeleton_archer is not None:
                if 'disorienting_blast' in hero.skills:
                    attack = 'disorienting_blast'
                    stun_chance = disorienting_stun_chance
                    target = skeleton_archer
                elif 'blinding_gas' in hero.skills and blinding_stun_chance - skeleton_archer.stunResist > 50 \
                        and not skeleton_archer.stunned:
                    attack = 'blinding_gas'
                    stun_chance = blinding_stun_chance

        # two enemies on ranks 3 & 4
        if attack is None and rank3_enemy is not None and rank4_enemy is not None \
                and not rank3_enemy.alreadyGoingToDie and not rank4_enemy.alreadyGoingToDie:
            # can stun two enemies with blinding gas
            if 'blinding_gas' in hero.skills and not rank3_enemy.stunned and not rank4_enemy.stunned \
                        and (blinding_stun_chance - rank3_enemy.stunResist > 50
                             or blinding_stun_chance - rank4_enemy.stunResist > 50):
                attack = 'blinding_gas'
                stun_chance = blinding_stun_chance
            # can kill one of them
            elif 'plague_grenade' in hero.skills and (rank3_enemy.effectiveHp <= plague_poison_dmg + 1
                                                      or rank4_enemy.effectiveHp <= plague_poison_dmg + 1):
                attack = 'plague_grenade'

        # can kill or stun a high threat enemy that hasn't moved (>= 4)
        if attack is None and len(high_threat_not_moved) > 0:
            attack, stun_chance, potential_targets = plague_doctor_attack_helper(hero, high_threat_not_moved)

        # can kill or stun a high threat enemy (>= 4)
        if attack is None and len(high_threat_enemies) > 0:
            attack, stun_chance, potential_targets = plague_doctor_attack_helper(hero, high_threat_enemies)

        # can kill or stun enemy
        if attack is None and len(enemies_not_dead_already) > 0:
            attack, stun_chance, potential_targets = plague_doctor_attack_helper(hero, enemies_not_dead_already)

        # swap if beneficial
        if attack is None and hero.rank == 3 and party[3].heroClass != 'vestal':
            attack = 'swap'

        # cure bleed/blight
        if attack is None and 'battlefield_medicine' in hero.skills and len(very_high_threat_enemies) == 0:
            heal_targets = list(hero for hero in party if hero.bleedAmount > 0 or hero.blightAmount > 0)
            if len(heal_targets) > 0:
                heal_targets.sort(key=lambda k: k.bleedAmount * k.bleedDuration + k.blightAmount * k.blightDuration,
                                  reverse=True)
                target = heal_targets[0]
                attack = 'battlefield_medicine'

    if attack == 'swap':
        swap_hero(hero, swap_distance, debug=Debug)
    elif attack == 'blinding_gas' or attack == 'disorienting_blast':
        find_target_and_stun(hero, potential_targets, attack, stun_chance, target)
    elif attack == 'battlefield_medicine':
        heal_target(hero, target, attack, Debug)
    else:
        # Find target and attack enemy
        if attack is not None:
            list_of_attacks.insert(0, attack)
        find_target_and_attack(potential_targets, hero, list_of_attacks)

    # heal, buff, or swap if can't hit enemies with any attacks
    if not attack_completed and attack != 'swap' and attack != 'blinding_gas' and attack != 'disorienting_blast' \
            and attack != 'battlefield_medicine':
        if 'battlefield_medicine' in hero.skills and hero.rank == 3 or hero.rank == 4:
            attack = 'battlefield_medicine'
            party.sort(key=lambda k: k.effectiveHp)
            heal_target(hero, party[0], attack, Debug)
        elif 'emboldening_vapors' in hero.skills:
            attack = 'emboldening_vapors'
            target = next(hero for hero in party if hero.heroClass == 'vestal')
            heal_target(hero, target, attack, Debug)
        else:
            if hero.rank == 4:
                swap_distance = 1
            elif (hero.rank == 1 and party[1].heroClass in BackLineClasses) \
                    or (hero.rank == 2 and party[2].heroClass in BackLineClasses):
                swap_distance = 0
            swap_hero(hero, swap_distance, debug=Debug)


def highwayman_action(party_sorted_by_rank, hero, raid_info, enemy_formation):
    """[ Ideal skill load-out: wicked slice, pistol shot, duelists advance, point blank shot ]"""
    current_round = raid_info['battle']['round']
    party = party_sorted_by_rank
    list_of_attacks = ['wicked_slice', 'opened_vein', 'pistol_shot']
    attack = None
    swap_distance = 1

    enemies_not_dead_already = []
    for each_enemy in enemy_formation:
        if not each_enemy.alreadyGoingToDie:
            enemies_not_dead_already.append(each_enemy)

    # stall if only one weak enemy left and need to heal or stress heal
    if len(enemies_not_dead_already) <= 1 and current_round < 5 \
            and any(hero.heroClass == 'vestal' for hero in party) and any(hero.percentHp < 90 for hero in party):
        if len(enemies_not_dead_already) == 1:
            enemy = enemies_not_dead_already[0]
            if hero.rank == 3 and party[1].heroClass in BackLineClasses \
                    or ((enemy.threat < 4 or enemy.stunned) and ((not enemy.isTank and enemy.effectiveHp != enemy.maxHp)
                                                                 or (enemy.isTank and enemy.canBeKilledIn1Hit))):
                attack = 'swap'
                swap_distance = -1 if hero.rank == 1 else 1
        else:
            attack = 'swap'
            swap_distance = -1 if hero.rank == 1 else 1
    elif hero.rank == 1:
        # point blank shot if high threat enemy in rank 3 or 4 unless rank 2 is back line hero
        if party[1].heroClass not in BackLineClasses or party[1].heroClass != 'highwayman':
            attack = 'point_blank_shot' if any(enemy.threat >= 7 and (3 in enemy.rank or 4 in enemy.rank)
                                               for enemy in enemies_not_dead_already) else attack
    elif hero.rank == 2:
        if len(enemy_formation) > 1 or 2 in enemy_formation[0].rank:
            # duelist's advance if party out of position
            attack = 'duelist_advance' if party[0].heroClass in BackLineClasses else attack
            # if no high threat enemy in rank 3 or 4
            if not any(enemy.threat >= 7 and (3 in enemy.rank or 4 in enemy.rank) for enemy in enemy_formation):
                # duelist's advance if at least 3 enemies left, and can kill 1 of them with it
                if len(enemy_formation) >= 3:
                    if any((enemy.isTank and enemy.percentHpRemain <= 10)
                           or (not enemy.isTank and enemy.percentHpRemain <= 30) for enemy in enemy_formation):
                        attack = 'duelist_advance'
                    # duelist's advance if at least 3 enemies left, and can't kill 1 of them with slice
                    elif not any(enemy.canBeKilledIn1Hit for enemy in enemy_formation):
                        attack = 'duelist_advance'
        elif party[0].heroClass in BackLineClasses:
            attack = 'swap'
    elif hero.rank == 3:
        if len(enemy_formation) > 1 or 2 in enemy_formation[0].rank:
            # duelist's advance if party out of position
            attack = 'duelist_advance' if party[1].heroClass in BackLineClasses else attack
            # duelist's advance if no high threat enemy in rank 4 and not bad for position
            attack = 'duelist_advance' \
                if not any(enemy.threat >= 7 and 4 in enemy.rank and len(enemy.rank) > 1 for enemy in enemy_formation) \
                and party[1].heroClass not in FrontLineClasses and party[0].heroClass not in BackLineClasses else attack
        elif party[1].heroClass in BackLineClasses:
            attack = 'swap'
    elif hero.rank == 4:
        if len(enemy_formation) > 1 or 2 in enemy_formation[0].rank:
            # duelist's advance if not front line ally in rank 3
            attack = 'duelist_advance' \
                if not party[2].heroClass in FrontLineClasses or party[2].heroClass == 'highwayman' or \
                party[2].heroClass == 'shieldbreaker' else attack
        elif len(enemy_formation) == 1:
            attack = 'swap'

    if attack == 'swap':
        swap_hero(hero, swap_distance, debug=Debug)
    else:
        # Find target and attack enemy
        if attack is not None:
            list_of_attacks.insert(0, attack)
        find_target_and_attack(enemy_formation, hero, list_of_attacks)


def crusader_action(party_sorted_by_rank, hero, raid_info, enemy_formation):
    """[ Ideal skill load-out: smite, stunning blow, holy lance, inspiring cry ]"""
    # future - add stress healing with inspiring cry
    current_round = raid_info['battle']['round']
    party = party_sorted_by_rank
    list_of_attacks = ['smite']
    attack, stun_chance, target = None, None, None
    swap_distance = 1

    if 'stunning_blow' in hero.skills:
        stun_level = hero.skills['stunning_blow']
        stun_chance = AttackSkills['stunning_blow'][2][stun_level]

    enemies_not_dead_already = []
    for each_enemy in enemy_formation:
        if not each_enemy.alreadyGoingToDie:
            enemies_not_dead_already.append(each_enemy)

    # stall if only one weak enemy left and need to heal or stress heal
    if len(enemies_not_dead_already) <= 1 and current_round < 5 \
            and any(hero.heroClass == 'vestal' for hero in party) and any(hero.percentHp < 90 for hero in party):
        if (hero.rank == 1 or hero.rank == 2) and len(enemies_not_dead_already) == 1:
            enemy = enemies_not_dead_already[0]
            can_stun = stun_chance - enemy.stunResist > 50
            if enemy.threat >= 4 and not can_stun and (1 in enemy.rank or 2 in enemy.rank):
                attack = 'smite'
            elif (enemy.effectiveHp == enemy.maxHp or (enemy.threat >= 4 and can_stun)
                  or (enemy.isTank and not enemy.canBeKilledIn1Hit)) and (1 in enemy.rank or 2 in enemy.rank):
                attack = 'stunning_blow'
                target = enemy
            else:
                attack = 'swap' if hero.rank == 2 or (hero.rank == 1 and party[1].heroClass not in BackLineClasses) \
                    else None
                swap_distance = -1 if hero.rank == 1 and party[1].heroClass not in BackLineClasses else 1
        elif (hero.rank == 3 or hero.rank == 4) or len(enemies_not_dead_already) == 0:
            attack = 'swap'
            swap_distance = -1 if hero.rank == 1 else 1
    elif (hero.rank == 1 or hero.rank == 2) and 'stunning_blow' in hero.skills:
        high_threat_enemies = []
        for i in range(2 if len(enemy_formation) > 2 else len(enemy_formation)):
            if enemy_formation[i].threat >= 4 and enemy_formation[i] in enemies_not_dead_already:
                high_threat_enemies.append(enemy_formation[i])

        # if high threat enemy, stun if can't kill
        if len(high_threat_enemies) > 0:
            attack = 'stunning_blow' \
                if any(stun_chance - enemy.stunResist > 50 and not enemy.stunned
                       and (enemy.effectiveHp == enemy.maxHp or (enemy.isTank and not enemy.canBeKilledIn1Hit))
                       for enemy in high_threat_enemies) else attack
        # stun enemy if can't kill
        elif any(stun_chance - enemy.stunResist > 50 and not enemy.stunned
                 and (enemy.effectiveHp == enemy.maxHp or (enemy.isTank and not enemy.canBeKilledIn1Hit))
                 for enemy in high_threat_enemies):
            attack = 'stunning_blow'
    elif hero.rank == 3 or hero.rank == 4:
        # holy lance if rank 3 or 4, and not front line on next rank, and enemy on rank 2
        if party[hero.rank-2].heroClass not in FrontLineClasses:
            if any(2 in enemy.rank for enemy in enemy_formation):
                attack = 'holy_lance' if 'holy_lance' in hero.skills else 'swap'
            elif not any(2 in enemy.rank for enemy in enemy_formation):
                attack = 'swap'
        else:
            attack = 'swap'
            # inspiring cry if high threat enemies are dead and any hero more than 5 stress
            # attack = 'inspiring_cry'

    if attack == 'swap':
        swap_hero(hero, swap_distance, debug=Debug)
    elif attack == 'stunning_blow':
        find_target_and_stun(hero, enemies_not_dead_already, attack, stun_chance, target)
    else:
        # Find target and attack enemy
        if attack is not None:
            list_of_attacks.insert(0, attack)
        find_target_and_attack(enemy_formation, hero, list_of_attacks)


def find_target_and_attack(enemy_formation, hero, list_of_attacks):
    global attack_completed
    attack_completed = False

    # filter out skills if hero is not in the correct rank or does not have equipped
    viable_attacks = [attack for attack in list_of_attacks
                      if attack in hero.skills and hero.rank in AttackSkills[attack][0]]

    # if enemy is a very high threat (>=7, stress attacker) and not going to die already
    if not attack_completed:
        targets = []
        for each_enemy in enemy_formation:
            if each_enemy.threat >= 7 and not each_enemy.alreadyGoingToDie:
                targets.append(each_enemy)
        if len(targets) > 0:
            sort_targets(targets)
            choose_best_attack(hero, targets, viable_attacks)
    # if enemy isn't stunned, can be killed in one hit, isn't going to die from blight or bleed
    if not attack_completed:
        targets = []
        for each_enemy in enemy_formation:
            if not each_enemy.stunned and not each_enemy.alreadyGoingToDie and each_enemy.canBeKilledIn1Hit \
                    and each_enemy.threat > 0:
                targets.append(each_enemy)
        if len(targets) > 0:
            sort_targets(targets)
            choose_best_attack(hero, targets, viable_attacks)
    # if enemy is a high threat (>=4, high threat) and not going to die already
    if not attack_completed:
        targets = []
        for each_enemy in enemy_formation:
            if each_enemy.threat >= 4 and not each_enemy.alreadyGoingToDie:
                targets.append(each_enemy)
        if len(targets) > 0:
            sort_targets(targets)
            choose_best_attack(hero, targets, viable_attacks)
    # if corpse in rank 1 or 2 and enemy in rank 3 is skeleton archer
    if not attack_completed:
        targets = []
        if any(enemy.name == 'Bone Arbalist' and not enemy.alreadyGoingToDie for enemy in enemy_formation):
            if len(enemy_formation) > 2 and 'Bone Arbalist' == enemy_formation[2].name:
                if 'Corpse' == enemy_formation[0].name or 'Large Corpse' == enemy_formation[0].name:
                    targets.append(enemy_formation[0])
                if 'Corpse' == enemy_formation[1].name or 'Large Corpse' == enemy_formation[1].name:
                    targets.append(enemy_formation[1])
            elif 'Large Corpse' == enemy_formation[0].name and 'Bone Arbalist' == enemy_formation[1].name:
                targets.append(enemy_formation[0])
        if len(targets) > 0:
            sort_targets(targets)
            choose_best_attack(hero, targets, viable_attacks)
    # if enemy isn't stunned, and isn't going to die from blight or bleed
    if not attack_completed:
        targets = []
        for each_enemy in enemy_formation:
            if not each_enemy.stunned and not each_enemy.alreadyGoingToDie and each_enemy.threat > 0:
                targets.append(each_enemy)
        if len(targets) > 0:
            sort_targets(targets)
            choose_best_attack(hero, targets, viable_attacks)
    # if isn't going to die from blight or bleed
    if not attack_completed:
        targets = []
        for each_enemy in enemy_formation:
            if not each_enemy.alreadyGoingToDie and each_enemy.threat > 0:
                targets.append(each_enemy)
        if len(targets) > 0:
            sort_targets(targets)
            choose_best_attack(hero, targets, viable_attacks)
    # if they're all going to die anyway it doesn't matter
    if not attack_completed:
        targets = []
        for each_enemy in enemy_formation:
            targets.append(each_enemy)
        choose_best_attack(hero, targets, viable_attacks)


def sort_targets(targets):
    if len(targets) > 1:
        # sort enemies first by threat > 1, then by already_moved, then threat level, then hp
        targets.sort(key=lambda k: k.effectiveHp)
        targets.sort(key=lambda k: k.threat, reverse=True)
        targets.sort(key=lambda k: (k.threat <= 1, k.alreadyMoved))


def sort_stun_targets(targets):
    if len(targets) > 1:
        # sort enemies first by threat > 1, then by already_moved, then threat level, then rank
        targets.sort(key=lambda k: k.rank, reverse=True)
        targets.sort(key=lambda k: k.threat, reverse=True)
        targets.sort(key=lambda k: (k.threat <= 1, k.alreadyMoved))


def choose_best_attack(hero, targets, list_of_attacks):
    global Debug, attack_completed
    for attack in list_of_attacks:
        for enemy in targets:
            target = enemy if any(enemy.rank[i] in AttackSkills[attack][1]
                                  for i, ranks in enumerate(enemy.rank)) else None
            if target is not None:
                attack_target(hero, target, attack, Debug)
                attack_completed = True
                break
        if attack_completed:
            break
    # global attack completed will be false if not successful (e.x. see bottom of plague_doctor_action)


def find_target_and_stun(hero, enemies_not_dead_already, attack, stun_chance, target=None):
    global attack_completed
    attack_completed = False
    list_of_attacks = [attack]
    potential_targets = []

    if target is None:
        for each_enemy in enemies_not_dead_already:
            if stun_chance - each_enemy.stunResist > 50 and not each_enemy.stunned:
                potential_targets.append(each_enemy)

        # if enemy is a very high threat and not going to die already
        if not attack_completed:
            targets = []
            for each_enemy in potential_targets:
                if each_enemy.threat >= 6:
                    targets.append(each_enemy)
            if len(targets) > 0:
                sort_stun_targets(targets)
                choose_best_attack(hero, targets, list_of_attacks)
        # if enemy is a high threat and not going to die already
        if not attack_completed:
            targets = []
            for each_enemy in potential_targets:
                if each_enemy.threat >= 4:
                    targets.append(each_enemy)
            if len(targets) > 0:
                sort_stun_targets(targets)
                choose_best_attack(hero, targets, list_of_attacks)
        # if enemy is not going to die already
        if not attack_completed:
            targets = []
            for each_enemy in potential_targets:
                targets.append(each_enemy)
            if len(targets) > 0:
                sort_stun_targets(targets)
                choose_best_attack(hero, targets, list_of_attacks)
    else:
        choose_best_attack(hero, [target], list_of_attacks)


def select_hero(target_hero_rank, debug):
    global SelectedHeroRank
    c = Controller(debug)
    if SelectedHeroRank != target_hero_rank:
        print('Selecting hero to lead!')
        c.press(c.down, interval=c.interval)
        if target_hero_rank < SelectedHeroRank:
            c.press(c.right_bumper, SelectedHeroRank - target_hero_rank, interval=c.interval)
        else:
            c.press(c.left_bumper, target_hero_rank - SelectedHeroRank, interval=c.interval)
        SelectedHeroRank = target_hero_rank


class Enemy:
    def __init__(self, enemy_info, index, rank, already_moved=False):
        self.index = int(index)
        self.battleId = enemy_info['data']['battle_guid']
        self.name = enemy_info['data']['actor']['name']
        self.threat = Monsters[self.name]['threat']
        self.currentHp = enemy_info['data']['actor']['current_hp']
        self.level = 0
        self.maxHp = Monsters[self.name]['hp'][self.level]
        self.isTank = True if (self.level == 0 and self.maxHp > 14) or (self.level == 1 and self.maxHp > 19) \
            or (self.level == 2 and self.maxHp > 25) else False
        self.rank = rank
        self.stunned = enemy_info['data']['actor']['stunned']
        buff_group = enemy_info['data']['actor']['buff_group']
        self.blightAmount = sum((buff['amount'] for buff in buff_group.values() if buff['stat_type'] == 4), 0)
        self.blightDuration = max(buff['duration'] for buff in buff_group.values() if buff['stat_type'] == 4) \
            if any(buff['stat_type'] == 4 for buff in buff_group.values()) else 0
        self.bleedAmount = sum((buff['amount'] for buff in buff_group.values() if buff['stat_type'] == 5), 0)
        self.bleedDuration = max(buff['duration'] for buff in buff_group.values() if buff['stat_type'] == 5) \
            if any(buff['stat_type'] == 5 for buff in buff_group.values()) else 0
        self.damageOnNextTurn = self.bleedAmount + self.blightAmount
        self.damageOnNextTwoTurns = (2*self.bleedAmount if self.bleedDuration > 1 else self.bleedAmount) \
            + (2*self.blightAmount if self.blightDuration > 1 else self.blightAmount)
        self.effectiveHp = self.currentHp - self.damageOnNextTurn if not self.stunned \
            else self.currentHp - self.damageOnNextTwoTurns
        self.percentHpRemain = (self.effectiveHp / self.maxHp) * 100
        self.canBeKilledIn1Hit = True if (not self.isTank and self.percentHpRemain < 50) \
            or (self.isTank and self.percentHpRemain <= 30) or self.name == 'Maggot' else False
        self.alreadyMoved = already_moved
        self.alreadyGoingToDie = self.effectiveHp <= 0 or self.threat == 0
        self.stunResist = Monsters[self.name]['stun_resist'][self.level]
        for each_buff in buff_group.values():
            if each_buff['stat_sub_type'] == 'stun':
                self.stunResist += (each_buff['amount'] * 100)


def get_enemy_formation(raid_info, turn_order):
    enemy_formation = []
    prev_enemy_size = None
    for index, enemy_info in raid_info['battle']['enemies'].items():
        name = enemy_info['data']['actor']['name']
        monster_id = str(enemy_info['data']['battle_guid'])
        if index == '0' and Monsters[name]['size'] == 2:
            rank = [1, 2]
            prev_enemy_size = 2
        elif index == '0' and Monsters[name]['size'] == 1:
            rank = [1]
            prev_enemy_size = 1
        elif index == '1' and prev_enemy_size == 2:
            rank = [3, 4] if Monsters[name]['size'] == 2 else [3]
        else:
            rank = [int(index) + 1]
        enemy_turn = \
            next((turn for turn in turn_order if 'monster_id' in turn and turn['monster_id'] == monster_id), None)
        enemy_formation.append(
            Enemy(enemy_info, index, rank, True if enemy_turn is None else enemy_turn['already_moved']))
    return enemy_formation
