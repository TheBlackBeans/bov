### State module
# Contains every public shared objects,
# so at any moment this represents the "state" of the program

import curses, color
from verticalhandler import KeyHandler, QuitGame

### DEFINES ###

# Constants
UP = (-1, 0)
RIGHT = (0, 1)
DOWN = (1, 0)
LEFT = (0, -1)


# MULTIPLATFORM ALIASES
ENTER_ALIASES = {curses.KEY_ENTER, ord("\n"), ord("\r")}
QUIT_ALIASES = {ord("q"), ord("Q")}

# Key handler
keyhandler = KeyHandler()
PRIORITIES = {
    "Game": 0,
    "Action": 1,
    "Argument": 2
}


### UTILITY ###

def add_tuples(*tuples):
    return tuple(sum(values) for values in zip(*tuples))

def sub_tuples(t1, t2):
    return tuple(a-b for a, b in zip(t1, t2))

def message(*args, source="game"):
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
    def addch(self, y, x, *args, **kwargs):
        self.parent.addch(self.y+y, self.x+x, *args, **kwargs)
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


### MAP ###
# Map related classes

# A tile is the most basic map component
class Tile:
    def __init__(self, char, wall):
        self.char = char
        self.wall = wall
        self.lit = True
    def draw(self):
        if self.lit:
            return self.char
        else:
            return " "

        
### CREATURES ###

class Creature:
    DEFAULT_CHAR = "%"
    DEFAULT_POS = (0,0)
    DEFAULT_COLOR = 4
    def __init__(self, pos=None, char=None, color=None):
        if char is None:
            self.char = self.DEFAULT_CHAR
        else:
            self.char = char
        if pos is None:
            self.pos = self.DEFAULT_POS
        else:
            self.pos = pos
        if color is None:
            self.color = self.DEFAULT_COLOR
        else:
            self.color = color
    def move(self, dir):
        self.pos = add_tuples(self.pos, dir)
        
class Hero(Creature):
    DEFAULT_CHAR = "@"
    
class Daemon(Creature):
    DEFAULT_CHAR = "&"


### OTHER ###

# Life, keeps graphical count of life
class Life:
    def __init__(self, parent):
        self.parent = parent
        self.y = 3
        self.x = 0
        self.size = (2, 20)
        self.max_life = 20
        self.actual = 20
    def update_max(self, life):
        d = life-self.max_life
        self.max_life = life
        self.size = (1, life)
        if d > 0:
            self.differential(d)
    def update(self, life):
        self.actual = min(max(life, 0), self.max_life)
    def differential(self, d):
        self.update(self.actual+d)
    def draw(self):
        self.parent.addstr(self.y, self.x, "Life: %s/%s" % (str(self.actual), str(self.max_life)))
        for i in range(self.size[1]):
            if i < self.actual:
                self.parent.addch(self.y+1, self.x+i, ord(" "), curses.color_pair(2) | curses.A_BOLD)
            else:
                self.parent.addch(self.y+1, self.x+i, ord(" "), cuses.color_pair(3) | curses.A_BOLD)


class Coords:
    def __init__(self, parent):
        self.parent = parent
        self.y = 0
        self.x = 0
        self.size = (1, 20)
    def draw(self):
        self.parent.addstr(self.y, self.x, "Coords: %s,%s" % game_frame.creatures[0].pos)

import action, verticalhandler, game

from action import ActionFrame, ActionWindow, Action
from game import GameFrame, GameWindow
