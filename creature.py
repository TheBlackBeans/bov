import state, random, items, queue, items, os

def options(pos):
    for dir in {state.UP, state.RIGHT, state.DOWN, state.LEFT}:
        newpos = state.add_tuples(pos, dir)
        if state.game_frame.window.map[newpos] and not state.game_frame.window.map[newpos].wall:
            yield newpos

def heuristic(pos, goal):
    y1, x1 = pos
    y2, x2 = pos
    return abs(y1-y2)+abs(x1-x2)
            
def a_star(start, end):
    border = queue.PriorityQueue()
    border.put_nowait((0, start))
    came_from = {start: None}
    cost_so_far = {start: 0}
    while border.qsize() > 0:
        distance, current = border.get_nowait()
        if current == end:
            break
        for next in options(current):
            new_cost = cost_so_far[current] + 1
            if next not in cost_so_far or new_cost < cost_so_far[next]:
                cost_so_far[next] = new_cost
                came_from[next] = current
                border.put_nowait((heuristic(next, end) + new_cost, next))
    return came_from

def reconstruct_path(came_from, start, end):
    current = end
    path = []
    while current != start:
        path.append(current)
        current = came_from[current]
    path.reverse()
    return tuple(path)

def shortest_path(start, end):
    came_from = a_star(start, end)
    return reconstruct_path(came_from, start, end)

class RemoveCorpse(BaseException):
    pass

class SaveInterface:
    def __init__(self, value_type, save_type, value):
        self.value_type = value_type
        self.save_type = save_type
        self.value = value
    def load(self, value):
        return self.value_type(value)
    def save(self, value):
        return self.save_type(value)
    def __call__(self):
        return self.load(self.value)
    def copy(self):
        return type(self)(self.value_type, self.save_type, self.value)

class Constructor:
    def __init__(self, type, args):
        self.type = type
        self.args = args
    def __call__(self):
        return self.type(*self.args)

    
class Creature:
    DEFAULT_IS_PICKABLE = SaveInterface(bool, bool, False)
    DEFAULT_CHAR = SaveInterface(str, str, "%")
    DEFAULT_POS = SaveInterface(tuple, list, (0,0))
    DEFAULT_COLOR = SaveInterface(int, int, 4)
    DEFAULT_SPEED = SaveInterface(int, int, 5)
    DEFAULT_LIFE = SaveInterface(int, int, 10)
    DEFAULT_MAX_LIFE = SaveInterface(int, int, 10)
    DEFAULT_MANA = SaveInterface(int, int, 0)
    DEFAULT_MAX_MANA = SaveInterface(int, int, 0)
    DEFAULT_STR = SaveInterface(str, str, "random creature")
    DEFAULT_ARMOR = SaveInterface(int, int, 20)
    DEFAULT_RESISTANCE = SaveInterface(int, int, 1)
    DEFAULT_STRENGHT = SaveInterface(int, int, 5)
    DEFAULT_MAX_WEIGHT = SaveInterface(int, int, 10)
    DEFAULT_WEIGHT = SaveInterface(int, int, 0)
    DEFAULT__DEAD = SaveInterface(bool, bool, False)
    DEFAULT_INVENTORY = SaveInterface(items.Inventory.load, items.Inventory.save, {"slots": None, "inventory": None})
    DEFAULT_CREATURE_ID = SaveInterface(int, int, 0)
    DEFAULT_UUID = SaveInterface(int, int, 0)
    DEFAULT_IS_HERO = SaveInterface(bool, bool, False)
    DEFAULT_IS_WALKABLE = SaveInterface(bool, bool, False)
    DEFAULT_EFFECTS = SaveInterface(list, list, [])
    DEFAULT_ALIVE = SaveInterface(bool, bool, True)
    CREATURE_ATTRIBUTES = {"is_pickable", "char", "pos", "color", "speed", "life", "max_life", "mana", "max_mana", "str", "armor", "resistance", "strenght", "max_weight", "weight", "inventory", "_dead", "creature_id", "uuid", "is_hero", "is_walkable", "effects", "alive"}
    def exec_trigger(self, trigger):
        cmd = trigger.split(" ",1)[0]
        args = trigger.split(" ",1)[1:]
        if cmd == "summon":
            crt = creature_map[int(args[0])](pos=self.pos)
            state.game_frame.create_creature(crt)
    def add_trigger(self, trigger, effect):
        self.triggers[trigger] = effect
    def __init__(self, **attributes):
        for key in attributes.keys():
            if key not in self.CREATURE_ATTRIBUTES:
                raise NameError("Attribute %s doesn't exist" % key)
        for key in self.CREATURE_ATTRIBUTES:
            attr = getattr(self, "DEFAULT_"+key.upper())
            value = attr()
            setattr(self, key, value)
        for key, value in attributes.items():
            dattr = getattr(self, "DEFAULT_"+key.upper())
            setattr(self, key, dattr.load(value))
        self.triggers = {}
        self._post_init()
    def is_dead(self):
        return self._dead
    def remove_item(self, item):
        self.current_weight += item.weight
        self.inventory.remove(item)
    def add_item(self, item):
        if item.weight <= self.weight - self.current_weight:
            self.inventory.append(item)
            self.current_weight += item.weight
    def compute_attack(self):
        modifier = 0
        for effect in self.effects:
            if attack in effect:
                modifier += effect["attack"]
        return self.strenght + modifier
    def attack(self, target):
        self._attack(target, self.compute_attack())
    def _attack(self, target, damage):
        state.output("%s attacks %s" % (str(self), str(state.game_frame.get_creature(target))))
        state.game_frame.get_creature(target).hurt(damage, self.uuid)
    def react_to_attack(self, damage, source):
        pass
    def on_death(self):
        if "death" in self.triggers:
            self.exec_trigger(self.triggers["death"])
    def die(self):
        self._dead = True
        self.on_death()
        state.game_frame.remove_creature(self.uuid)
        state.output("%s dies" % str(self))
    def _post_init(self):
        pass
    def move(self, dir):
        state.game_frame.window.map[self.pos].remove_creature(self.uuid)
        self.pos = state.add_tuples(self.pos, dir)
        state.game_frame.window.map[self.pos].add_creature(self.uuid)
    def compute_armor(self, damage):
        return 100/(100+self.armor)*damage
    def compute_resistance(self, damage):
        return max(damage-self.resistance, 0)
    def compute_realdamage(self, damage):
        return int(round(self.compute_resistance(self.compute_armor(damage)),0))
    def hurt(self, damage, source):
        self.react_to_attack(damage, source)
        self.take_damage(self.compute_realdamage(damage))
    def take_damage(self, damage):
        state.output("%s hurt for %s" % (str(self), damage))
        self.life -= damage
        if self.life <= 0:
            self.die()
    def take_turn(self):
        # do something
        return []
        #return [(self.speed, self.take_turn)]
    def save(self):
        res = {}
        for key in self.CREATURE_ATTRIBUTES:
            dattr_s = getattr(self, "DEFAULT_"+key.upper())
            attr = getattr(self, key)
            if attr != dattr_s() or key == "creature_id":
                res[key] = dattr_s.save(attr)
        return res
    def draw(self):
        return self.char
    @staticmethod
    def savec(creature):
        return creature.save()
    def __str__(self):
        return self.str

class Hero(Creature):
    DEFAULT_CHAR = SaveInterface(str, str, "@")
    DEFAULT_LIFE = SaveInterface(int, int, 50)
    DEFAULT_MAX_LIFE = SaveInterface(int, int, 50)
    DEFAULT_STR = SaveInterface(str, str, "hero")
    DEFAULT_MANA = SaveInterface(int, int, 20)
    DEFAULT_MAX_MANA = SaveInterface(int, int, 20)
    DEFAULT_CREATURE_ID = SaveInterface(int, int, 0)
    DEFAULT_IS_HERO = SaveInterface(bool, bool, True)
    def take_turn(self):
        results = state.game_frame.player_action()
        return [(self.speed, self.take_turn)] + results

class AutoCreature(Creature):
    DEFAULT_ENNEMY = SaveInterface(int, int, -1)
    DEFAULT_PATH = SaveInterface(tuple, list, tuple())
    def __init__(self, *args, **kwargs):
        self.CREATURE_ATTRIBUTES = self.CREATURE_ATTRIBUTES.union({"ennemy", "path"})
        Creature.__init__(self, *args, **kwargs)
        self.target_pos = None
        self.path_step = -1
    def react_to_attack(self, damage, source):
        self.ennemy = source
    def compute_path(self):
        self.target_pos = state.game_frame.get_creature(self.ennemy).pos
        self.path = shortest_path(self.pos, self.target_pos)
        self.path_step = 0
    def take_turn(self):
        if self.is_dead():
            return []
        if self.ennemy!=-1 and (not state.game_frame.exists(self.ennemy) or state.game_frame.get_creature(self.ennemy).is_dead()):
            self.ennemy = -1
        if self.ennemy!=-1 and state.distance(state.game_frame.get_creature(self.ennemy).pos, self.pos) < 3:
            self.attack(self.ennemy)
            return [(self.speed, self.take_turn)]
        elif self.ennemy!=-1:
            if state.game_frame.get_creature(self.ennemy).pos != self.target_pos:
                self.compute_path()
            if state.game_frame.is_walkable(self.path[self.path_step]):
                self.move(state.sub_tuples(self.path[self.path_step], self.pos))
                self.path_step += 1
            return [(self.speed, self.take_turn)]
            
        moves = [state.UP, state.RIGHT, state.LEFT, state.DOWN]
        random.shuffle(moves)
        for dir in moves:
            if state.game_frame.is_walkable(state.add_tuples(self.pos, dir)):
                self.move(dir)
                break
        return [(self.speed, self.take_turn)]

class CreatureHolder:
    def __init__(self, ai, args):
        self.ai = ai
        self.args = args
        for attr in ai.CREATURE_ATTRIBUTES:
            rattr = "DEFAULT_" + attr.upper()
            setattr(self, rattr, getattr(ai, rattr))
        for attr, value in args.items():
            rattr = "DEFAULT_" + attr.upper()
            save_int = getattr(self, rattr).copy()
            save_int.value = value
            setattr(self, rattr, save_int)
        self.triggers = {}
    def add_trigger(self, trigger, effect):
        self.triggers[trigger] = effect
    def __call__(self, *args, **kwargs):
        kargs = self.args.copy()
        kargs.update(kwargs)
        ai = self.ai(*args, **kargs)
        for trigger in self.triggers.items():
            ai.add_trigger(*trigger)
        return ai
    
"""
class Soul(AutoCreature):
    DEFAULT_CHAR = SaveInterface(str, str, "s")
    DEFAULT_STR = SaveInterface(str, str, "soul")
    DEFAULT_ATK = SaveInterface(int, int, 5)
    DEFAULT_LIFE = SaveInterface(int, int, 3)
    DEFAULT_MAX_LIFE = SaveInterface(int, int, 3)
    DEFAULT_RESISTANCE = SaveInterface(int, int, 0)
    DEFAULT_ARMOR = SaveInterface(int, int, 10)
    DEFAULT_CREATURE_ID = SaveInterface(int, int, 2)

class Daemon(AutoCreature):
    DEFAULT_CHAR = SaveInterface(str, str, "&")
    DEFAULT_STR = SaveInterface(str, str, "daemon")
    DEFAULT_ATK = SaveInterface(int, int, 7)
    DEFAULT_CREATURE_ID = SaveInterface(int, int, 1)
    def on_death(self):
        state.output("dead")
        soul = Soul(pos=self.pos)
        if self.ennemy!=-1:
            soul.react_to_attack(0, self.ennemy)
        state.game_frame.create_creature(soul)
"""

class Item(Creature):
    DEFAULT_IS_WALKABLE = SaveInterface(bool, bool, True)
    DEFAULT_ITEM = SaveInterface(str, str, "sword")
    DEFAULT_ATTRIBUTES = SaveInterface(list, list, [])
    DEFAULT_IS_PICKABLE = SaveInterface(bool, bool, True)
    DEFAULT_STR = SaveInterface(str, str, "item")
    DEFAULT_ALIVE = SaveInterface(bool, bool, False)
    DEFAULT_NAME = SaveInterface(str, str, "sword")
    DEFAULT_ICON = SaveInterface(str, str, ")")
    def __init__(self, **attributes):
        self.ritem = state.items.get_item(attributes.get("item", "sword"))
        attributes.update(self.ritem.entity)
        self.CREATURE_ATTRIBUTES = self.CREATURE_ATTRIBUTES.union({"attributes", "item", "name", "icon"})
        Creature.__init__(self, **attributes)
    def take_turn(self):
        return []

ais = {
    "neutral-standard": AutoCreature,
    "item": Item,
    "idle": Creature
}

def crt2dict(crt):
    crt = crt.replace("\n", "")
    while "  " in crt:
        crt.replace("  ", " ")
    result = {}
    for entry in crt.split(";;"):
        if not entry.replace(" ","").replace("\t", ""): continue
        key, value = entry.split(" ", 1)
        value = eval(value)
        result[key] = value
    return result

def load_creatures():
    global creature, creature_map, alive_creatures

    alive_creatures = {0}

    creature_map = {
        0: Hero,
        3: Item
    }

    creatures = {}

    pwd, _, files = next(os.walk(os.path.join(state.BASEDIR, "creatures/")))
    for file in files:
        if not file.endswith(".crt"):
            continue
        with open(os.path.join(pwd, file)) as f:
            c = f.read()
        crt_name = file[:-4]
        crt = crt2dict(c)
        ai = ais[crt["ai"]]
        args = {key: value for key, value in crt.items() if key in ai.CREATURE_ATTRIBUTES}

        creatures[crt_name] = CreatureHolder(ai,args)
        creature_map[crt["creature_id"]] = creatures[crt_name]
        if args.get("alive", True):
            alive_creatures.add(crt["creature_id"])
        for arg in crt.keys():
            if arg.startswith("on_"):
                creatures[crt_name].add_trigger(arg[3:], crt[arg])
load_creatures()
