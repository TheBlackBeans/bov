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
        self.offset = 0
    def update_messages(self, message):
        for msg in message.split("\n"):
            self.messages.append(msg)
        self.get_messages()
    def split_message(self, msg, width):
        return [msg[i*width:(i+1)*width] for i in range(ceil(len(msg)/width))]
    def get_messages(self):
        self.msg = []
        height = self.height - 2
        width = self.width - 3
        line_skiped = 0
        for message in self.messages[::-1]:
            for line in self.split_message(message, width)[::-1]:
                line_skiped += 1
                if line_skiped <= self.offset:
                    continue
                if len(self.msg) >= height:
                    break
                self.msg.insert(0, line)
            if len(self.msg) >= height:
                break
    def page_up(self):
        self.offset += 3
        self.get_messages()
    def page_down(self):
        self.offset -= 3
        self.offset = max(self.offset, 0)
        self.get_messages()
    def draw_messages(self):
        offset = self.height-len(self.msg)-2
        for i, line in enumerate(self.msg):
            self.addstr(i+1+offset, 1, line)
    def draw(self):
        self.border()
        self.draw_messages()
    
def main(stdscr):
    stop = False
    color.init_curses_color()
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
    mw_width = 2*sc_width//5+1
    state.message_window = MessageWindow(
        state.screen,
        sc_height - mw_height,
        0,
        mw_height,
        mw_width
    )

    aw_height = 3
    aw_width = 2*sc_width//5+1
    action_window = ActionWindow(
        state.screen,
        sc_height - (aw_height + mw_height),
        0,
        aw_height,
        aw_width
    )

    iw_height = sc_height - (6+aw_height+mw_height)
    iw_width = 2*sc_width//5+1
    state.inventory_window = InventoryWindow(
        state.screen,
        sc_height - (aw_height+mw_height+iw_height),
        0,
        iw_height,
        iw_width
    )
    
    armor = Armor(state.screen)
    resistance = Resistance(state.screen)
    life = Life(state.screen)
    mana = Mana(state.screen)
    coords = Coords(state.screen)
    turns = Turns(state.screen)

    hands = Hands(state.screen)
    
    state.game_frame = state.GameFrame(game_window)
    state.game_frame.load_map()
    state.action_frame = state.ActionFrame(action_window)
    state.action.init_actions()
    
    state.screen.add_window(state.message_window)
    state.screen.add_window(armor)
    state.screen.add_window(resistance)
    state.screen.add_window(life)
    state.screen.add_window(mana)
    state.screen.add_window(coords)
    state.screen.add_window(turns)
    state.screen.add_window(hands)
    state.screen.add_window(game_window)
    state.screen.add_window(action_window)
    state.screen.add_window(state.inventory_window)
    state.screen.refresh()
    try:
        while not stop:
            state.game_frame.take_turn()
    except QuitGame:
        stop = True
    
    
#os.environ.setdefault('ESCDELAY', '25')
# doesn't seem to be working...
wrapper(main)
