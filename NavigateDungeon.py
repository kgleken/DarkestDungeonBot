import pydirectinput
import json
from pathlib import Path
import time

from SaveFileReader import SaveFileReader as sfr
from Controls import Controller, reset_party_order
from DungeonInteractions import activate_curio, clear_obstacle, disarm_trap, hunger_check, enter_room, get_party_tile
from Battle import select_hero

pydirectinput.FAILSAFE = True

Debug = False
isKeyDown = False
RoomCounter = 0


def navigate_dungeon(dungeon_name, raid_info, map_info, party_info, location, debug):
    global Debug
    Debug = debug
    print('Navigate Dungeon!')

    party = party_info.heroes
    party_order = party_info.partyOrder
    starting_party_order = party_info.startingPartyOrder

    # player is in a room
    if location.startswith('roo'):

        # interact with curio in room
        areas = map_info['map']['static_dynamic']['areas']
        tile = areas[location]['tiles']['tile0']
        if tile['curio_prop'] != 0 and tile['content'] != 0:
            activate_curio(raid_info, tile_number=0, area_name=location, reverse=False, debug=Debug)

        # make sure party order is correct and hero with best traps skill is leading
        reset_party_order(dungeon_name, party_order, starting_party_order, debug)
        select_best_traps_hero(party, debug)

        select_next_room(dungeon_name)

    # player is in a hall/corridor
    elif location.startswith('co'):

        # make sure party order is correct and hero with best traps skill is leading
        reset_party_order(dungeon_name, party_order, starting_party_order, debug)
        select_best_traps_hero(party, debug)

        travel_to_next_room(raid_info, map_info, hallway_name=location)


def select_next_room(dungeon_name):
    global Debug, RoomCounter
    c = Controller(Debug)

    print('Selecting next room!')
    c.press(c.b, 2, interval=c.interval)
    if dungeon_name == 'tutorial':
        # First tutorial mission
        c.press(c.right_stick_right, interval=c.interval)
    else:
        # Second tutorial mission
        if RoomCounter == 0 or RoomCounter == 1 or RoomCounter == 2 or RoomCounter == 5:
            c.press(c.right_stick_up, interval=c.interval)
            RoomCounter += 1
        elif RoomCounter == 3 or RoomCounter == 7:
            c.press(c.right_stick_down, interval=c.interval)
            RoomCounter += 1
        elif RoomCounter == 4 or RoomCounter == 6:
            c.press(c.right_stick_right, interval=c.interval)
            RoomCounter += 1
    time.sleep(1.5)


def travel_to_next_room(raid_info, map_info, hallway_name):
    global Debug
    print('Traveling to next room!')

    static_areas = map_info['map']['static_dynamic']['static_save']['base_root']['areas']
    static_tiles = static_areas[hallway_name]['tiles']
    areas = map_info['map']['static_dynamic']['areas']
    hallway_tiles = areas[hallway_name]['tiles']
    hallway_length = len(hallway_tiles) - 1

    # get previous room number in order to determine travel direction
    last_room_number = raid_info['last_room_id']  # 1111584611
    reverse = last_room_number != static_tiles['tile0']['door_to']['area_to']

    # make a list for remaining tiles in hallway, taking direction of travel into account
    party_tile = get_party_tile(raid_info, hallway_length, reverse)
    if not reverse:
        tiles_to_navigate = list(range(party_tile, hallway_length))
    else:
        tiles_to_navigate = list(range(party_tile, 0, -1))

    # Determine next hallway interaction
    # - it's rare but if party tile doesn't update in save file for some reason, just need to close and reopen the game
    for i in tiles_to_navigate:
        tile_name = f'tile{i}'
        curio_prop = hallway_tiles[tile_name]['curio_prop']
        # Curio
        if curio_prop != 0 and hallway_tiles[tile_name]['content'] != 0:
            move_to_tile(raid_info, hallway_length, reverse, tile_number=i)
            activate_curio(raid_info, tile_number=i, area_name=hallway_name, reverse=reverse, debug=Debug)
            break
        # Trap
        trap = hallway_tiles[tile_name]['trap']
        if trap != -858993460 and trap != 0 and hallway_tiles[tile_name]['knowledge'] > 1 \
                and hallway_tiles[tile_name]['content'] == 3:
            tile = i - 1 if not reverse else i + 1
            move_to_tile(raid_info, hallway_length, reverse, tile_number=tile)
            disarm_trap(raid_info, tile_number=i, area_name=hallway_name, reverse=reverse, debug=Debug)
            break
        # future - secret room
        # clear obstacle
        obstacle = static_tiles[tile_name]['obstacle']
        if obstacle != -858993460 and obstacle != 0 and hallway_tiles[tile_name]['content'] != 0:
            move_to_tile(raid_info, hallway_length, reverse, tile_number=i)
            clear_obstacle(raid_info, tile_number=i, area_name=hallway_name, reverse=reverse, debug=Debug)
            break
        # hunger check
        if hallway_tiles[tile_name]['content'] == 8:
            move_to_tile(raid_info, hallway_length, reverse, tile_number=i)
            hunger_check(static_areas, tile_number=i, area_name=hallway_name, reverse=reverse, debug=Debug)
            break
        # end of hallway
        if i == (hallway_length - 1 if not reverse else 1):
            move_to_tile(raid_info, hallway_length, reverse, tile_number=i)
            enter_room(raid_info, static_areas, area_name=hallway_name, reverse=reverse, debug=Debug)
            break


def move_to_tile(raid_info, hallway_length, reverse, tile_number):
    global isKeyDown
    c = Controller(Debug)
    torch_used = False

    party_tile = get_party_tile(raid_info, hallway_length, reverse)
    print(f'party on tile{party_tile}, moving to tile{tile_number}!')

    # move to tile with next dungeon interaction
    while party_tile != tile_number and not raid_info['inbattle']:
        if not isKeyDown:
            pydirectinput.keyDown(c.right)
            isKeyDown = True

        sfr.decrypt_save_info('persist.raid.json')
        f = open(Path(f'{sfr.save_editor_path()}/persist.raid.json'))
        raid_info = json.load(f)['base_root']
        f.close()

        torchlight = 0 if raid_info['torchlight'] == 0 else (raid_info['torchlight'] / 131072) - 8448
        if torchlight < 50 and not torch_used:
            pydirectinput.write(c.torch)  # need to use 'write' instead of 'press' for torch
            torch_used = True

        party_tile = get_party_tile(raid_info, hallway_length, reverse)

    if isKeyDown:
        pydirectinput.keyUp(c.right)
        isKeyDown = False


def select_best_traps_hero(party, debug):
    hero = None
    heroes = []
    for each_hero in party:
        if each_hero.traps_skill >= 30:
            heroes.append(each_hero)
    # future - add hp check in addition to stress check when choosing hero
    if len(heroes) > 0:
        heroes.sort(key=lambda k: k.stress, reverse=True)
        hero = next((hero for hero in heroes if hero.stress <= 70), None)
    if hero is None:
        party.sort(key=lambda k: k.stress)
        hero = party[0]
    select_hero(target_hero_rank=hero.rank, debug=debug)
