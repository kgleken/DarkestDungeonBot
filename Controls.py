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

        self.left_bumper = '9' if not debug else ''
        self.right_bumper = '0' if not debug else ''

        self.right_stick_up = 'p' if not debug else ''
        self.right_stick_down = ';' if not debug else ''
        self.right_stick_left = 'l' if not debug else ''
        self.right_stick_right = '\'' if not debug else ''

        self.x = 'x' if not debug else ''
        self.y = 'z' if not debug else ''
        self.a = 'v' if not debug else ''
        self.b = 'b' if not debug else ''

        self.left_stick_up = 'k' if not debug else ''
        self.left_stick_down = ',' if not debug else ''
        self.left_stick_left = 'm' if not debug else ''
        self.left_stick_right = '.' if not debug else ''

        self.interval = .05

    # wrapper for pydirectinput press method
    @staticmethod
    def press(keys, presses=1, interval=0.0):
        for i in range(0, presses):
            pydirectinput.write(keys)
            time.sleep(interval)


def attack_target(hero, target, attack, debug=False):
    c = Controller(debug)
    attack_slot = None
    for index, skill in enumerate(hero.skills):
        if attack == skill:
            attack_slot = index + 1
            break

    # Select Ability
    c.press(str(attack_slot) if not debug else '', 2, interval=c.interval)
    c.press(c.left_stick_left, 4, interval=c.interval)

    # Move Cursor
    c.press(c.left_stick_right, target.index, interval=c.interval)

    # Attack
    c.press(c.a, interval=c.interval)
    print('Attack Target complete!')


def heal_target(hero, target, attack, debug=False):
    c = Controller(debug)

    attack_slot = None
    for index, skill in enumerate(hero.skills):
        if attack == skill:
            attack_slot = index + 1
            break

    # Select Ability
    c.press(str(attack_slot) if not debug else '', 2, interval=c.interval)
    c.press(c.left_stick_right, 4, interval=c.interval)

    # Move Cursor
    if attack != 'gods_comfort':
        c.press(c.left_stick_left, target.rank - 1, interval=c.interval)

    # Heal
    c.press(c.a, interval=c.interval)
    print('Heal target complete!')


def swap_hero(hero, swap_distance, debug=False):
    """ Positive number for distance moves hero forward and negative number moves hero backward """
    c = Controller(debug)
    offset = None

    # Select 'Swap' from choices
    c.press(c.five, 2, interval=c.interval)

    # Move Cursor
    if swap_distance < 0:  # backward
        swap_distance *= -1

        if hero.rank == 1:
            offset = -1
        elif hero.rank == 2:
            offset = 0
        elif hero.rank == 3:
            offset = 1
        c.press(c.left_stick_right, 3, interval=c.interval)  # move cursor to start position
        c.press(c.left_stick_left, presses=offset+swap_distance, interval=c.interval)
    elif swap_distance > 0:  # forward

        if hero.rank == 4:
            offset = -1
        elif hero.rank == 3:
            offset = 0
        elif hero.rank == 2:
            offset = 1
        c.press(c.left_stick_left, 3, interval=c.interval)  # move cursor to start position
        c.press(c.left_stick_right, presses=offset+swap_distance, interval=c.interval)
    elif swap_distance == 0:  # skip turn
        c.press(c.b, 2, interval=c.interval)
        c.press(c.left_stick_right, interval=c.interval)

    # Swap
    c.press(c.a, interval=c.interval)
    print('Swap complete!')


def reset_party_order(dungeon_name, party_order, starting_party_order, debug):
    if party_order != starting_party_order and dungeon_name != 'tutorial':
        print('reset_party_order')
        c = Controller(debug)
        c.press(c.b, interval=c.interval)
        pydirectinput.keyDown(c.a)
        time.sleep(1.5)
        pydirectinput.keyUp(c.a)
        time.sleep(1)
