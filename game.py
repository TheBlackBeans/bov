import state, curses, random

class GameFrame(state.Frame):
    def _post_init(self, hero):
        self.creatures = [hero]
        self.load_map()
        state.keyhandler.add_handler(state.PRIORITIES["Game"])(self.get_key)
    def take_turn(self):
        for creature in range(len(self.creatures)-1):
            moves = [state.UP,state.RIGHT,state.LEFT,state.DOWN]
            random.shuffle(moves)
            for dir in moves:
                if self.move(creature+1, dir): break
    def get_key(self, key):
        if key in state.QUIT_ALIASES:
            state.action_frame.load_action(
                state.action.quit_action
            )
        elif key == ord("l"):
            state.action_frame.load_action(
                state.action.look_action
            )
        elif key == ord("i"):
            state.action_frame.load_action(
                state.action.idle_action
            )
        elif key == curses.KEY_DOWN:
            if self.move(0, state.DOWN): self.take_turn()
        elif key == curses.KEY_UP:
            if self.move(0, state.UP): self.take_turn()
        elif key == curses.KEY_RIGHT:
            if self.move(0, state.RIGHT): self.take_turn()
        elif key == curses.KEY_LEFT:
            if self.move(0, state.LEFT): self.take_turn()
        else:
            return False
        return True
    def load_map(self):
        self.window.map = {}
        with open("maps/map2.mp") as f:
            for y, line in enumerate(f.read().split("\n")):
                for x, c in enumerate(line):
                    if c == "@":
                        self.creatures[0].pos = (y,x)
                        self.window.map[y, x] = state.Tile(".", False)
                    elif c == "&":
                        self.creatures.append(state.Daemon(pos=(y,x)))
                        self.window.map[y, x] = state.Tile(".", False)
                    elif c == ".":
                        self.window.map[y, x] = state.Tile(c, False)
                    elif c == "#":
                        self.window.map[y, x] = state.Tile(c, True)
    def move(self, what, dir):
        y, x = state.add_tuples(self.creatures[what].pos, dir)
        if (y, x) in self.window.map and not self.window.map[y, x].wall:
            if (y,x) not in {creature.pos for i, creature in enumerate(self.creatures) if i != what}:
                self.creatures[what].move(dir)
                return True
        return False

class GameWindow(state.Window):
    def _post_init(self):
        self.offset = (1,2)
        self.highlights = set()
    def add_highlight(self, pos):
        self.highlights.add(pos)
    def draw(self):
        self.regulate_offset()
        self.border()
        self.draw_map()
        self.draw_creatures()
        self.draw_highlights()
    def draw_highlights(self):
        for y, x in self.highlights:
            self.parent.chgat(self.y+y, self.x+x, 1, curses.color_pair(5)|curses.A_BOLD)
        self.highlights = set()
    def draw_map(self):
        for y in range(1, self.height-1):
            for x in range(1, self.width-2):
                # real x and y
                ry, rx = state.sub_tuples((y, x), self.offset)
                if (ry, rx) in self.map:
                    self.addch(y, x, self.map[ry, rx].draw())
    def in_rect(self, y, x):
        return 1 <= y < self.height-1 and 1 <= x < self.width-2
    def draw_creatures(self):
        for creature in state.game_frame.creatures:
            if self.in_rect(*state.add_tuples(creature.pos, self.offset)):
                self.addch(*state.add_tuples(creature.pos, self.offset), creature.char, curses.color_pair(creature.color))
    def regulate_offset(self):
        while state.game_frame.creatures[0].pos[0] + self.offset[0] <= 2:
            self.offset = state.add_tuples(self.offset, (1, 0))
        while state.game_frame.creatures[0].pos[0] + self.offset[0] >= self.height-3:
            self.offset = state.add_tuples(self.offset, (-1, 0))
        while state.game_frame.creatures[0].pos[1] + self.offset[1] <= 2:
            self.offset = state.add_tuples(self.offset, (0, 1))
        while state.game_frame.creatures[0].pos[1] + self.offset[1] >= self.width-4:
            self.offset = state.add_tuples(self.offset, (0, -1))
