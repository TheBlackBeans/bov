import state, curses, color

class ActionFrame(state.Frame):
    def reset(self):
        self.action.delete()
        self.action = None
        state.keyhandler.disable_handler(state.PRIORITIES["Action"])
    def _post_init(self):
        self.action = None
        state.keyhandler.add_handler(state.PRIORITIES["Action"])(self.get_key)
        state.keyhandler.disable_handler(state.PRIORITIES["Action"])
    def load_action(self, action):
        if self.action:
            self.action.delete()
        self.action = action
        state.keyhandler.enable_handler(state.PRIORITIES["Action"])
    def do_action(self):
        if self.action:
            if not self.action.do_action(): return
            self.reset()
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
        elif key == ord(":"): # ESC
            self.reset()
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

class Action:
    def __init__(self, name, args, action):
        self.name = name
        self.args = args
        self.action = action
        self.index = 0
    def select_n(self):
        if not self.args:
            return
        if self.index < len(self.args)-1:
            self.index += 1
    def select_p(self):
        if self.index > 0:
            self.index -= 1
    def select_n_unselected(self):
        for i in range(len(self.args)):
            if self.args[i].value == None:
                self.index = i
                return
    def select(self):
        if self.args:
            self.args[self.index].prompt(self.select_n_unselected)
    def set_arg(self, arg, value):
        self.args[arg].set_value(value)
    def repr_string(self):
        return " ".join(str(e) if ((i-1) != self.index or i==0) else ("\\C5" + str(e) + "\\C1" if not e.active else "\\C6" + str(e) + "\\C1") for i, e in enumerate([self.name] + self.args))
    def do_action(self):
        if not all(arg.value for arg in self.args):
            return False
        self.action(*(arg.value for arg in self.args))
        return True
    def delete(self):
        if self.args:
            for arg in self.args:
                arg.reset()
        self.index = 0

class Argument:
    def __init__(self, name, type):
        self.name = name
        self.default_type = type
        self.default = "<" + name + ">"
        self.active = False
        self.reset()
    def reset(self):
        self.reset_value()
        self.release()
        self.type = self.default_type(self.set_value)
        self.next = None
    def release(self):
        if self.active:
            self.type.release()
            self.active = False
    def reset_value(self):
        self.value = None
        self.repr = self.default
    def set_value(self, value):
        self.value = value
        self.repr = str(value)
        self.release()
        if self.next:
            self.next()
    def is_set(self):
        return not self.value == None
    def prompt(self, next):
        self.next = next
        if not self.active:
            self.type()
            self.active = True
    def __str__(self):
        return self.repr
            
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
            state.game_frame.window.add_highlight((ny, nx))
    def release(self):
        state.keyhandler.remove_handler(state.PRIORITIES["Argument"])
    def return_pos(self):
        self.returner(state.sub_tuples(self.pos, state.game_frame.window.offset))
    def __call__(self):
        self.pos = state.add_tuples(state.game_frame.creatures[0].pos, state.game_frame.window.offset)
        state.game_frame.window.add_highlight(self.pos)
        state.keyhandler.add_handler(state.PRIORITIES["Argument"])(self.get_key)

def look(pos, uesless):
    if pos in state.game_frame.window.map:
        if state.game_frame.creatures[0].pos == pos:
            state.message("You!", source="look")
        elif state.game_frame.window.map[pos].wall:
            state.message("Tile not walkable", source="look")
        else:
            state.message("Tile walkable", source="look")
    else:
        state.message("Not a tile", source="look")

look_action = Action(
    "look",
    [Argument("pos", PromptPos), Argument("useless", PromptPos)],
    look
)

quit_action = Action(
    "quit",
    [],
    lambda: state.quit()
)

idle_action = Action(
    "idle",
    [],
    lambda: state.game_frame.take_turn()
)
