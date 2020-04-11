import state, curses, color, creature, math, string, os

class ActionFrame(state.Frame):
    def reset(self):
        self.action.delete()
        self.action = None
        state.keyhandler.disable_handler(state.PRIORITIES["Action"])
    def _post_init(self):
        self.action = None
        state.keyhandler.add_handler(state.PRIORITIES["Action"])(self.get_key)
        state.keyhandler.disable_handler(state.PRIORITIES["Action"])
        self.autotrigger = False
    def load_action(self, action):
        if self.action:
            self.action.delete()
        self.action = action
        state.keyhandler.enable_handler(state.PRIORITIES["Action"])
        if self.autotrigger:
            self.do_action()
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
        elif key in state.ARGQUIT_ALIASES: # ESC
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
        return " ".join(str(e) if ((i-1) != self.index or i==0) else ("\\C5;" + str(e) + "\\C1;" if not e.active else "\\C6;" + str(e) + "\\C1;") for i, e in enumerate([self.name] + self.args))
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

class AskListWindow(state.Window):
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

class AskStringWindow(state.Window):
    def __init__(self, parent, max_string=float("inf"), border=True):
        self.parent = parent
        sc_height, sc_width = self.parent.size
        self.height = 3
        self.width = min(2*sc_width//3,max_string+3)
        self.y = sc_height//2-(self.height//2)
        self.x = sc_width//2-(self.width//2)
        self.size = (self.height, self.width)
        self.max_string = max_string
        self.index = 0
        self.offset = 0
        self.string = ""
        self._border = border
    def clean(self):
        self.addstr(1,0," "*(self.width-2))
    def draw_string(self):
        string = self.string[self.offset:self.offset+self.width-3]
        if string:
            string = string[:self.index-1] + '\\C5;' + string[self.index-1] + '\\C1;' + string[self.index:]
        self.addstr(1,1,string)
    def select_p(self):
        if self.index == 1:
            if self.offset > 0:
                self.offset -= 1
        else:
            self.index -= 1
    def select_n(self):
        if self.index < self.width-3 and self.index < len(self.string)-self.offset:
            self.index += 1
        elif self.index < len(self.string) - self.offset:
            self.offset += 1
    def add_char(self, char):
        if len(self.string) < self.max_string:
            self.string = self.string[:self.index]+char+self.string[self.index:]
        self.select_n()
    def del_char(self):
        if self.string:
            self.string = self.string[:self.index-1]+self.string[self.index:]
        self.select_p()
    def draw(self):
        self.clean()
        self.border()
        self.draw_string()
        
            
class AskString(Type):
    def __init__(self, max_string=float("inf")):
        self.max_string = max_string
    def init(self):
        self.window = AskStringWindow(state.screen, self.max_string)
        state.screen.add_window(self.window)
    def _release(self):
        state.screen.remove_window(self.window)
    def get_key(self, key):
        if key == curses.KEY_RIGHT:
            self.window.select_n()
        elif key == curses.KEY_LEFT:
            self.window.select_p()
        elif key in state.ENTER_ALIASES:
            self.returner(ArgumentValue(self.window.string, self.window.string))
        elif key in state.ARGQUIT_ALIASES:
            return False # allow exit
        elif chr(key) in string.ascii_letters + string.digits + '-_#@()[]{}+=$|':
            self.window.add_char(chr(key))
        elif key in state.BACKSPACE_ALIASES:
            self.window.del_char()
        return True


            
class AskFromList(Type):
    def __init__(self, items):
        # items: [(repr, value)]
        # shows repr, returns value
        self.items = items
    def init(self):
        self.window = AskListWindow(state.screen, [repr for repr, value in self.items])
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
        elif key in state.ARGQUIT_ALIASES:
            return False # allow exit
        return True
        
class AskItem(AskFromList):
    def __init__(self):
        pass
    def init(self):
        self.pos = state.game_frame.get_hero().pos
        self.items = [(str(state.game_frame.get_creature(c)), c) for c in state.game_frame.window.map[self.pos].creatures if state.game_frame.get_creature(c).is_pickable]
        self.window = AskListWindow(state.screen, [repr for repr, item in self.items])
        state.screen.add_window(self.window)

    
class ListProxy:
    def __init__(self, value):
        self.value = value
    def __getitem__(self, index):
        return str(index), self.value[index]
    def __iter__(self):
        return (self[i] for i in range(len(self.value)))

class TileProxy:
    def __init__(self, pos):
        self.pos = pos
    @property
    def creatures(self):
        return state.game_frame.window.map[tuple(self.pos)].creatures

class HeroPosProxy:
    def __getitem__(self, index):
        return state.game_frame.get_hero().pos[index]
    
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
    def str_pos(self, pos):
        return str(pos)
    def check_realpos_return(self, pos):
        return True
    def return_pos(self):
        pos = self.convert_pos(self.pos)
        self.returner(ArgumentValue(self.str_pos(pos), pos))
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
        realpos = state.sub_tuples((ny,nx), state.game_frame.window.offset)
        if 1 <= ny < state.game_frame.window.height-1 and 1 <= state.game_frame.window.width-1 and self.check_pos((ny,nx)) and state.game_frame.window.map[realpos] and state.game_frame.window.map[realpos].lit == 2:
            self.pos = (ny, nx)
        state.game_frame.window.add_highlight(self.pos)
            
class PromptCreature(PromptType):
    def __init__(self, check_range=lambda x: True):
        self.check_range = check_range
    def str_pos(self, pos):
        return str(state.game_frame.get_creature(pos))
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
        

class PromptLock(PromptType):
    def __init__(self, max_range=1):
        self.max_range = max_range
    def check_realpos_return(self, pos):
        return state.game_frame.window.map[pos] and state.game_frame.window.map[pos].openable and len(state.game_frame.window.map[pos].creatures) == 0
    def init_pos(self):
        self.pos = state.add_tuples(state.game_frame.get_hero().pos, state.game_frame.window.offset)
        self.base_pos = self.pos
    def check_pos(self, pos):
        return state.distance(self.base_pos, pos) <= self.max_range
        
        
def look(pos):
    for uuid in state.game_frame.window.map[pos].creatures:
        entity = state.game_frame.get_creature(uuid)
        if entity.creature_id not in creature.alive_creatures:
            state.output("You look at a %s (id=%s)" % (str(entity), entity.creature_id))
            return
        if entity.max_life <= entity.life:
            condition = "very healthy"
        elif entity.life >= 3*entity.max_life//5:
            condition = "healthy"
        elif entity.life >= entity.max_life//5:
            condition = "wounded"
        elif entity.life >= entity.max_life//10:
            condition = "severly wounded"
        elif entity.life > 0:
            condition = "almost dead"
        else:
            condition = "dead"
        state.output("You look at a %s (id=%s), which looks %s" % (str(entity), entity.creature_id, condition))
        return
    if state.game_frame.window.map[pos]:
        if state.game_frame.window.map[pos].wall:
            state.output("%s (not walkable)" % state.game_frame.window.map[pos].desc.capitalize())
        else:
            state.output("%s (walkable)" % state.game_frame.window.map[pos].desc.capitalize())
    else:
        state.output("Nothing...")

def idle():
    state.game_frame.played = True
    state.output("idle")

def attack(entity):
    state.game_frame.get_hero().attack(entity)
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
    state.output("move mode set to %s" % ({0: "real time", 1: "turn-by-turn"}[mode]))
    state.game_frame.move_mode = mode

def save():
    if state.game_frame.window.map.save() == 0:
        state.output("cannot save")
    else:
        state.output("saved into %s" % state.game_frame.window.map.file)

def create(entity, pos):
    creature = entity(pos=pos)
    state.game_frame.create_creature(creature)
    state.output("created %s at %s" % (creature, pos))

def delete(pos):
    res = len(state.game_frame.window.map[pos].creatures)
    state.game_frame.remove_creatures_pos(pos)
    state.output("deleted %s entities at %s" % (res, pos))

def coords(pos):
    state.output(pos)

def vertexes(pos):
    state.output(state.game_frame.window.compute_vertex(state.game_frame.get_creature(state.game_frame.hero_uuid).pos, pos))

def switch():
    if state.game_frame.window.hide:
        state.game_frame.window.map.lit()
        state.game_frame.window.hide = False
    else:
        state.game_frame.window.hide = True
    state.output("switched")
        
def shadow(pos1):
    pos = state.game_frame.get_hero().pos
    w = state.game_frame.window
    shadow = w.compute_shadow(pos,pos1)
    a1 = state.rad2deg(shadow.start)
    a2 = state.rad2deg(shadow.start+shadow.lenght)
    state.output("Shadow #%s: %s=>%s" % (len(state.game_frame.shadows), int(a1), int(a2)))
    state.game_frame.shadows.append(shadow)

def join(shadow1, shadow2):
    shadow = shadow1.copy()
    shadow.join(shadow2)
    a1 = state.rad2deg(shadow.start)
    a2 = state.rad2deg(shadow.start+shadow.lenght)
    state.output("Shadow #%s: %s=>%s" % (len(state.game_frame.shadows), int(a1), int(a2)))
    state.game_frame.shadows.append(shadow)

def compare(shadow1, shadow2):
    state.output("1 in 2:  %s" % (shadow1 in shadow2))
    state.output("2 in 1:  %s" % (shadow2 in shadow1))
    state.output("1 >in 2: %s" % shadow2.strictly_contains(shadow1))
    state.output("2 >in 1: %s" % shadow1.strictly_contains(shadow2))

def name(entity, name):
    state.game_frame.get_creature(entity).str = name
    state.output("Entity renamed")

def open_(pos):
    door = state.game_frame.window.map[pos]
    if door.wall == True:
        state.output("Lock opened")
        door.wall = False
        door.obscure = False
    else:
        state.output("Lock is already open")

def close(pos):
    door = state.game_frame.window.map[pos]
    if door.wall == False:
        state.output("Lock closed")
        door.wall = True
        door.obscure = True
    else:
        state.output("Lock is already closed")

def pickup(item):
    state.game_frame.window.map[state.game_frame.get_hero().pos].remove_creature(item)
    state.game_frame.get_hero().inventory.add_item(state.game_frame.get_creature(item))
    state.output("pickup item")
    
def load(map_name):
    if not map_name.endswith(".mp"):
        map_name += ".mp"
    file = os.path.join(state.BASEDIR, "maps", map_name)
    state.game_frame.window.map.load_file(file)
    state.output("Map loaded!")

def autotrigger():
    state.action_frame.autotrigger ^= True
    state.output("Changed command trigger mode")

def neighboors(pos):
    state.output(state.game_frame.window.map.adapt_neighboors(pos))
    state.output(state.game_frame.window.map[pos].family)
    
def help():
    state.output(
        """HELP - commands starting withing braces are debug only
q -> quit
l -> look
i -> idle
[arrows] -> move
a -> attack <target>
t -> turnmode <mode>
s -> save
[c] -> create <entity> <pos>
[d] -> delete <pos>
[z] -> vertexes <pos>
[e] -> coords <pos>
[r] -> switch
[d] -> shadow
[C] -> compare <shadow1> <shadow2>
n -> name <creature> <name>
[j] -> join <shadow1> <shadow2>
o -> open <door>
O -> close <door>
p -> pickup <item>
[C-l] -> load
C-x -> *exit current command*
next -> *scroll down messages*
prior -> *scoll up messages*
u -> switch autotrigger
[N] -> neighboors <pos>"""
    )
    
def init_actions():
    global look_action, quit_action, idle_action, attack_action, left_action, up_action, right_action, down_action, left_action, move_mode_action, save_action, create_action, delete_action, delete_action, vertexes_action, coords_action, switch_action, shadow_action, compare_action, name_action, join_action, open_action, close_action, pickup_action, load_action, help_action, switch_trigger_action, neighboors_action
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
        [Argument("entity", AskFromList([(entity.DEFAULT_STR(), entity) for entity in creature.creature_map.values()])), Argument("pos", PromptPos(check_realpos_r=state.game_frame.is_walkable))],
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
        [Argument("pos", PromptPos())],
        shadow
    )

    compare_action = Action(
        "compare",
        [Argument("shadow1", AskFromList(ListProxy(state.game_frame.shadows))), Argument("shadow2", AskFromList(ListProxy(state.game_frame.shadows)))],
        compare
    )

    join_action = Action(
        "join",
        [Argument("shadow1", AskFromList(ListProxy(state.game_frame.shadows))), Argument("shadow2", AskFromList(ListProxy(state.game_frame.shadows)))],
        join
    )

    name_action = Action(
        "name",
        [Argument("creature", PromptCreature()), Argument("name", AskString())],
        name
    )

    open_action = Action(
        "open",
        [Argument("lock", PromptLock())],
        open_
    )

    close_action = Action(
        "close",
        [Argument("lock", PromptLock())],
        close
    )

    pickup_action = Action(
        "pickup",
        [Argument("item", AskItem())],
        pickup
    )
    load_action = Action(
        "load",
        [Argument("map", AskString())],
        load
    )
    help_action = Action(
        "help",
        [],
        help
    )
    switch_trigger_action = Action(
        "switch autotrigger",
        [],
        autotrigger
    )
    neighboors_action = Action(
        "neighboors",
        [Argument("pos", PromptPos())],
        neighboors
    )
