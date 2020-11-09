# DarkestDungeonBot

Requirements:

RoboJumper's save file editor - https://github.com/robojumper/DarkestDungeonSaveEditor

Xbox360 CE - https://www.x360ce.com/

Instructions:
1. Install the latest version of Python (3.8) and use whatever IDE you want, I like using PyCharm which is free with the base version.
2. Check the list of includes at the top of each file and install and the necessary packages using pip, or just right click and let Pycharm add the to the virtual environment for your project
3. Open Xbox360 CE and set it up to match the button configuration contained in the Controls.py file
4. The program uses the pydirectinput python library which has a feature that allows it throw an exception when you move the mouse cursor to one of the corners of the screen. Do that or switch to your IDE whenever you need to stop the program

Debugging:
1. In order to debug, change the debug argument in main from False to True. This prevent the program from doing any key presses
2. Feel free to drop break points anywhere you want
3. Manually press the keys on the keyboard to do the button inputs instead as you step through the code

Enjoy!
