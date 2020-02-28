import state, curses, color, creature

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
        if not all(arg.value != None for arg in self.args):
            return False
        self.action(*(arg.value for arg in self.args))
        return True
    def delete(self):
        if self.args:
            for arg in self.args:
                arg.reset()
        self.index = 0

class ArgumentValue:
    def __init__(self, repr, value):
        self.repr = repr
        self.value = value
    def __str__(self):
        return self.repr
    def __bool__(self):
        return True
        
class Argument:
    def __init__(self, name, type):
        self.name = name
        self.type = type
        self.default = "<" + name + ">"
        self.active = False
        self.reset()
    def reset(self):
        self.reset_value()
        self.release()
        self.type(self.set_value)
        self.next = None
    def release(self):
        if self.active:
            self.type.release()
            self.active = False
    def reset_value(self):
        self.value = None
        self.repr = self.default
    def set_value(self, argument_value):
        self.repr, self.value = argument_value.repr, argument_value.value
        self.release()
        if self.next:
            self.next()
    def is_set(self):
        return not self.value == None
    def prompt(self, next):
        self.next = next
        if not self.active:
            self.type.prompt()
            self.active = True
    def __str__(self):
        return self.repr

class Type:
    def __call__(self, returner):
        self.returner = returner
    def _release(self):
        pass
    def release(self):
        self._release()
        state.keyhandler.remove_handler(state.PRIORITIES["Argument"])
    def init(self):
        pass
    def prompt(self):
        state.keyhandler.add_handler(state.PRIORITIES["Argument"])(self.get_key)
        self.init()

class AskWindow(state.Window):
        def __init__(self, parent, items, border=True):
            self.items = items
            self.parent = parent
            sc_height, sc_width = self.parent.size
            self.height = len(items)+2
            self.width = 2*sc_width//3
            self.y = sc_height//2-(self.height//2)
            self.x = sc_width//2-(self.width//2)
            self.size = (self.height, self.width)
            self.index = 0
            self._border = border
        def clean(self):
            for i in range(self.height):
                self.addstr(i, 0, " "*(self.width-1))
        def draw_menu(self):
            for i in range(len(self.items)):
                color = 1 if i != self.index else 6
                self.addstr(i+1, 1, self.items[i], color=color)
        def select_n(self):
            if self.index < len(self.items)-1:
                self.index += 1
        def select_p(self):
            if self.index > 0:
                self.index -= 1 
        def draw(self):
            self.clean()
            self.border()
            self.draw_menu()
            
class AskFromList(Type):
    def __init__(self, items):
        # items: [(repr, value)]
        # shows repr, returns value
        self.items = items
    def init(self):
        self.window = AskWindow(state.screen, [repr for repr, value in self.items])
        state.screen.add_window(self.window)
    def _release(self):
        state.screen.remove_window(self.window)
    def get_key(self, key):
        if key == curses.KEY_DOWN:
            self.window.select_n()
        elif key == curses.KEY_UP:
            self.window.select_p()
        elif key in state.ENTER_ALIASES:
            self.returner(ArgumentValue(*self.items[self.window.index]))
        elif key == ord(":"):
            return False # allow exit
        return True
        
    
class PromptType(Type):
    def init(self):
        self.init_pos()
        state.game_frame.window.add_highlight(self.pos)
    def pos_to_realpos(self, pos):
        return state.sub_tuples(self.pos, state.game_frame.window.offset)
    def init_pos(self):
        self.pos = (0,0)
    def check_pos(self, pos):
        return True
    def check_pos_return(self, pos):
        return True
    def check_realpos_return(self, pos):
        return True
    def return_pos(self):
        pos = self.convert_pos(self.pos)
        self.returner(ArgumentValue(str(pos), pos))
    def get_key(self, key):
        
        if key == curses.KEY_DOWN:
            self.move(state.DOWN)
        elif key == curses.KEY_RIGHT:
            self.move(state.RIGHT)
        elif key == curses.KEY_LEFT:
            self.move(state.LEFT)
        elif key == curses.KEY_UP:
            self.move(state.UP)
        elif key in state.ENTER_ALIASES:
            if self.check_pos_return(self.pos) and self.check_realpos_return(self.pos_to_realpos(self.pos)):
                self.return_pos()
            else:
                self.move((0,0))
        else:
            return False
        return True
    def convert_pos(self, pos):
        return self.pos_to_realpos(pos)
    def move(self, dir):
        ny, nx = state.add_tuples(self.pos, dir)
        if 1 <= ny < state.game_frame.window.height-1 and 1 <= state.game_frame.window.width-1 and self.check_pos((ny,nx)):
            self.pos = (ny, nx)
        state.game_frame.window.add_highlight(self.pos)
            
class PromptCreature(PromptType):
    def __init__(self, check_range=lambda x: True):
        self.check_range = check_range
    def init_pos(self):
        self.pos = state.add_tuples(state.game_frame.get_hero().pos, state.game_frame.window.offset)
        self.base_pos = self.pos
    def convert_pos(self, pos):
        return state.game_frame.window.map[self.pos_to_realpos(pos)].creatures[0]
    def check_pos(self, pos):
        if self.check_range(state.distance(self.base_pos, pos)):
            return True
        return False
    def check_realpos_return(self, pos):
        return state.game_frame.window.map[pos] and len(state.game_frame.window.map[pos].creatures) > 0
        
class PromptPos(PromptType):
    def __init__(self, check_realpos_r=None):
        if check_realpos_r:
            self.check_realpos_return = check_realpos_r
    def init_pos(self):
        self.pos = state.add_tuples(state.game_frame.get_hero().pos, state.game_frame.window.offset)
        
        state.keyhandler.add_handler(state.PRIORITIES["Argument"])(self.get_key)

        
def look(pos):
    for uuid in state.game_frame.window.map[pos].creatures:
        creature = state.game_frame.get_creature(uuid)
        if creature.max_life <= creature.life:
            condition = "very healthy"
        elif creature.life >= 3*creature.max_life//5:
            condition = "healthy"
        elif creature.life >= creature.max_life//5:
            condition = "wounded"
        elif creature.life >= creature.max_life//10:
            condition = "severly wounded"
        elif creature.life > 0:
            condition = "almost dead"
        else:
            condition = "dead"
        state.message("You look at a %s (id=%s), which looks %s" % (str(creature), creature.creature_id, condition), source="look")
        return
    if state.game_frame.window.map[pos]:
        if state.game_frame.window.map[pos].wall:
            state.message("Tile not walkable", source="look")
        else:
            state.message("Tile walkable", source="look")
    else:
        state.message("Nothing...", source="look")

def idle():
    state.game_frame.played = True

def attack(creature):
    state.game_frame.get_hero().attack(creature, state.game_frame.get_hero().strenght)
    state.game_frame.played = True

def left():
    if state.game_frame.is_walkable(state.add_tuples(state.game_frame.get_hero().pos, state.LEFT)):
        state.game_frame.get_hero().move(state.LEFT)
        state.game_frame.played = True
def up():
    if state.game_frame.is_walkable(state.add_tuples(state.game_frame.get_hero().pos, state.UP)):
        state.game_frame.get_hero().move(state.UP)
        state.game_frame.played = True
def right():
    if state.game_frame.is_walkable(state.add_tuples(state.game_frame.get_hero().pos, state.RIGHT)):
        state.game_frame.get_hero().move(state.RIGHT)
        state.game_frame.played = True
        
def down():
    if state.game_frame.is_walkable(state.add_tuples(state.game_frame.get_hero().pos, state.DOWN)):
        state.game_frame.get_hero().move(state.DOWN)
        state.game_frame.played = True

def turnmode(mode):
    state.message("move mode set to %s" % ({0: "real time", 1: "turn-by-turn"}[mode]), source="movemode")
    state.game_frame.move_mode = mode

def save():
    state.game_frame.window.map.save()

def create(entity, pos):
    creature = entity(pos=pos)
    state.game_frame.create_creature(creature)
    state.message("created %s at %s" % (creature, pos), source="create")

def delete(pos):
    res = len(state.game_frame.window.map[pos].creatures)
    state.game_frame.remove_creatures_pos(pos)
    state.message("deleted %s entities at %s" % (res, pos), source="delete")

def coords(pos):
    state.message(pos, source="coords")

def vertexes(pos):
    state.message(state.game_frame.window.compute_vertex(state.game_frame.get_creature(state.game_frame.hero_uuid).pos, pos), source="vertexes")

def switch():
    if state.game_frame.window.hide:
        state.game_frame.window.map.lit()
        state.game_frame.window.hide = False
    else:
        state.game_frame.window.hide = True
        
def shadow(pos1, pos2):
    pos = state.game_frame.get_hero().pos
    w = state.game_frame.window
    shadow1 = w.compute_shadow(pos1,pos2)
    a1 = state.rad2deg(shadow1.left)
    a2 = state.rad2deg(shadow1.right)
    state.message("Shadow: %s-%s" % (int(a1), int(a2)))
        
def init_actions():
    global look_action, quit_action, idle_action, attack_action, left_action, up_action, right_action, down_action, left_action, move_mode_action, save_action, create_action, delete_action, delete_action, vertexes_action, coords_action, switch_action, shadow_action
    look_action = Action(
        "look",
        [Argument("pos", PromptPos())],
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
        idle
    )

    attack_action = Action(
        "attack",
        [Argument("target", PromptCreature(check_range=lambda x: x<5))],
        attack
    )

    # moves
    left_action = Action(
        "left",
        [],
        left
    )

    up_action = Action(
        "up",
        [],
        up
    )

    right_action = Action(
        "right",
        [],
        right
    )

    down_action = Action(
        "down",
        [],
        down
    )

    move_mode_action = Action(
        "turnmode",
        [Argument("mode", AskFromList([("real time", 0), ("turn-by-turn", 1)]))],
        turnmode
    )

    save_action = Action(
        "save",
        [],
        save
    )

    create_action = Action(
        "create",
        [Argument("entity", AskFromList([("daemon", creature.Daemon), ("soul", creature.Soul)])), Argument("pos", PromptPos(check_realpos_r=state.game_frame.is_walkable))],
        create
    )

    delete_action = Action(
        "delete",
        [Argument("pos", PromptPos())],
        delete
    )

    coords_action = Action(
        "coords",
        [Argument("pos", PromptPos())],
        coords
    )

    vertexes_action = Action(
        "vertexes",
        [Argument("pos", PromptPos())],
        vertexes
    )

    switch_action = Action(
        "switch",
        [],
        switch
    )

    shadow_action = Action(
        "shadow",
        [Argument("pos1", PromptPos()), Argument("pos2", PromptPos())],
        shadow
    )
