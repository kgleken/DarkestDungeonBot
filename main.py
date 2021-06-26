import pydirectinput
import pyautogui
import win32gui
import json
import time
import os
from pathlib import Path

from SaveFileReader import SaveFileReader
from Battle import battle
from NavigateDungeon import navigate_dungeon, get_party_tile, get_dungeon_path
from DungeonInteractions import loot_treasure, identify_lootscreen_items
from Roster import Party
from Controls import Controller
from Items import Inventory

# ModsCheck = False
provisions_bought = False

# when fail-safe is on, move mouse to the corner of the screen to throw exception and abort program
pydirectinput.FAILSAFE = True


# if debug is True, then no keys will be pressed
def main(save_editor_path, game_install_location, profile_number, battle_speed='safe',
         debug=False, test_lootscreen=False):
    global provisions_bought
    c = Controller(debug)

    # Initialize Save File Reader
    sfr = SaveFileReader(save_editor_path, game_install_location, profile_number)

    if not debug:
        # Make Darkest Dungeon the active window
        dd_window = win32gui.FindWindowEx(0, 0, 0, "Darkest Dungeon")
        win32gui.SetForegroundWindow(dd_window)
        pydirectinput.doubleClick(x=1050, y=500)
        pydirectinput.doubleClick(x=1050, y=500)

    while True:
        print('Beginning main loop ...')
        sfr.decrypt_save_info('persist.game.json')
        f = open(Path(f'{sfr.SaveEditorPath}/persist.game.json'))
        info = json.load(f)['base_root']
        f.close()

        # In Dungeon
        if info['inraid']:
            # if ModsCheck is False:
            #     ModsCheck = True
            #     if 'applied_ugcs_1_0' in info:
            #         installed_mods = info['applied_ugcs_1_0']
            #         battle_speed = 'fast' \
            #             if any(mod['name'] == '885957080' for mod in installed_mods.values()) else 'safe'

            sfr.decrypt_save_info('persist.raid.json')
            f = open(Path(f'{sfr.SaveEditorPath}/persist.raid.json'))
            raid_info = json.load(f)['base_root']
            f.close()
            inventory = Inventory(raid_info)

            # Get party info
            sfr.decrypt_save_info('persist.roster.json')
            f = open(Path(f'{sfr.save_editor_path()}/persist.roster.json'))
            roster_info = json.load(f)['base_root']
            f.close()
            party_order = raid_info['party']['heroes']  # [front - back]
            party_info = Party(roster_info, party_order)

            # Separate utility for testing pattern recognition with saved lootscreen images
            # - problem with screen grab where it doesn't capture all windows including the loot window. Need to
            #   deselect and reselect darkest dungeon window in order to capture curio/loot window if not already
            #   open when starting the program (see activate_curio())
            # - second problem with pattern recognition accuracy not being good enough to classify items
            #  (not even close, see loot_treasure() for more details)
            if test_lootscreen:
                print('Testing loot screen capture!')
                search_region = rf'{sfr.save_editor_path()}\search_region.png'
                loot_img = rf'{sfr.game_install_location()}\scrolls\byhand.png'
                # use_item_img = rf'{sfr.game_install_location()}\scrolls\use_inventory.png'

                if not debug:
                    # Make Darkest Dungeon the active window
                    dd_window = win32gui.FindWindowEx(0, 0, 0, "Darkest Dungeon")
                    win32gui.SetForegroundWindow(dd_window)
                    pydirectinput.doubleClick(x=1050, y=500)
                    pydirectinput.doubleClick(x=1050, y=500)

                    if os.path.exists(search_region):
                        os.remove(search_region)
                    # pyautogui.screenshot(search_region, region=(1300, 425, 100, 150))
                    pyautogui.screenshot(search_region, region=(1060, 400, 585, 215))
                # found = list(pyautogui.locateAll(use_item_img, search_region, confidence=.8))
                found = list(pyautogui.locateAll(loot_img, search_region, confidence=.45))
                loot_screen_found = True if len(found) > 0 else False
                print(f'Found loot screen = {loot_screen_found}')

                if loot_screen_found:
                    dungeon_name = raid_info['raid_instance']['dungeon']
                    loot = identify_lootscreen_items(search_region, dungeon_name, party=party_info.heroes)
                    for item in loot:
                        print(f'item: {item.name}, quantity: {item.quantity}, slot: {item.item_slot}')
                return

            # Take action in Dungeon
            if raid_info['inbattle']:
                battle(inventory, battle_speed, debug)
            else:
                # Determine Dungeon location
                map_file = 'persist.map.json'
                sfr.decrypt_save_info(map_file)
                # map_file = 'map.json'  # can provide an alternate map file for debugging DungeonPath
                f = open(Path(f'{sfr.save_editor_path()}/{map_file}'))
                map_info = json.load(f)['base_root']
                f.close()
                areas = map_info['map']['static_dynamic']['areas']
                static_areas = map_info['map']['static_dynamic']['static_save']['base_root']['areas']
                location_number = raid_info['in_area']  # 1111584611
                location = next(index for index, area in areas.items() if static_areas[index]['id'] == location_number)

                # Used to debug droppable_items
                # dungeon_name = raid_info['raid_instance']['dungeon']
                # droppable_items = get_droppable_items(raid_info, areas, inventory, dungeon_name, party_info.heroes)
                # return

                # Check for loot screen
                queued_loot = raid_info['loot']['queue_items']['items']
                battle_reward = raid_info['loot']['result']['inventory_system']['items'] \
                    if 'result' in raid_info['loot'] else []
                if len(queued_loot) > 0 or len(battle_reward) > 0:
                    areas = map_info['map']['static_dynamic']['areas']
                    if location.startswith('co'):
                        static_tiles = static_areas[location]['tiles']
                        hallway_length = len(static_tiles) - 1
                        last_room_number = raid_info['last_room_id']  # 1111584611
                        reverse = last_room_number != static_tiles['tile0']['door_to']['area_to']
                        party_tile = get_party_tile(raid_info, hallway_length, reverse)
                    else:
                        party_tile = 0
                    dungeon_path, _ = get_dungeon_path(raid_info, static_areas, location)
                    loot_treasure(raid_info, inventory, areas, location, party_info.heroes,
                                  tile_number=party_tile, dungeon_path=dungeon_path, debug=debug)
                    sfr.decrypt_save_info('persist.raid.json')
                    f = open(Path(f'{sfr.SaveEditorPath}/persist.raid.json'))
                    raid_info = json.load(f)['base_root']
                    f.close()
                    inventory = Inventory(raid_info)  # important, need to check inventory again after looting

                time.sleep(.5)  # give enough time for loot/curio screen to close and mission complete to open
                c.write(c.b, 4)  # close out of menu (e.g. mission complete)
                time.sleep(.2)  # give enough time for mission complete screen to close

                navigate_dungeon(raid_info, areas, static_areas, inventory, party_info, location, debug)

        # In Town
        elif not info['inraid'] and not provisions_bought:
            # buy_provisions(dungeon_name, length, difficulty, debug)
            # provisions_bought = True

            # elif not info['inraid'] and provisions_bought:
            break
    print('DD bot finished!')


if __name__ == '__main__':
    main(r'C:\Users\Glek\Desktop\DDSaveEditor-v0.0.68', r'C:\Program Files (x86)\Steam\steamapps\common\DarkestDungeon',
         profile_number=1, battle_speed='fast', debug=False, test_lootscreen=False)
