### State module
# Contains every public shared objects,
# so at any moment this represents the "state" of the program

import curses, math, os
from verticalhandler import KeyHandler, QuitGame

### DEFINES ###

# Constants
UP = (-1, 0)
RIGHT = (0, 1)
DOWN = (1, 0)
LEFT = (0, -1)

# Directory
BASEDIR = os.path.dirname(os.path.abspath(__file__))

# MULTIPLATFORM ALIASES
ENTER_ALIASES = {curses.KEY_ENTER, ord("\n"), ord("\r")}
BACKSPACE_ALIASES = {curses.KEY_BACKSPACE, 127}
QUIT_ALIASES = {ord("q"), ord("Q")}
ARGQUIT_ALIASES = {ord(curses.ascii.ctrl("x"))}


# Key handler
keyhandler = KeyHandler()
PRIORITIES = {
    "Game": 0,
    "Action": 1,
    "Argument": 2
}


### UTILITY ###

# To be sure game can be executed anywhere

def realpath(*path):
    return os.path.join(BASEDIR, *path)

# Work with tuples

def abs_distance(pos1,pos2):
    # Manhatan distance
    y1,x1 = pos1
    y2,x2 = pos2
    return math.ceil(math.sqrt((y2-y1)**2+(x2-x1)**2))

def diag_distance(pos1, pos2):
    # Chebyshev distance
    y1,x1 = pos1
    y2,x2 = pos2
    dx, dy = abs(x2-x1), abs(y2-y1)
    return dy+dx-min(dx,dy)

def distance(pos1,pos2):
    # Euclidian distance
    y1,x1 = pos1
    y2,x2 = pos2
    return abs(y1-y2)+abs(x1-x2)
    
def rad2deg(a):
    return a*180/math.pi

def add_tuples(*tuples):
    return tuple(sum(values) for values in zip(*tuples))

def sub_tuples(t1, t2):
    return tuple(a-b for a, b in zip(t1, t2))

# I/O utilitaries

def warning(message):
    output('\\C11[Warning]\\C1 ' + message)

def message(*args, source="game"):
    warning("deprecated usage of 'message'")
    output("["+source+"]",*args)

def output(*args, sep=' '):
    message_window.update_messages(sep.join(str(e) for e in args))

def quit():
    raise QuitGame()
    
### FRAMES ###

# A frame is an object which purpose is to make a single aspect
# of the program run, e.g. handle physics
class Frame:
    def __init__(self, window, *args, **kwargs):
        self.window = window
        self._post_init(*args, **kwargs)
    def _post_init(self):
        pass


### WINDOWS ###

# A virtual representation of the screen
class Screen:
    def __init__(self, stdscr):
        self.window = stdscr
        self.size = curses.LINES, curses.COLS
        self.windows = []
        self.bkgd(' ', curses.color_pair(1) | curses.A_BOLD)
    def __getattr__(self, attr):
        return getattr(self.window, attr)
    def add_window(self, window):
        self.windows.append(window)
    def remove_window(self, window):
        self.windows.remove(window)
    def refresh(self):
        self.clear()
        for window in self.windows:
            window.draw()
        self.window.refresh()
# A window is a representation of an element of the screen
# visually independent from the rest of the screen
class Window:
    def __init__(self, parent, y, x, height, width, *args, **kwargs):
        self.parent = parent
        self.y = y
        self.x = x
        self.height = height
        self.width = width
        self._post_init(*args, **kwargs)
        self._border = True
    def _post_init(self):
        pass
    def draw(self):
        self.border()
    def addch(self, y, x, char, attributes=0):
        colors = 0
        if len(char) > 1:
            if len(char) > 3 and char.startswith("\\C"):
                color = ""
                index = 2
                while True:
                    if char[index] in '0123456789':
                        color += char[index]
                        index += 1
                    else:
                        break
                index += 1
                char = char[index:]
                color = int(color)
            attributes |= curses.color_pair(color)
        self.parent.addch(self.y+y, self.x+x, char, color|curses.A_BOLD)
        self.parent.chgat(self.y+y, self.x+x, 1, curses.color_pair(color)|curses.A_BOLD)
    def addstr(self, y, x, string, color=1, *args, other_flags=0, **kwargs):
        strings = []
        actual = ""
        i = 0
        uptonow = 0
        while i < len(string):
            if i < len(string)-2 and string[i:i+2] == '\\C':
                strings.append((uptonow-len(actual), color, actual))
                actual = ""
                color = ""
                i += 2
                while i < len(string) and string[i] in '0123456789':
                    color += string[i]
                    i += 1
                i += 1
                color = int(color)
            else:
                uptonow += 1
                actual += string[i]
                i += 1
        strings.append((uptonow-len(actual), color, actual))
        for uptonow, color, string in strings:
            self.parent.addstr(self.y+y, self.x+x+uptonow, string, curses.color_pair(color) | other_flags, *args, **kwargs)
    def border(self):
        if self._border:
            curses.textpad.rectangle(self.parent, self.y, self.x, self.y+self.height-1, self.x+self.width-2)


        
### OTHER ###

class Armor:
    def __init__(self, parent):
        self.parent = parent
        self.y = 0
        self.x = 0
        self.size = (1, 20)
    def draw(self):
        hero = game_frame.get_hero()
        self.parent.addstr(self.y,self.x,"Armor: %s" % hero.armor)

class Resistance:
    def __init__(self, parent):
        self.parent = parent
        self.y = 1
        self.x = 0
        self.size = (1, 20)
    def draw(self):
        hero = game_frame.get_hero()
        self.parent.addstr(self.y,self.x,"Resistance: %s" % hero.resistance)

# Life, keeps graphical count of life
class Life:
    def __init__(self, parent):
        self.parent = parent
        self.y = 2
        self.x = 0
        self.size = (2, 20)
    def draw(self):
        max_life = game_frame.creatures[0].max_life
        actual = int(round(game_frame.creatures[0].life*self.size[1]/max_life,0))
        actual_true = game_frame.creatures[0].life
        self.parent.addstr(self.y, self.x, "Life: %s/%s" % (str(actual_true), str(max_life)))
        for i in range(self.size[1]):
            if i < actual:
                self.parent.addch(self.y+1, self.x+i, ord(" "), curses.color_pair(2) | curses.A_BOLD)
            else:
                self.parent.addch(self.y+1, self.x+i, ord(" "), curses.color_pair(3) | curses.A_BOLD)

class Mana:
    def __init__(self, parent):
        self.parent = parent
        self.y = 4
        self.x = 0
        self.size = (2, 20)
    def draw(self):
        max_mana = game_frame.creatures[0].max_mana
        if max_mana == 0:
            actual = 0
        else:
            actual = int(round(game_frame.creatures[0].mana*self.size[1]/max_mana,0))
        actual_true = game_frame.creatures[0].mana
        self.parent.addstr(self.y, self.x, "Mana: %s/%s" % (str(actual_true), str(max_mana)))
        for i in range(self.size[1]):
            if i < actual:
                self.parent.addch(self.y+1, self.x+i, ord(" "), curses.color_pair(7) | curses.A_BOLD)
            else:
                self.parent.addch(self.y+1, self.x+i, ord(" "), curses.color_pair(3) | curses.A_BOLD)

class Hands(Window):
    def __init__(self, parent):
        self.parent = parent
        self.y = 0
        self.x = 21
        self.size = (2, 20)
        self._border = False
    def draw(self):
        hero_inventory = game_frame.get_hero().inventory
        self.addstr(0, 0, "Right: " + hero_inventory.slots["right"].repr())
        self.addstr(1, 0, "Left: " + hero_inventory.slots["left"].repr())
                
class Coords:
    def __init__(self, parent):
        self.parent = parent
        self.y = 2
        self.x = 21
        self.size = (1, 20)
    def draw(self):
        self.parent.addstr(self.y, self.x, "Coords: %s,%s" % game_frame.get_hero().pos)

class Turns:
    def __init__(self, parent):
        self.parent = parent
        self.y = 3
        self.x = 21
        self.size = (1, 20)
    def draw(self):
        self.parent.addstr(self.y, self.x, "Turns: %s (%s)" % (game_frame.player_turns, game_frame.turns))


import action, verticalhandler, game, creature, items, color, map

from items import Item, InventoryWindow, Inventory
from action import ActionFrame, ActionWindow, Action
from game import GameFrame, GameWindow
from creature import Creature, Hero
from color import colors
from map import Map
