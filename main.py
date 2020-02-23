#!/usr/bin/python3
# -*- coding: utf-8 -*-

from math import ceil
import sys, os
from curses import wrapper
import curses
import curses.textpad

import state
from state import *



class MessageWindow(Window):
    def _post_init(self):
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
    
def main(stdscr):
    stop = False
    # Default text
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    # Bars
    #  filled
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_RED)
    #  empty
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_WHITE)
    # Hero
    curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_WHITE)
    # Highlighted text
    curses.init_pair(5, curses.COLOR_RED, curses.COLOR_WHITE)
    # Selected argument
    curses.init_pair(6, curses.COLOR_RED, curses.COLOR_MAGENTA)
    state.screen = Screen(stdscr)
    curses.curs_set(False)
    state.screen.clear()

    hero = Hero()
    sc_height = state.screen.size[0]
    sc_width = state.screen.size[1]
    
    gw_height = sc_height
    gw_width = 3*sc_width//5
    game_window = GameWindow(
        state.screen,
        0,
        sc_width - gw_width,
        gw_height,
        gw_width
    )
    
    mw_height = sc_height//3
    mw_width = 2*sc_width//5
    state.message_window = MessageWindow(
        state.screen,
        sc_height - mw_height,
        0,
        mw_height,
        mw_width
    )

    aw_height = 3
    aw_width = 2*sc_width//5
    action_window = ActionWindow(
        state.screen,
        sc_height - (aw_height + mw_height),
        0,
        aw_height,
        aw_width
    )

    life = Life(state.screen)
    coords = Coords(state.screen)
    
    state.game_frame = state.GameFrame(game_window, hero)
    state.action_frame = state.ActionFrame(action_window)

    
    state.screen.add_window(state.message_window)
    state.screen.add_window(life)
    state.screen.add_window(coords)
    state.screen.add_window(game_window)
    state.screen.add_window(action_window)
    state.screen.refresh()
    try:
        while not stop:
            key = state.screen.getch()
            state.keyhandler.dispatch_key(key)
            state.screen.refresh()
    except QuitGame:
        stop = True
    
    
#os.environ.setdefault('ESCDELAY', '25')
# doesn't seem to be working...
wrapper(main)
