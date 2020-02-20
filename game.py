import state, curses

class GameFrame(state.Frame):
    def _post_init(self, hero):
        self.creatures = {"hero": hero}
        self.load_map()
        state.keyhandler.add_handler(state.PRIORITIES["Game"])(self.get_key)
    def get_key(self, key):
        if key in state.QUIT_ALIASES:
            state.action_frame.load_action(
                state.action.quit_action
            )
        elif key == ord("l"):
            state.action_frame.load_action(
                state.action.look_action
            )
        elif key == curses.KEY_DOWN:
            self.move("hero", state.DOWN)
        elif key == curses.KEY_UP:
            self.move("hero", state.UP)
        elif key == curses.KEY_RIGHT:
            self.move("hero", state.RIGHT)
        elif key == curses.KEY_LEFT:
            self.move("hero", state.LEFT)
    def load_map(self):
        self.window.map = {}
        with open("maps/map2.mp") as f:
            for y, line in enumerate(f.read().split("\n")):
                for x, c in enumerate(line):
                    if c == "@":
                        self.creatures["hero"].pos = (y,x)
                        self.window.map[y, x] = state.Tile(".", False)
                    elif c == ".":
                        self.window.map[y, x] = state.Tile(c, False)
                    elif c == "#":
                        self.window.map[y, x] = state.Tile(c, True)
    def move(self, what, dir):
        y, x = state.add_tuples(self.creatures[what].pos, dir)
        if (y, x) in self.window.map and not self.window.map[y, x].wall:
            self.creatures[what].move(dir)
            return True
        return False

class GameWindow(state.Window):
    def _post_init(self):
        self.offset = (1,2)
    def draw(self):
        self.regulate_offset()
        self.border()
        self.draw_map()
        self.draw_creatures()
    def draw_map(self):
        for y in range(1, self.height-1):
            for x in range(1, self.width-3):
                # real x and y
                ry, rx = state.sub_tuples((y, x), self.offset)
                if (ry, rx) in self.map:
                    self.addch(y, x, self.map[ry, rx].draw())
    def draw_creatures(self):
        for creature in state.game_frame.creatures.values():
            self.addch(*state.add_tuples(creature.pos, self.offset), creature.char, curses.color_pair(creature.color))
    def regulate_offset(self):
        while state.game_frame.creatures["hero"].pos[0] + self.offset[0] <= 2:
            self.offset = state.add_tuples(self.offset, (1, 0))
        while state.game_frame.creatures["hero"].pos[0] + self.offset[0] >= self.height-3:
            self.offset = state.add_tuples(self.offset, (-1, 0))
        while state.game_frame.creatures["hero"].pos[1] + self.offset[1] <= 2:
            self.offset = state.add_tuples(self.offset, (0, 1))
        while state.game_frame.creatures["hero"].pos[1] + self.offset[1] >= self.width-4:
            self.offset = state.add_tuples(self.offset, (0, -1))
