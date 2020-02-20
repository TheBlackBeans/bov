import state, curses, color

class ActionFrame(state.Frame):
    def _post_init(self):
        self.action = None
        state.keyhandler.add_handler(state.PRIORITIES["Action"])(self.get_key)
        state.keyhandler.disable_handler(state.PRIORITIES["Action"])
    def load_action(self, action):
        self.action = action
        state.keyhandler.enable_handler(state.PRIORITIES["Action"])
    def do_action(self):
        if self.action:
            self.action.do_action()
        self.action = None
        state.keyhandler.disable_handler(state.PRIORITIES["Action"])
    def get_key(self, key):
        if key in state.ENTER_ALIASES:
            self.do_action()
        elif key == curses.KEY_RIGHT:
            self.action.select_n()
        elif key == curses.KEY_LEFT:
            self.action.select_p()
        elif key in {curses.KEY_UP, curses.KEY_DOWN}:
            pass
        elif key == ord(" "):
            self.action.select()
        else:
            return False
        return True


class ActionWindow(state.Window):
    def draw(self):
        self.border()
        self.draw_action()
    def draw_action(self):
        if state.action_frame.action:
            self.addstr(1, 1, state.action_frame.action.repr_string())

class Argument:
    def __init__(self, name, type):
        self.name = name
        self.type = type(self.set_value)
        self.default = "<" + name + ">"
        self.repr = self.default
        self.value = None
    def reset_value(self):
        self.value = None
        self.repr = self.default
    def set_value(self, value):
        self.value = value
        self.repr = str(value)
    def is_set(self):
        return not self.value == None
    def prompt(self):
        self.type()
    def __str__(self):
        return self.repr
            
class Action:
    def __init__(self, name, args, action, msg=None):
        self.name = name
        self.args = args
        self.action = action
        self.msg = msg
        self.index = 0
    def select_n(self):
        if self.index < len(self.args):
            self.index += 1
    def select_p(self):
        if self.index > 0:
            self.index -= 1
    def select(self):
        if self.index != 0:
            self.args[self.index-1].prompt()
    def set_arg(self, arg, value):
        self.args[arg].set_value(value)
    def repr_string(self):
        return " ".join(str(e) if (i != self.index) else "\\C5" + str(e) + "\\C1" for i, e in enumerate([self.name] + self.args))
    def do_action(self):
        self.action(*self.args)
        if self.msg:
            state.message(self.msg)

class PromptPos:
    def __init__(self, returner):
        self.returner = returner
    def get_key(self, key):
        if key == curses.KEY_DOWN:
            self.move(state.DOWN)
        elif key == curses.KEY_UP:
            self.move(state.UP)
        elif key == curses.KEY_RIGHT:
            self.move(state.RIGHT)
        elif key == curses.KEY_LEFT:
            self.move(state.LEFT)
        elif key in state.ENTER_ALIASES:
            self.return_pos()
        else:
            return False
        return True
    def move(self, dir):
        ny, nx = state.add_tuples(self.pos, dir)
        if 1 <= ny < state.game_frame.window.height-1 and 1 <= nx < state.game_frame.window.width-1:
            self.pos = (ny, nx)
            self.returner(self.pos)
            state.game_frame.window.addch(ny, nx, "%")
            #curses.setsyx(*state.add_tuples(self.pos, (state.game_frame.window.y-1, state.game_frame.window.x-1)))
            
    def return_pos(self):
        curses.curs_set(self._previous)
        state.keyhandler.remove_handler(state.PRIORITIES["Argument"])
        self.returner(self.pos)
    def __call__(self):
        self._previous = curses.curs_set(2)
        self.pos = state.game_frame.creatures["hero"].pos
        state.keyhandler.add_handler(state.PRIORITIES["Argument"])(self.get_key)

def look(pos):
    if pos in state.game_frame.window.map:
        state.message("Tile %s" % "walkable" if not state.game_frame.map[pos].wall else "wall")
    else:
        state.message("Not a tile")
        
look_action = Action(
    "look",
    [Argument("pos", PromptPos)],
    look,
    ""
)

quit_action = Action(
    "quit",
    [],
    lambda: state.quit(),
    ""
)
