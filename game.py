import state, curses, random, heapq, functools, creature, queue
from math import pi, atan
class ActionsQueue:
    def __init__(self, queue=None):
        if queue is None:
            self.queue = []
        else:
            self.queue = queue.copy()
            heapq.heapify(self.queue)
    def add_action(self, time, action, parent):
        heapq.heappush(self.queue, TimeAndAction(time, action, parent))
    def pop_action(self):
        time, action, parent = heapq.heappop(self.queue)
        for i in range(len(self.queue)):
            self.queue[i].decrease_time(time)
        return action, parent
    
@functools.total_ordering
class TimeAndAction:
    def __init__(self, time, action, parent):
        self.time = time
        self.action = action
        self.parent_entity = parent
    def __eq__(self, right):
        return self.time == right.time
    def __gt__(self, right):
        return self.time > right.time
    def __getitem__(self, index):
        if index in {0, "time"}: return self.time
        elif index in {1, "action"}: return self.action
        elif index in {2, "parent"}: return self.parent_entity
        else:
            raise IndexError("Index out of range")
    def decrease_time(self, time):
        self.time -= time

class UUIDGen:
    def __init__(self, taken=set()):
        self.taken = taken
        self.current = 0
    def __next__(self):
        while self.current in self.taken:
            self.current += 1
        self.taken.add(self.current)
        return self.current

class FOVWalkGen:
    def __init__(self, start):
        self.start = start
        self.visited = {start}
        self.border = queue.PriorityQueue()
        self.border.put_nowait((0,start))
    def neighboors(self, pos):
        for dir in {state.UP, state.RIGHT, state.DOWN, state.LEFT}:
            yield state.add_tuples(dir, pos)
    def __next__(self):
        distance, current = self.border.get_nowait()
        for next in self.neighboors(current):
            if next not in self.visited:
                self.visited.add(next)
                self.border.put_nowait((state.distance(next, self.start),next))
        return current

class Shadow:
    def __init__(self, left, right):
        self.left = left
        self.right = right
        self.ext = left > right
    def __contains__(self, right):
        return (self.left <= right.right <= self.right or self.left <= right.left <= self.right) or (self.right <= right.left <= self.left or self.right <= right.right <= self.left)
    def strictly_contains(self, right):
        return (self.left <= right.left <= right.right <= self.right and not (self.ext and right.ext)) or (self.right <= right.right <= right.left <= self.left and (self.ext and right.ext))
    def join(self, right):
        lfunc = max if self.ext else min
        rfunc = min if self.ext else max
        self.left = lfunc(self.left, right.left)
        self.right = rfunc(self.right, right.right)
        self.ext = self.left > self.right
    def is_full_circle(self):
        return self.left == 0 and self.right == 2*pi
    
class PosError(BaseException): pass
        
class GameFrame(state.Frame):
    def _post_init(self):
        self.window.map = state.map.Map()
        self.creatures = {}
        self.items = {}
        state.keyhandler.add_handler(state.PRIORITIES["Game"])(self.get_key)
        self.actions = ActionsQueue()
        self.played = True
        self.player_turns = 0
        self.turns = 0
        self.creature_uuid_gen = UUIDGen()
        self.item_uuid_gen = UUIDGen()
        self.init_actions_with_creatures()
        # move_mode
        #  0 - real time: action on button press
        #  1 - turn-by-turn: prompts an action on button press,
        #                    requires confirmation
        self.move_mode = 0
        self.hero_uuid = -1
    def get_creature(self, uuid):
        return self.creatures[uuid]
    def pre_load(self):
        self.window.map.reset()
        self.creatures = {}
        self.items = {}
    def load_creatures(self, creatures):
        self.creature_uuid_gen = UUIDGen({creature.uuid for creature in creatures})
        for creature in creatures:
            if creature.is_hero:
                self.hero_uuid = creature.uuid
            self.creatures[creature.uuid] = creature
            self.window.map[creature.pos].add_creature(creature.uuid)
            self.actions.add_action(creature.speed, creature.take_turn, creature.uuid)
    def remove_creatures_pos(self, pos):
        for uuid in self.window.map[pos].creatures:
            del self.creatures[uuid]
        self.window.map[pos].creatures.clear()
    def remove_creature(self, uuid):
        entity = self.get_creature(uuid)
        self.window.map[entity.pos].creatures.remove(entity.uuid)
        del self.creatures[uuid]
    def load_items(self, items):
        self.items_uuid_gen = UUIDGen({item.uuid for item in items})
        for item in items:
            self.items[item.uuid] = item
    def create_creature(self, creature):
        tile = self.window.map[creature.pos]
        if not tile:
            raise PosError("Creature created outside the map (%s)" % (creature.pos,))
        creature.uuid = next(self.creature_uuid_gen)
        tile.add_creature(creature.uuid)
        self.creatures[creature.uuid] = creature
        self.actions.add_action(creature.speed, creature.take_turn, creature.uuid)
    def init_actions_with_creatures(self):
        for creature in self.creatures.values():
            self.actions.add_action(creature.speed, creature.take_turn, creature.uuid)
    def take_turn(self):
        self.turns += 1
        action, parent = self.actions.pop_action()
        if parent not in self.creatures:
            return
        actions = action()
        for time, act in actions:
            self.actions.add_action(time, act, parent)
    def is_walkable(self, pos):
        return not self.window.map[pos].wall and all(self.get_creature(uuid).is_walkable for uuid in self.window.map[pos].creatures)
    def get_hero(self):
        return self.get_creature(self.hero_uuid)
    def player_action(self):
        self.player_turns += 1
        self.played = False
        self.player_actions = []
        state.screen.refresh()
        while not self.played:
            key = state.screen.getch()
            state.keyhandler.dispatch_key(key)
            state.screen.refresh()
        return self.player_actions
    def process_move(self, move):
        move_map = {
            curses.KEY_UP: state.UP,
            curses.KEY_RIGHT: state.RIGHT,
            curses.KEY_DOWN: state.DOWN,
            curses.KEY_LEFT: state.LEFT
        }
        action_map = {
            curses.KEY_UP: state.action.up_action,
            curses.KEY_RIGHT: state.action.right_action,
            curses.KEY_DOWN: state.action.down_action,
            curses.KEY_LEFT: state.action.left_action
        }
        if self.move_mode == 0:
            self.move(
                0,
                move_map[move]
            )
        elif self.move_mode == 1:
            state.action_frame.load_action(
                action_map[move]
            )
    def get_key(self, key):
        hero = self.creatures[0]
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
        elif key in {curses.KEY_UP, curses.KEY_RIGHT, curses.KEY_DOWN, curses.KEY_LEFT}:
                self.process_move(key)
        elif key == ord("a"):
            state.action_frame.load_action(
                state.action.attack_action
            )
        elif key == ord("t"):
            state.action_frame.load_action(
                state.action.move_mode_action
            )
        elif key == ord("s"):
            state.action_frame.load_action(
                state.action.save_action
            )
        elif key == ord("c"):
            state.action_frame.load_action(
                state.action.create_action
            )
        elif key == ord("d"):
            state.action_frame.load_action(
                state.action.delete_action
            )
        elif key == ord("z"):
            state.action_frame.load_action(
                state.action.vertexes_action
            )
        elif key == ord("e"):
            state.action_frame.load_action(
                state.action.coords_action
            )
        elif key == ord("r"):
            state.action_frame.load_action(
                state.action.switch_action
            )
        elif key == ord(curses.ascii.ctrl("d")):
            state.action_frame.load_action(
                state.action.shadow_action
            )
        else:
            return False
        return True
    def load_map(self):
        self.window.map.load_file("maps/map1.mp")
    def move(self, what, dir):
        if self.is_walkable(state.add_tuples(self.creatures[what].pos, dir)):
            self.creatures[what].move(dir)
            if what == self.hero_uuid:
                self.played = True

class GameWindow(state.Window):
    def _post_init(self):
        self.offset = (1,2)
        self.hide = False
    def pos_to_realpos(self, pos):
        return state.sub_tuples(pos, self.offset)
    def add_highlight(self, pos):
        self.map[self.pos_to_realpos(pos)].highlight = True
    def draw(self):
        self.regulate_offset()
        self.border()
        if self.hide:
            self.update_seen()
        self.draw_map()
        self.map.unhighlight()
    def draw_highlights(self):
        for y, x in self.highlights:
            self.parent.chgat(self.y+y, self.x+x, 1, curses.color_pair(5)|curses.A_BOLD)
        self.highlights = set()
    def inclusive_mod_2pi(self, angle):
        while angle < 0:
            angle += 2*pi
        while angle > 2*pi:
            angle -= 2*pi
        return angle
    def compute_angle(self, pos):
        if pos[1] == 0:
            if pos[0] >= 0:
                return pi/2
            else:
                return 3*pi/2
        angle = atan(pos[0]/pos[1])
        if pos[1] < 0:
            angle += pi
        angle = self.inclusive_mod_2pi(angle)
        return angle
    def compute_vertex(self, start, pos):
        if start[1] == pos[1]:
            # start.x == pos.x
            if start[0] < pos[0]:
                return (pos, state.add_tuples(pos, (0,1)))
            else:
                return (state.add_tuples(pos, (1,0)), state.add_tuples(pos, (1,1)))
        if start[0] == pos[0]:
            # start.y == pos.y
            if start[1] < pos[1]:
                return (pos, state.add_tuples(pos, (1,0)))
            else:
                return (state.add_tuples(pos, (0,1)), state.add_tuples(pos, (1,1)))

        if (pos[0] > start[0] and pos[1] > start[1]) or (pos[0] < start[0] and pos[1] < start[1]):
            return (state.add_tuples(pos, (0,1)), state.add_tuples(pos, (1,0)))
        else:
            return (pos, state.add_tuples(pos, (1,1)))
    def compute_shadow(self, pos1, pos2):
        vertex1, vertex2 = self.compute_vertex(pos1, pos2)
        angle1 = self.compute_angle(state.sub_tuples(vertex1, pos1))
        angle2 = self.compute_angle(state.sub_tuples(vertex2, pos1))
        return Shadow(min(angle1,angle2),max(angle1,angle2))
    def compute_visibility(self, start, max_range=float("inf")):
        gen = FOVWalkGen(start)
        start_center = state.add_tuples(start, (.5,.5))
        shadows = []
        steps = 0
        while not (len(shadows) == 1 and shadows[0].is_full_circle()):
            steps += 1
            pos = next(gen)
            if state.distance(start, pos) > max_range:
                break
            if not self.map[pos]:
                continue
            
            shadow = self.compute_shadow(start, pos)
            if any(s.strictly_contains(shadow) for s in shadows):
                continue
            elif any(s in shadow for s in shadows):
                self.map[pos].known = True
                self.map[pos].lit = 1
            elif self.map[pos]:
                self.map[pos].known = True
                self.map[pos].lit = 2
            if self.map[pos] and not self.map[pos].wall:
                continue
                
            i = 0
            while i < len(shadows):
                if shadows[i] in shadow:
                    shadow.join(shadows.pop(i))
                else:
                    i += 1
            shadows.append(shadow)
    def update_seen(self):
        self.map.unlit()
        self.compute_visibility(state.game_frame.creatures[state.game_frame.hero_uuid].pos, max_range=50)
        self.map.lit_known()
    def draw_map(self):
        for y in range(1, self.height-1):
            for x in range(1, self.width-2):
                # real x and y
                ry, rx = state.sub_tuples((y, x), self.offset)
                if self.map[ry, rx]:
                    self.addch(y, x, self.map[ry, rx].draw())
    def in_rect(self, y, x):
        return 1 <= y < self.height-1 and 1 <= x < self.width-2
    def regulate_offset(self):
        while state.game_frame.creatures[state.game_frame.hero_uuid].pos[0] + self.offset[0] <= 2:
            self.offset = state.add_tuples(self.offset, (1, 0))
        while state.game_frame.creatures[state.game_frame.hero_uuid].pos[0] + self.offset[0] >= self.height-3:
            self.offset = state.add_tuples(self.offset, (-1, 0))
        while state.game_frame.creatures[state.game_frame.hero_uuid].pos[1] + self.offset[1] <= 2:
            self.offset = state.add_tuples(self.offset, (0, 1))
        while state.game_frame.creatures[state.game_frame.hero_uuid].pos[1] + self.offset[1] >= self.width-4:
            self.offset = state.add_tuples(self.offset, (0, -1))
