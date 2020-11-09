import pydirectinput
import win32gui
import json
from pathlib import Path

from SaveFileReader import SaveFileReader
from Battle import battle
from NavigateDungeon import navigate_dungeon
from DungeonInteractions import loot_treasure
from Roster import Party
from Controls import Controller

ModsCheck = False
battle_speed_offset = 0

# when fail-safe is on, move mouse to the corner of the screen to throw exception and abort program
pydirectinput.FAILSAFE = True


# if debug is True, then no keys will be pressed
def main(save_editor_path, profile_number, debug=False):
    global ModsCheck, battle_speed_offset
    c = Controller(debug)

    # Initialize Save File Reader
    sfr = SaveFileReader(save_editor_path, profile_number)

    if not debug:
        # Make Darkest Dungeon the active window
        dd_window = win32gui.FindWindowEx(0, 0, 0, "Darkest Dungeon")
        win32gui.SetForegroundWindow(dd_window)
        pydirectinput.doubleClick(x=1200, y=500)
        pydirectinput.doubleClick(x=1200, y=500)

    while True:
        sfr.decrypt_save_info('persist.game.json')
        f = open(Path(f'{sfr.SaveEditorPath}/persist.game.json'))
        info = json.load(f)['base_root']
        f.close()

        # In Dungeon
        if info['inraid']:
            dungeon_name = info['raiddungeon']

            if ModsCheck is False:
                ModsCheck = True
                if 'applied_ugcs_1_0' in info:
                    installed_mods = info['applied_ugcs_1_0']
                    battle_speed_offset = .3 \
                        if any(mod['name'] == '885957080' for mod in installed_mods.values()) else 0

            sfr.decrypt_save_info('persist.raid.json')
            f = open(Path(f'{sfr.SaveEditorPath}/persist.raid.json'))
            raid_info = json.load(f)['base_root']
            f.close()

            # Take action in Dungeon
            if raid_info['inbattle']:
                battle(battle_speed_offset, debug)
            else:
                # Get party info
                sfr.decrypt_save_info('persist.roster.json')
                f = open(Path(f'{sfr.save_editor_path()}/persist.roster.json'))
                roster_info = json.load(f)['base_root']
                f.close()
                party_order = raid_info['party']['heroes']  # [front - back]
                party_info = Party(roster_info, party_order)

                # Determine Dungeon location
                sfr.decrypt_save_info('persist.map.json')
                f = open(Path(f'{sfr.save_editor_path()}/persist.map.json'))
                map_info = json.load(f)['base_root']
                f.close()
                areas = map_info['map']['static_dynamic']['areas']
                static_area_data = map_info['map']['static_dynamic']['static_save']['base_root']['areas']

                location = None
                location_number = raid_info['in_area']  # 1111584611
                for index, area in areas.items():
                    if static_area_data[index]['id'] == location_number:
                        location = index  # e.x. 'rooA' or 'coAB' for room or hallway/corridor
                        break

                queued_loot = raid_info['loot']['queue_items']['items']
                if len(queued_loot) > 0 or 'result' in raid_info['loot']:
                    loot_treasure(delay=1, debug=debug)

                if location.startswith('roo'):  # player is in a room
                    c.press(c.b, 2, interval=c.interval)  # close out of menu (e.g. mission complete)

                navigate_dungeon(dungeon_name, raid_info, map_info, party_info, location, debug)

        # In Town
        if not info['inraid']:
            break
    print('DD bot finished!')


if __name__ == '__main__':
    main(r'C:\Users\Glek\Desktop\DDSaveEditor-v0.0.68', profile_number=1, debug=False)
