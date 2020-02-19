#!/usr/bin/python3
# -*- coding: utf-8 -*-

from math import ceil
from curses import wrapper
import curses
import curses.textpad

from modding import Event, register_callback, register_event, register_trigger


# Exceptions
class QuitGame(BaseException):
    pass

# Events
@register_event
class KeyPress(Event):
    pass



UP = (-1, 0)
RIGHT = (0, 1)
DOWN = (1, 0)
LEFT = (0, -1)

ENTER_ALIASES = {curses.KEY_ENTER, ord("\n"), ord("\r")}

class Window:
    def draw():
        self.border()
    def addch(self, y, x, *args, **kwargs):
        self.parent.addch(self.begin_y+y, self.begin_x+x,*args, **kwargs)
    def addstr(self, y, x, *args, **kwargs):
        self.parent.addstr(self.begin_y+y, self.begin_x+x,*args, **kwargs)
    def border(self):
        curses.textpad.rectangle(self.parent, self.begin_y, self.begin_x, self.begin_y+self.height-1, self.begin_x+self.width-1)
        
class Tile:
    def __init__(self, char, wall):
        self.char = char
        self.wall = wall
        
class MessageWindow(Window):
    def __init__(self, parent):
        self.parent = parent
        self.height = parent.size[0]//3
        self.width = 2*parent.size[1]//5
        self.size = self.height, self.width
        self.begin_y = parent.size[0] - self.height
        self.begin_x = 0
        self.messages = []
        self.msg = []
    def update_messages(self, message):
        self.messages.append(message)
        self.get_messages()
    def split_message(self, msg, width):
        return [msg[i*width:(i+1)*width] for i in range(ceil(len(msg)/width))]
    def get_messages(self):
        self.msg = []
        height = self.height - 2
        width = self.width - 2
        for message in self.messages[::-1]:
            for line in self.split_message(message, width)[::-1]:
                if len(self.msg) >= height:
                    break
                self.msg.insert(0, line)
            if len(self.msg) >= height:
                break
    def draw_messages(self):
        for i, line in enumerate(self.msg):
            self.addstr(i+1, 1, line)
    def draw(self):
        self.border()
        self.draw_messages()
        
class ActionWindow(Window):
    def __init__(self, parent):
        self.parent = parent
        self.height = 3
        self.width = 2*parent.size[1]//5
        self.size = self.height, self.width
        self.begin_y = parent.size[0] - (self.height + parent.size[0]//3)
        self.begin_x = 0
        self.action = None
    def draw(self):
        self.border()
        self.draw_action()
    def draw_action(self):
        if self.action:
            self.addstr(1, 1, self.action.repr_string())
    def load_action(self, action):
        self.action = action
    def do_action(self):
        if self.action:
            self.action.do_action()
        self.action = None

class Action:
    def __init__(self, name, args, action, msg=None):
        self.name = name
        self.args = args
        self.repr = [name] + args
        self.action = action
        self.msg = msg
    def set_arg(self, arg, value):
        self.repr[arg+1] = value
    def repr_string(self):
        return " ".join(self.repr)
    @register_callback(KeyPress)
    def key_handler(self, context):
        pass
    def do_action(self):
        self.action()
        if self.msg:
            print_well(self.msg)
        
        
class GameWindow(Window):
    def __init__(self, parent, hero):
        self.map = {}
        with open("maps/map1.mp") as f:
            for y, line in enumerate(f.read().split("\n")):
                for x, c in enumerate(line):
                    if c == "@":
                        hero.pos = (y,x)
                        self.map[y, x] = Tile(".", False)
                    elif c == ".":
                        self.map[y, x] = Tile(c, False)
                    elif c == "#":
                        self.map[y, x] = Tile(c, True)
        self.parent = parent
        self.height = parent.size[0]
        self.width = 3*parent.size[1]//5
        self.size = self.height, self.width
        self.begin_y = 0
        self.begin_x = parent.size[1] - self.width
        self.creatures = {"hero": hero}
        self.offset = (1,2)
    def add_tuples(self, t1, t2):
        return tuple(a+b for a, b in zip(t1, t2))
    def move(self, what, dir):
        y, x = self.add_tuples(self.creatures[what].pos, dir)
        if (y, x) in self.map and not self.map[y, x].wall:
            self.creatures[what].move(dir)
            
    def regulate_offset(self):
        while self.creatures["hero"].pos[0]+self.offset[0] <= 2:
            self.offset = self.offset[0]+1, self.offset[1]
        while self.creatures["hero"].pos[0]+self.offset[0] >= self.height-3:
            self.offset = self.offset[0]-1, self.offset[1]
        while self.creatures["hero"].pos[1]+self.offset[1] <= 2:
            self.offset = self.offset[0], self.offset[1]+1
        while self.creatures["hero"].pos[1]+self.offset[1] >= self.width-4:
            self.offset = self.offset[0], self.offset[1]-1
    def draw(self):
        self.regulate_offset()
        self.border()
        self.draw_map()
        self.draw_hero()
    def draw_map(self):
        for y in range(1,self.height-1):
            for x in range(1,self.width-3):
                if (y-self.offset[0], x-self.offset[1]) in self.map:
                    self.addch(y, x, self.map[y-self.offset[0],x-self.offset[1]].char)
                    
    def addch(self, y, x, *args, **kwargs):
        if 0 <= y < self.height and 0 <= x < self.width:
            self.parent.addch(self.begin_y+y, self.begin_x+x, *args, **kwargs)
    def draw_hero(self):
        self.addch(self.creatures["hero"].pos[0]+self.offset[0], self.creatures["hero"].pos[1]+self.offset[1], self.creatures["hero"].char, curses.color_pair(self.creatures["hero"].color))
    def border(self):
        curses.textpad.rectangle(self.parent, self.begin_y, self.begin_x, self.begin_y+self.height-1, self.begin_x+self.width-2)

        
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
        
class Life:
    def __init__(self, parent):
        self.parent = parent
        self.y = 3
        self.x = 0
        self.size = (2, 20)
        self.max_life = 20
        self.actual = 20
    def update_max(self, life):
        d = life - self.max_life
        self.max_life = life
        self.size = (1, life)
        if d > 0:
            self.differential(d)
    def update(self, life):
        self.actual = life
    def differential(self, d):
        self.actual = min(max(self.actual + d, 0), self.max_life)
    def draw(self):
        self.parent.addstr(self.y, self.x, "%s/%s" % (str(self.actual), str(self.max_life)))
        for i in range(self.size[1]):
            if i < self.actual:
                self.parent.addch(self.y+1, self.x+i, ord(" "), curses.color_pair(2) | curses.A_BOLD)
            else:
                self.parent.addch(self.y, self.x+i, ord(" "), curses.color_pair(3) | curses.A_BOLD)

class Hero:
    def __init__(self):
        self.char = "@"
        self.pos = (0, 0)
        self.color = 4
    def move(self, dir):
        if dir == UP:
            self.pos = self.pos[0]-1, self.pos[1]
        elif dir == RIGHT:
            self.pos = self.pos[0], self.pos[1]+1
        elif dir == DOWN:
            self.pos = self.pos[0]+1, self.pos[1]
        elif dir == LEFT:
            self.pos = self.pos[0], self.pos[1]-1

def print_well(*args, sep=' '):
    message_window.update_messages(sep.join(str(e) for e in args))

def quit():
    raise QuitGame()
    
def main(stdscr):
    global message_window
    # Default text
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    # Bars
    #  filled
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_RED)
    #  empty
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_WHITE)
    # Hero
    curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_WHITE)
    screen = Screen(stdscr)
    curses.curs_set(False)
    screen.clear()

    hero = Hero()
    message_window = MessageWindow(screen)
    life = Life(screen)
    game_window = GameWindow(screen, hero)
    action_window = ActionWindow(screen)

    keyloggers = []
    
    screen.add_window(message_window)
    screen.add_window(life)
    screen.add_window(game_window)
    screen.add_window(action_window)
    screen.refresh()
    try:
        while True:
            key = screen.getch()
            if key in {ord("q"), ord("Q")}:
                action_window.load_action(Action("quit", [], lambda: quit()))
            elif key == curses.KEY_DOWN:
                game_window.move("hero", DOWN)
            elif key == curses.KEY_UP:
                game_window.move("hero", UP)
            elif key == curses.KEY_RIGHT:
                game_window.move("hero", RIGHT)
            elif key == curses.KEY_LEFT:
                game_window.move("hero", LEFT)
            elif key == ord("h"):
                message_window.update_messages("This is quite a long text. I would even say this text is too long for the message box!")
            elif key == ord("k"):
                message_window.update_messages("Hurt! (%s)" % str(life.actual -1))
                life.differential(-1)
            elif key == ord("l"):
                action_window.load_action(Action("look", [], lambda: print_well("Coords:",hero.pos), ""))
            elif key == ord("s"):
                action_window.load_action(Action("save", [], lambda: None, "Saved!"))
            elif key in ENTER_ALIASES:
                action_window.do_action()
            else:
                print_well("DEBUG:",key)
            screen.refresh()
    except QuitGame:
        return 
    
    

wrapper(main)
