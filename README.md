# DarkestDungeonBot

See it working, in action, on my Youtube channel -
https://www.youtube.com/watch?v=XcX_klvC1zk

**Requirements:**

RoboJumper's save file editor - https://github.com/robojumper/DarkestDungeonSaveEditor

Xbox360 CE - https://www.x360ce.com/

**Instructions:**
1. Start Xbox360 CE (Controller Emulator) and click the checkbox that says "Enable 0 Mapped Devices" beneath the Controller 1 tab
2. Click the "Add" button with the plus icon in the Controller 1 tab. Your mouse and keyboard should already be selected by default, click "Add Selected Device"
3. Open the x360ce.xml file using a text editor and copy the entire contents
4. Click the "Paste Preset" button at the button to import the controller settings. The Xbox360 CE app allows you to save the settings, feel free to do so
5. Minimize Xbox360 CE to the system tray. It is now ready to go. Remember to exit the application later when your are finished using it
	Note: If you wish to use a custom controller configuration instead, you will need to edit Controls.py and rebuild the DDbot.exe
6. Extract/Unzip the DarkestDungeonSaveEditor package to it's own folder and place it in the same directory as the DDbot executable
7. Open the settings.json file and change the default settings if needed. The game install location you will probably not need to change. The save editor path you may need to change if the folder path is different
8. Change the save profile number to match your save file slot in game. "0" corresponds to the first slot, "1" corresponds to the second slot, and so on
	Note: It is assumed that your game save files are stored at 'C:\Program Files (x86)\Steam\userdata\71731729\262060\remote'. Please let me know if that is not the case
9. The battle_speed setting you can leave alone, but you can change it from "fast" to "safe" if you are experiencing problems, and not using the Faster Combat mod which I recommend (https://steamcommunity.com/sharedfiles/filedetails/?id=885957080)
10. Start the DarkestDungeon game, and once you are inside a dungeon double-click the DDbot.exe to begin. If you want to watch the console on another monitor while the application is running you can run it from the command prompt on a second monitor

**Currently Supported:**

    Hero Classes
    - Crusader
    - Hellion
    - Highwayman
    - Houndmaster
    - Jester
    - Man-at-Arms
    - Occultist
    - Plague Doctor
    - Shieldbreaker (only short length dungeons / no camping !!!)
    - Vestal
    
 - All Apprentice level dungeons and quest missions
 - No stealthed enemies
    - This is the only reason why dungeon levels higher than apprentice aren't supported yet and only shorth length missions for Shieldbreaker
 - No bosses
    - This includes The Collector which appears randomally, and The Shambler
    - Currently the program will exit whenever a boss is encountered so that the player can takeover control. This is because the bosses don't have threat levels assigned to them. In my own testing the generic battle algorithms have worked to defeat certain bosses like The Swine King and The Collector however they haven't been optimized,        and many bosses may require a more particular strategy. Therefore it is not enabled at this time

- No Town or Party management yet in-between missions 

- No Crimson Court or Color of Madness DLC

- Battle Speed mods that shorten animation times during battle are supported (and encouraged!!!). Make sure that the battle speed argument in the main function is set to 'Fast' (default). If not, I suggest changing it to 'Safe' instead to have the bot wait longer for potential animations to complete 

**Limitations:**

    Important !!! (MUST READ)
    
    - When resuming in the middle of a dungeon, the default party order is whatever order the heroes were in when you entered 
    the dungeon. Your party must be arranged in default order when starting the program otherwise things like selecting a hero 
    and camping will not work right. This includes when starting the program during battle. If not in battle you may need to 
    move a little bit afterward to make sure the change is reflected in the savefile 
    
    - When resuming in the middle of a dungeon, the items in your inventory must be arranged such that there are no gaps and 
    the first item is in slot 0 (upper left). If it is not correct, then the bot will not know which slot contains which item, 
    and things like looting and using items on curios won't work. This includes when starting the program during battle. If 
    not in battle you may need to move a little bit afterward to make sure the change is reflected in the savefile

- Loot that is awarded after battle is contained inside the savefile, which can read by the bot, and used to determine whether or not to drop and replace certain items held in the inventory. Loot that is awarded from curios however is random, and only exists inside the game client, therefore the bot cannot tell what items there are or how many. When this happens, we attempt to drop items one-at-a-time until we are able to blindly take all the items or we don't have anything left we can drop beneath a certain threshold. In the future we may be able to identify and classify the items using pattern recognition, however currently that is not supported

- The bot is not designed to handle situations where heroes die or become afflicted during a mission. This shouldn't ever happen on Apprentice or Veteran level missions anyways, unless the player screws up

- The algorithm used to navigate the dungeon is designed to visit every room in the shortest number of moves, regardless of what the mission objective is. This is fine in almost all cases, except when doing some quest missions that have a long and winding map layout. In these cases there could still be a quest curio hiding in one of the extra hallways that we do not go to. In the future the algorithm should probably cheat a little bit and check where the quest curios are. Also the bot will visit secret rooms if they are discovered, but will not re-route or go out of it's way to visit them currently   

**Known Issues:**
- Sometimes an enemy dies and leaves behind a corpse, and the next hero attacks the corpse. Not sure if this is caused by an error in the save file data or bug in the generic battle targeting script. It's probably the later, I think I've seen it more frequently occur with the Hellion and Highwayman hero classes

- In battle sometimes the cursor can be off by one when selecting a target for an ability or the cursor location can get reset, causing the ability to be used on the wrong target or the program to stall. This is a problem with either the xbox controller emulator, the pydirectinput python library, or the game's controller support. I'm not sure which, but I've done everything in my power to work-around this issue and make sure it happens as little as possible. This can happen while camping as well, but I believe it no longer happens when looting and interacting with curios. I've previously seen this bug cause the quest log screen to open when trying to drop an item, but this is believed to be fixed. The way you can tell when this happens is by looking at console output or log

- Sometimes (although rarely) after battle the program will think that the wrong hero is currently selected. This will usually cause trap disarm check failures or camping to not work right. Typically the hero that moved last in combat should be the one selected after combat. Usually the problem will correct itself the next time there is a battle. You can tell when it's wrong by looking at console output or log

- There is a rarely occurring game bug where it is an enemies turn to move during battle, but the game client waits for the player to move instead. If the player reloads the game, then the enemy will move instead. Currently we attempt to read the save file 10 times and if the enemy still hasn't moved then we assume that the game client is waiting for us to move instead, but it has yet to be thoroughly tested

- Certain curios that can yield treasure where treasure is not guaranteed such a Sarcophagus, ConfessionBooth, LeftLuggage, HolyFountain, UnlockedStrongbox, etc. can sometimes be activated and closed without looting. This is because in these cases we have to take a screenshot and look for the hand icon that appears on the loot screen to determine whether or not there is treasure. Sometimes a controller icon appears in the image that obscurs the hand icon that we are searching for. It has yet to be confirmed whether or not this has been fixed 

**Rebuilding:**
1. Install the latest version of Python (3.8), open the command line and make sure pip is up to date with "pip install --upgrade pip"
2. Install all the necessary packages one at a time using the command "pip install *package_name*". I think these are the only ones needed but let me know if not.
	pyinstaller
	pyautogui
	pydirectinput
	pywin32
	opencv-python (needed for pyautogui screenshot confidence interval)
3. Use cd to navigate to the location of the main.py file for darkest dungeon bot
4. Delete the old DDbot.exe file. Type 'pyinstaller --onefile -c -n DDbot main.py' and wait for the new one to finish building. The spec file and build folder that get generated aren't needed and can be removed after

**Debugging:**
1. Use whichever Python IDE to run or debug that you want, I like using PyCharm which is free with the base version
2. In order to debug, change the debug argument in main from False to True. This prevents the program from doing any key presses
3. Feel free to drop break points anywhere you want
4. Manually press the keys on the keyboard to do the button inputs instead as you step through the code

Enjoy!
