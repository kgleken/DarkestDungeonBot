import pydirectinput
import json
from pathlib import Path
import time

from SaveFileReader import SaveFileReader as sfr
from Controls import Controller

pydirectinput.FAILSAFE = True


def get_party_tile(raid_info, hallway_length, reverse):
    area_tile = raid_info['areatile']
    if not reverse:
        return area_tile
    return hallway_length - area_tile


def loot_treasure(delay, debug):
    c = Controller(debug)
    print('Looting treasure!')
    pydirectinput.press(c.space, interval=c.interval)
    time.sleep(delay)


def activate_curio(raid_info, tile_number, area_name, reverse, debug):
    c = Controller(debug)
    print('Interacting with curio!')

    # future - select antiquarian or other hero depending on curio

    while not raid_info['inbattle']:
        c.press(c.up, interval=.3)
        c.press(c.a, 2, interval=.3)
        loot_treasure(delay=1, debug=debug)

        # move forward and try again if didn't get the curio
        sfr.decrypt_save_info('persist.map.json')
        f = open(Path(f'{sfr.save_editor_path()}/persist.map.json'))
        map_info = json.load(f)['base_root']
        f.close()
        areas = map_info['map']['static_dynamic']['areas']
        area_tiles = areas[area_name]['tiles']
        area_length = len(area_tiles) - 1
        tile_name = f'tile{tile_number}'

        sfr.decrypt_save_info('persist.raid.json')
        f = open(Path(f'{sfr.save_editor_path()}/persist.raid.json'))
        raid_info = json.load(f)['base_root']
        f.close()
        party_tile = 0 if area_length == 0 else get_party_tile(raid_info, area_length, reverse)

        if tile_number != party_tile or area_tiles[tile_name]['content'] == 0:
            break
        pydirectinput.press(c.right, 5)


def disarm_trap(raid_info, tile_number, area_name, reverse, debug):
    c = Controller(debug)
    print('Disarming Trap!')

    while not raid_info['inbattle']:
        pydirectinput.press(c.up, interval=c.interval)

        # move forward and try again if didn't get the trap
        sfr.decrypt_save_info('persist.map.json')
        f = open(Path(f'{sfr.save_editor_path()}/persist.map.json'))
        map_info = json.load(f)['base_root']
        f.close()
        areas = map_info['map']['static_dynamic']['areas']
        area_tiles = areas[area_name]['tiles']
        area_length = len(area_tiles) - 1

        sfr.decrypt_save_info('persist.raid.json')
        f = open(Path(f'{sfr.save_editor_path()}/persist.raid.json'))
        raid_info = json.load(f)['base_root']
        f.close()
        party_tile = 0 if area_length == 0 else get_party_tile(raid_info, area_length, reverse)

        if tile_number == party_tile:
            break
        pydirectinput.press(c.right, 3)


def clear_obstacle(raid_info, tile_number, area_name, reverse, debug):
    c = Controller(debug)
    print('Clearing Obstacle!')

    while not raid_info['inbattle']:
        pydirectinput.press(c.y, 2, interval=c.interval)

        # move forward and try again if didn't get the obstacle
        sfr.decrypt_save_info('persist.map.json')
        f = open(Path(f'{sfr.save_editor_path()}/persist.map.json'))
        map_info = json.load(f)['base_root']
        f.close()
        areas = map_info['map']['static_dynamic']['areas']
        area_tiles = areas[area_name]['tiles']
        area_length = len(area_tiles) - 1
        tile_name = f'tile{tile_number}'

        sfr.decrypt_save_info('persist.raid.json')
        f = open(Path(f'{sfr.save_editor_path()}/persist.raid.json'))
        raid_info = json.load(f)['base_root']
        f.close()
        party_tile = 0 if area_length == 0 else get_party_tile(raid_info, area_length, reverse)

        if party_tile > tile_number or area_tiles[tile_name]['content'] == 0:
            break
        pydirectinput.keyDown(c.right)
        time.sleep(2)
        pydirectinput.keyUp(c.right)


def hunger_check(static_areas, tile_number, area_name, reverse, debug):
    c = Controller(debug)
    print('Hunger Check!')
    area_number = static_areas[area_name]['id']

    while True:
        # move forward and try again if didn't get the check
        sfr.decrypt_save_info('persist.map.json')
        f = open(Path(f'{sfr.save_editor_path()}/persist.map.json'))
        map_info = json.load(f)['base_root']
        f.close()
        areas = map_info['map']['static_dynamic']['areas']
        area_tiles = areas[area_name]['tiles']
        area_length = len(area_tiles) - 1
        tile_name = f'tile{tile_number}'

        sfr.decrypt_save_info('persist.raid.json')
        f = open(Path(f'{sfr.save_editor_path()}/persist.raid.json'))
        raid_info = json.load(f)['base_root']
        f.close()
        party_tile = 0 if area_length == 0 else get_party_tile(raid_info, area_length, reverse)
        location_number = raid_info['in_area']

        if raid_info['inbattle'] or area_tiles[tile_name]['content'] != 8 or area_number != location_number \
                or (party_tile > tile_number and not reverse) or (party_tile < tile_number and reverse):
            break

        pydirectinput.press(c.a, 2, interval=c.interval)  # hit 'a' to use food on hunger check
        time.sleep(.5)
        pydirectinput.press(c.b, interval=c.interval)  # hit 'b' to fail hunger check when no food
        time.sleep(.5)

        # Attempt to move to next tile or enter next room if at the end of hallway
        pydirectinput.keyDown(c.right)
        time.sleep(1.5)
        pydirectinput.keyUp(c.right)
        pydirectinput.press(c.up)
        time.sleep(1)  # wait for room to load


def enter_room(raid_info, static_areas, area_name, reverse, debug):
    c = Controller(debug)
    print('Entering Room!')
    area_number = static_areas[area_name]['id']

    while not raid_info['inbattle']:
        pydirectinput.press(c.up, interval=c.interval)

        # move forward and try again if didn't get the door
        sfr.decrypt_save_info('persist.map.json')
        f = open(Path(f'{sfr.save_editor_path()}/persist.map.json'))
        map_info = json.load(f)['base_root']
        f.close()
        areas = map_info['map']['static_dynamic']['areas']
        area_tiles = areas[area_name]['tiles']
        area_length = len(area_tiles) - 1

        sfr.decrypt_save_info('persist.raid.json')
        f = open(Path(f'{sfr.save_editor_path()}/persist.raid.json'))
        raid_info = json.load(f)['base_root']
        f.close()
        party_tile = get_party_tile(raid_info, area_length, reverse)
        location_number = raid_info['in_area']

        if party_tile == (area_length if not reverse else 0) or area_number != location_number:
            break
        pydirectinput.keyDown(c.right)
        time.sleep(2.5)
        pydirectinput.keyUp(c.right)

    time.sleep(1)  # wait for room to load
