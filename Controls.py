import pydirectinput
import time

pydirectinput.FAILSAFE = True


class Controller:
    def __init__(self, debug):
        self.up = 'w' if not debug else ''
        self.down = 's' if not debug else ''
        self.left = 'a' if not debug else ''
        self.right = 'd' if not debug else ''
        self.space = 'space' if not debug else ''
        self.one = '1' if not debug else ''
        self.two = '2' if not debug else ''
        self.three = '3' if not debug else ''
        self.four = '4' if not debug else ''
        self.five = '5' if not debug else ''
        self.torch = 't' if not debug else ''
        self.map = 'm' if not debug else ''
        self.enter = 'enter' if not debug else ''
        self.esc = 'esc' if not debug else ''

        self.left_bumper = '9' if not debug else ''
        self.right_bumper = '0' if not debug else ''

        self.right_stick_up = 'p' if not debug else ''
        self.right_stick_down = ';' if not debug else ''
        self.right_stick_left = 'l' if not debug else ''
        self.right_stick_right = '\'' if not debug else ''

        self.d_pad_up = 'y' if not debug else ''
        self.d_pad_down = 'h' if not debug else ''
        self.d_pad_left = 'g' if not debug else ''
        self.d_pad_right = 'j' if not debug else ''

        self.x = 'x' if not debug else ''
        self.y = 'z' if not debug else ''
        self.a = 'v' if not debug else ''
        self.b = 'b' if not debug else ''
        self.back = 'o' if not debug else ''

        self.left_stick_up = 'k' if not debug else ''
        self.left_stick_down = ',' if not debug else ''
        self.left_stick_left = 'n' if not debug else ''
        self.left_stick_right = '.' if not debug else ''

    # wrapper for pydirectinput press method
    @staticmethod
    def press(key, presses=1):
        for i in range(0, presses):
            print(f'press: {key}')
            pydirectinput.write(key)
        pydirectinput.write('')  # do nothing, important to make sure next write goes through
        time.sleep(.1)

    # wrapper for pydirectinput write method
    @staticmethod
    def write(key, presses=1):
        for i in range(0, presses):
            print(f'write: {key}')
            pydirectinput.write(key)
            pydirectinput.write('')  # do nothing, important to make sure next write goes through
        time.sleep(.1)  # .05 previously

    # wrapper for pydirectinput keyDown method
    @staticmethod
    def keyDown(key):
        print(f'keyDown: {key}')
        pydirectinput.keyDown(key)

    # wrapper for pydirectinput keyUp method
    @staticmethod
    def keyUp(key):
        print(f'keyUp: {key}')
        pydirectinput.keyUp(key)


def attack_target(hero, target, attack, debug=False):
    c = Controller(debug)
    attack_slot = None
    print(f'attack target rank {target.index + 1} using {attack}')
    for index, skill in enumerate(hero.skills):
        if attack == skill:
            attack_slot = index + 1
            break

    # Select Ability
    time.sleep(.1)  # see if this delay helps with button input
    c.write(str(attack_slot) if not debug else '', 2)
    c.write(c.left_stick_left, 2)

    # Move Cursor
    c.write(c.left_stick_right, target.index)

    # Attack
    c.write(c.d_pad_right, 2)  # padding to prevent cursor from being reset, remove if accidentally opens quest log
    c.write(c.a, 2)  # necessary to make sure button press goes through
    print('Attack Target complete!')


def heal_target(hero, target, attack, debug=False):
    c = Controller(debug)
    attack_slot = None
    rank = 0 if target is None else target.rank
    print(f'attack target rank {rank} using {attack}')
    for index, skill in enumerate(hero.skills):
        if attack == skill:
            attack_slot = index + 1
            break

    # Select Ability
    time.sleep(.1)  # see if this delay helps with button input
    c.write(str(attack_slot) if not debug else '', 2)
    c.write(c.left_stick_right, 4)

    # Move Cursor
    if attack != 'gods_comfort':
        c.write(c.left_stick_left, target.rank - 1)

    # Heal
    c.write(c.d_pad_right, 2)  # padding to prevent cursor from being reset, remove if accidentally opens quest log
    c.write(c.a, 2)  # necessary to make sure button press goes through
    print('Heal target complete!')


def swap_hero(hero, swap_distance, party_order, debug=False):
    """ Positive number for distance moves hero forward and negative number moves hero backward """
    c = Controller(debug)
    offset = None
    print(f'swap distance {swap_distance}')
    print('updating party order!')
    party_order.remove(int(hero.roster_index))
    new_rank = hero.rank + (swap_distance * -1)
    new_rank = 4 if new_rank > 4 else 1 if new_rank < 1 else new_rank
    party_order.insert(new_rank - 1, int(hero.roster_index))

    # Select 'Swap' from choices
    time.sleep(.1)  # see if this delay helps with button input
    c.write(c.five, 2)

    # Move Cursor
    if swap_distance < 0:  # backward
        swap_distance *= -1

        if hero.rank == 1:
            offset = -1
        elif hero.rank == 2:
            offset = 0
        elif hero.rank == 3:
            offset = 1
        c.write(c.left_stick_right, 3)  # move cursor to start position
        c.write(c.left_stick_left, presses=offset+swap_distance)
    elif swap_distance > 0:  # forward

        if hero.rank == 4:
            offset = -1
        elif hero.rank == 3:
            offset = 0
        elif hero.rank == 2:
            offset = 1
        c.write(c.left_stick_left, 3)  # move cursor to start position
        c.write(c.left_stick_right, presses=offset+swap_distance)
    elif swap_distance == 0:  # skip turn
        c.write(c.b, 2)
        c.write(c.left_stick_right)

    # Swap
    c.write(c.d_pad_right, 2)  # padding to prevent cursor from being reset, remove if accidentally opens quest log
    c.write(c.a, 2)  # necessary to make sure button press goes through
    print('Swap complete!')


def reset_party_order(in_room, debug):
    print('reset_party_order')
    c = Controller(debug)
    if in_room:  # move forward if in room so it doesn't activate curio
        c.keyDown(c.right)
        time.sleep(1.3)
        c.keyUp(c.right)
    c.write(c.map)
    c.write(c.b, 3)
    c.keyDown(c.a)
    time.sleep(2)
    c.keyUp(c.a)
    time.sleep(.5)
    if not in_room:  # move forward before re-reading save file and selecting lead hero in hallway
        c.write(c.right, 3)


def drop_item(item_number, debug):
    print(f'drop_item {item_number}')
    c = Controller(debug)
    offset = None
    c.write(c.left_stick_up, 3)  # make sure cursor is in correct start position
    c.write(c.left_stick_down)

    if item_number < 8:
        offset = item_number
    elif 7 < item_number < 16:
        c.write(c.left_stick_down)
        offset = item_number - 8

    c.write(c.left_stick_right, offset)
    c.write(c.d_pad_left, 2)  # necessary to make sure button press goes through, make sure doesn't open quest log
    # c.write(c.right_stick_down, 2)  # try this instead if still doesn't work, be careful can cause us to leave room
    c.keyDown(c.y)
    time.sleep(1.2)
    c.keyUp(c.y)
    c.write(c.a)


def combine_items(item_number_1, item_number_2, debug, last_slot_trinket=None, selected_hero_class=None):
    print(f'combine_items in inventory, {item_number_1}, {item_number_2}')
    c = Controller(debug)
    c.write(c.left_stick_up, 2)
    c.write(c.left_stick_down)

    if item_number_1 < 8:
        c.write(c.left_stick_right, item_number_1)
        c.write(c.a)
        if last_slot_trinket is not None \
                and ('hero_class' not in last_slot_trinket or last_slot_trinket['hero_class'] == selected_hero_class):
            if item_number_2 < 8:
                c.write(c.left_stick_right, 2)
                c.write(c.left_stick_up)
                c.write(c.left_stick_right, item_number_2)
            elif 7 < item_number_2 < 16:
                c.write(c.left_stick_right, 2)
                c.write(c.left_stick_right, item_number_2 - 8)
        elif item_number_2 < 8:
            if item_number_2 > item_number_1:
                c.write(c.left_stick_right, item_number_2 - item_number_1)
            elif item_number_2 < item_number_1:
                c.write(c.left_stick_left, item_number_1 - item_number_2)
        elif 7 < item_number_2 < 16:
            c.write(c.left_stick_down)
            offset = item_number_2 - 8
            if offset > item_number_1:
                c.write(c.left_stick_right, offset - item_number_1)
            elif offset < item_number_1:
                c.write(c.left_stick_left, item_number_1 - offset)

    elif 7 < item_number_1 < 16:
        c.write(c.left_stick_down)
        offset = item_number_1 - 8
        c.write(c.left_stick_right, offset)
        c.write(c.a)
        if last_slot_trinket is not None \
                and ('hero_class' not in last_slot_trinket or last_slot_trinket['hero_class'] == selected_hero_class):
            if item_number_2 < 8:
                c.write(c.left_stick_right, 2)
                c.write(c.left_stick_up)
                c.write(c.left_stick_right, item_number_2)
            elif 7 < item_number_2 < 16:
                c.write(c.left_stick_right, 2)
                c.write(c.left_stick_right, item_number_2 - 8)
        elif item_number_2 < 8:
            c.write(c.left_stick_up)
            if item_number_2 > offset:
                c.write(c.left_stick_right, item_number_2 - offset)
            elif item_number_2 < offset:
                c.write(c.left_stick_left, offset - item_number_2)
        elif 7 < item_number_2 < 16:
            if item_number_2 > item_number_1:
                c.write(c.left_stick_right, item_number_2 - item_number_1)
            elif item_number_2 < item_number_1:
                c.write(c.left_stick_left, item_number_1 - item_number_2)
    c.write(c.a)


def take_item(index, debug):
    print(f'take_item {index}')
    c = Controller(debug)
    c.write(c.left_stick_down)
    c.write(c.left_stick_up, 2)
    c.write(c.left_stick_right, index)
    c.write(c.a)


def use_item_on_curio(item_number, debug):
    print(f'use_item_on_curio {item_number}')
    c = Controller(debug)
    offset = None
    c.write(c.right_stick_down)
    c.write(c.y)

    if item_number < 8:
        offset = item_number
    elif 7 < item_number < 16:
        c.write(c.left_stick_down)
        offset = item_number - 8

    c.write(c.left_stick_right, offset)
    c.write(c.y)


def use_item(item_number, debug):
    print(f'using item {item_number}')
    c = Controller(debug)
    offset = None
    c.write(c.down)
    c.write(c.d_pad_up)

    if item_number < 8:
        offset = item_number
    elif 7 < item_number < 16:
        c.write(c.left_stick_down)
        offset = item_number - 8

    c.write(c.left_stick_right, offset)
    c.write(c.y)
