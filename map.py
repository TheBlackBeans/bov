import json, creature, state, random, math

class Tile:
    def __init__(self, char, wall):
        self.char = char
        self.wall = wall
        # lit
        #  0 - not lit (invisible)
        #  1 - known, but not lit (grey, doesn't show monsters)
        #  2 - completly lit (black, shows everything)
        self.lit = 2
        self.creatures = []
        self.items = []
        self.highlight = False
        self.known = False
    def draw(self):
        if self.highlight:
            color = "\\C10;"
        elif self.lit == 2:
            color = "\\C8;"
        elif self.lit == 1:
            color = "\\C9;"
        else:
            return "\\C1; "
        if self.creatures and self.lit == 2:
            char = state.game_frame.get_creature(self.creatures[-1]).draw()
        elif self.items and self.lit == 2:
            char = self.items[-1].draw()
        else:
            char = self.char
        return color + char
    def add_creature(self, creature):
        self.creatures.append(creature)
    def remove_creature(self, creature):
        try:
            self.creatures.remove(creature)
        except ValueError:
            state.warning("Trying to remove %s, whereas there are no such entity in that tile." % creature)
    def __bool__(self):
        return True

class NoTile:
    def __init__(self):
        self.wall = True
        self.creatures = []
        self.items = []
        self.known = False
        self.highlight = False
    def draw(self):
        return " "
    def __bool__(self):
        return False

class LCRNG:
    # Linear Congruential Random Numbers Generator
    M = 2147483647
    A = 69621
    B = 0
    MAX_RANGE = M-1
    def __init__(self, seed=None, step=0):
        if seed == None:
            self.seed = random.randint(0, self.M-1)
        else:
            self.seed = seed
        self.step = 0
        self.current = seed
        while step>0:
            next(self)
            step -= 1
    def get_seed(self):
        return {"seed": self.seed, "step": self.step}
    def __next__(self):
        self.current = (self.A*self.current+self.B)%self.M
        self.step += 1
        return current
    
class CMUWCRNG:
    # Complementay Multiply-With-Carry Random Numbers Generator
    R = 4096
    B = 2**32
    A = 18782
    MAX_RANGE = B-1
    def __init__(self, seeds=None, carry=None, step=0, seed_gen=None):
        if seeds == None:
            self.seeds = [random.randint(0,self.B-1) for i in range(self.R)]
        else:
            self.seeds = seeds
        self.initial_seed = self.seeds.copy()
        if carry == None:
            self.carry = random.randint(0,self.A-1)
        else:
            self.carry = carry
        self.initial_carry = self.carry
        self.step = 0
        while step>0:
            next(self)
            step-=1
    def get_seed(self):
        return {"seeds": self.initial_seeds, "carry": self.initial_carry, "step":self.step}
    def __next__(self):
        x = self.seeds.pop(0)
        value = self.A*x+self.carry
        self.seeds.append(value%self.B)
        self.carry = value//self.B
        self.step += 1
        return self.seeds[-1]

class RNG:
    # Random Number Generator
    def __init__(self, gen=CMUWCRNG, seed_gen=LCRNG, attrs={}, seed_seed=None):
        self.seed_seed = seed_seed
        self.gen = gen(**attrs, seed_gen=seed_gen(seed=seed_seed))
    def randint(self, a, b):
        if b < a:
            raise ValueError("max < min")
        lenght = b-a
        num_bins = lenght+1
        num_rand = self.gen.MAX_RANGE+1
        bin_size = num_rand/num_bins
        defect = num_rand%num_bins
        while True:
            x = next(self.gen)
            if num_rand - defect > x:
                break
        return int(a+x//bin_size)
    def randfloat(self, a, b):
        if b < a:
            raise ValueError("max < min")
        return a + self.random()*(b-a)
    def choose(self, l):
        return l[self.randint(0,len(l)-1)]
    def random(self):
        return next(self.gen)/self.gen.MAX_RANGE
    @property
    def seed(self):
        return self.gen.get_seed()

class BSPRoom:
    def __init__(self, x, y, maxwidth, maxheight, minwidth, minheight, rng):
        self.width = minwidth if minwidth == maxwidth else rng.randint(minwidth, maxwidth-1)
        self.height = minheight if minheight == maxheight else rng.randint(minheight, maxheight-1)
        self.w_offset = maxwidth-self.width
        self.h_offset = maxheight-self.height
        self.x = x+self.w_offset
        self.y = y+self.h_offset
        self.door = (1,0)
        self.rng = rng
    def set_door(self, v, l):
        if v == 1:
            if l == 0:
                self.door = (self.height, self.rng.randint(1, self.width-1))
            else:
                self.door = (0, self.rng.randint(1, self.width-1))
        else:
            if l == 0:
                self.door = (self.rng.randint(1, self.height-1), self.width)
            else:
                self.door = (self.rng.randint(1, self.height-1), 0)
    def offset(self, v, n):
        if v == 1:
            self.y += n
        else:
            self.x += n
    def __str__(self):
        return "BSPRoom<%s,%s,%s,%s>" % (self.x, self.y, self.width, self.height)

class BSPDungeon:
    def __init__(self, width, height, minwidth, minheight, recursion, rng, dispatch):
        self.width = width
        self.height = height
        self.minwidth = minwidth
        self.minheight = minheight
        self.recursion = recursion
        self.left = None
        self.right = None
        self.rng = rng
        self.dispatch = dispatch
    def generate(self):
        self.split()
        self.do_rooms()
        self.rooms = self.return_rooms()
        corridors = self.return_corridors()
        return rooms
    def draw_line(self, pos1, pos2):
        y1, x1 = pos1
        y2, x2 = pos2
        line = []
        if x1 <= x2:
            for i in range(x2-x1):
                line.append((0,1))
        else:
            for i in range(x1-x2):
                line.append((0,-1))
        if y1 <= y2:
            for i in range(y2-y1):
                line.append((1,0))
        else:
            for i in range(y1-y2):
                line.append((-1,0))
        
    def return_corridors(self):
        pass
    def do_corridors(self):
        if self.recursion == 1:
            left = self.left.return_rooms()[0]
            righ = self.right.return_rooms()[0]
            
    def return_rooms(self):
        if self.recursion == 0:
            return [self.room]
        leftrooms = self.left.return_rooms()    
        rightrooms = self.right.return_rooms()
        for room in rightrooms:
            room.offset(self.v, self.cut)
        return leftrooms+rightrooms
    def do_rooms(self):
        if self.recursion > 0:
            if self.left:
                self.left.do_rooms()
            if self.right:
                self.right.do_rooms()
        else:
            self.room = BSPRoom(0,0,self.width, self.height, self.minwidth, self.minheight, self.rng)
        if self.recursion == 1:
            if self.left:
                self.left.room.set_door(self.v, 0)
            if self.right:
                self.right.room.set_door(self.v, 1)

    def split(self):
        if self.recursion == 0:
            return
        self.v = self.rng.randint(0,1)
        if self.v == 1:
            # vertical
            self.cut = int(self.height*self.rng.randfloat(.5-self.dispatch/2,.5+self.dispatch/2))
            if self.cut-1 < self.minheight or self.height-self.cut < self.minheight:
                self.recursion = 0
                return
            
            self.left = BSPDungeon(self.width, self.cut-1, self.minwidth, self.minheight, self.recursion-1, self.rng, self.dispatch)
            self.right = BSPDungeon(self.width, self.height-self.cut, self.minwidth, self.minheight, self.recursion-1, self.rng, self.dispatch)
        else:
            # horizontal
            self.cut = int(self.width*self.rng.randfloat(.5-self.dispatch/2,.5+self.dispatch/2))
            if self.cut-1 < self.minwidth or self.width-self.cut < self.minwidth:
                self.recursion = 0
                return
            
            self.left = BSPDungeon(self.cut-1, self.height, self.minwidth, self.minheight, self.recursion-1, self.rng, self.dispatch)
            self.right = BSPDungeon(self.width-self.cut, self.height, self.minwidth, self.minheight, self.recursion-1, self.rng, self.dispatch)
        self.left.split()
        self.right.split()

class MapGenerator:
    pass



class BSP(MapGenerator):
    def __init__(self, width, height, recursion=None, minwidth=3, minheight=3, dispatch=.1, rng=None):
        if recursion == None:
            self.recursion = max(1, int(math.log(min(width, height), 2))-3)
        else:
            self.recursion = recursion
        if rng == None:
            self.rng = RNG()
        else:
            self.rng = rng
        self.width = width
        self.height = height
        self.dispatch = dispatch
        self.dungeon = BSPDungeon(width, height, minwidth, minheight, self.recursion, self.rng, dispatch)
    def generate(self):
        map = {}
        for room in self.dungeon.generate():
            y, x = room.y, room.x
            for i in range(room.width+1):
                for j in range(room.height+1):
                    map[y+j,x+i] = Tile(".", False)
            for i in range(room.width+1):
                map[y,x+i] = Tile("#", True)
                map[y+room.height,x+i] = Tile("#", True)
            for i in range(room.height+1):
                map[y+i,x] = Tile("#", True)
                map[y+i,x+room.width] = Tile("#", True)
            map[y+room.door[0], x+room.door[1]] = Tile("+", False)
        return map

class BlockAgregation(MapGenerator):
    DEFAULT_BLOCKS = [
        """##.##
#...#
.....
#...#
        ##.##""",
        """.....""",
        """.
.
.
.
        .""",
        """."""
    ]
    DEFAULT_MIN_AREA_FACTOR = .4
    def __init__(self, width, height, min_area=None, blocks=None, rng=None):
        if blocks == None:
            self.blocks = DEFAULT_BLOCKS
        else:
            self.blocks = blocks
        if min_area == None:
            self.min_area = int(width*height*self.DEFAULT_MIN_AREA_FACTOR)
        else:
            self.min_area = min_area
        if rng == None:
            self.rng = RNG()
        else:
            self.rng = rng
        self.width = widht
        self.height = height
    def print_block(self, pos, block):
        for j, line in enumerate(block):
            for i, c in enumerate(line):
                self.map[j][i] = c
    def do_block(self, pos, block):
        self.print_block(pos, block)
    def generate(self):
        self.map = [["#" for i in range(self.width)] for j in range(self.height)]


class CustomRoom:
    def __init__(self, x, y, width, height):
        self.chars = [[Tile("#", True) for i in range(width)] for i in range(height)]
        for j in range(1, height-1):
            for i in range(1, width-1):
                self.chars[j][i] = Tile(".", False)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.x2 = x+width
        self.y2 = y+height
        self.right = None
        self.left = None
        self.up = None
        self.down = None
        self.doors = [None, None, None, None]
    def __contains__(self, right):
        return not ((self.x > right.x2 or right.x > self.x2) or (self.y > right.y2 or right.y > self.y2))
    def draw_inside(self):
        for j, line in enumerate(self.chars):
            for i, c in enumerate(line):
                if i == 0 or i == self.width-1 or j == 0 or j == self.height-1:
                    continue
                yield (self.y+j, self.x+i), c
    def draw(self):
        for j, line in enumerate(self.chars):
            for i, c in enumerate(line):
                yield (self.y+j,self.x+i), c
    def create_door(self):
        is_open_default = False
        for i, door in enumerate(self.doors):
            if door == None: continue
            if i == 2:
                self.chars[0][door] = Tile("+", is_open_default)
            elif i == 3:
                self.chars[door][self.width-1] = Tile("+", is_open_default)
            elif i == 0:
                self.chars[self.height-1][door] = Tile("+", is_open_default)
            elif i == 1:
                self.chars[door][0] = Tile("+", is_open_default)
    def __str__(self):
        return "CustomRoom<%s,%s,%s,%s>" % (self.y, self.x, self.height, self.width)
    def __repr__(self):
        return str(self)
            
class CustomGenerator(MapGenerator):
    def __init__(self, nb_rooms, room_width_min=13, room_width_max=17, room_height_min=10, room_height_max=15, dist_min=2, dist_max=5, rng=None):
        if rng == None:
            self.rng = RNG()
        else:
            self.rng = rng
        self.dist_min = dist_min
        self.dist_max = dist_max
        self.room_width_min = room_width_min
        self.room_width_max = room_width_max
        self.room_height_min = room_height_min
        self.room_height_max = room_height_max
        self.nb_rooms = nb_rooms
        self.rooms = [CustomRoom(0, 0, self.rng.randint(room_width_min, room_width_max), self.rng.randint(room_height_min, room_height_max))]
        self.left = [0]
        self.bridges = {}
    def generate(self):
        self.expand_rooms()
        map =  self.generate_map()
        map = self.generate_bridges(map)
        map = self.handle_overlaps(map)
        return map
    def handle_overlaps(self, map):
        for room1 in self.rooms:
            for room2 in self.rooms:
                if room1 in room2:
                    for pos, tile in room1.draw_inside():
                        map[pos] = tile
                    for pos, tile in room2.draw_inside():
                        map[pos] = tile
        return map
    def generate_map(self):
        map = {}
        for room in self.rooms:
            room.create_door()
            for pos, tile in room.draw():
                map[pos] = tile
        return map
    def generate_bridges(self, map):
        for (room, dir), distance in self.bridges.items():
            room = self.rooms[room]
            odir = (dir+2)%4
            y = room.y
            x = room.x
            if dir == 0:
                y += 1
                x += room.doors[odir]
                for i in range(distance):
                    map[y-(i+2),x+1] = Tile("#", True)
                    map[y-(i+2),x] = Tile(".", False)
                    map[y-(i+2),x-1] = Tile("#", True)
            elif dir == 1:
                y += room.doors[odir]
                x += room.width
                for i in range(distance):
                    map[y+1,x+i] = Tile("#", True)
                    map[y,x+i] = Tile(".", False)
                    map[y-1,x+i] = Tile("#", True)
            elif dir == 2:
                y += room.height
                x += room.doors[odir]
                for i in range(distance):
                    map[y+i,x-1] = Tile("#", True)
                    map[y+i,x] = Tile(".", False)
                    map[y+i,x+1] = Tile("#", True)
            elif dir == 3:
                y += room.doors[odir]
                x += 1
                for i in range(distance):
                    map[y-1,x-(i+2)] = Tile("#", True)
                    map[y,x-(i+2)] = Tile(".", False)
                    map[y+1,x-(i+2)] = Tile("#", True)
        return map
    def door_pos(self, size1, size2):
        size1 -= 2
        size2 -= 2
        return min((size1+size2)//4, min(size1,size2))
    def expand_rooms(self):
        while len(self.rooms) < self.nb_rooms:
            current_id = self.rng.choose(self.left)
            current = self.rooms[current_id]
            options = []
            if current.up == None:
                options.append(0)
            if current.right == None:
                options.append(1)
            if current.down == None:
                options.append(2)
            if current.left == None:
                options.append(3)
            dir = self.rng.choose(options)
            options.remove(dir)
            distance = self.rng.randint(self.dist_min, self.dist_max)
            height = self.rng.randint(self.room_height_min, self.room_height_max)
            width = self.rng.randint(self.room_width_min, self.room_width_max)
            if dir == 0:
                # create up
                new = CustomRoom(current.x, current.y-(distance+height), width, height)
                new.down = current
                current.up = new
                sizes = [current.width, new.width]
            elif dir == 2:
                # create down
                new = CustomRoom(current.x, current.y2+(distance), width, height)
                new.up = current
                current.down = new
                sizes = [current.width, new.width]
            elif dir == 1:
                # create right
                new = CustomRoom(current.x2+(distance), current.y, width, height)
                new.left = current
                current.right = new
                sizes = [current.height, new.height]
            elif dir == 3:
                # create left
                new = CustomRoom(current.x-(distance+width), current.y, width, height)
                new.right = current
                current.left = new
                sizes = [current.height, new.height]
            odir = (dir+2)%4
            new.doors[dir] = self.door_pos(*sizes)
            current.doors[odir] = self.door_pos(*sizes)
            self.left.append(len(self.rooms))
            if not options:
                self.left.remove(current_id)
            self.bridges[current_id, dir] = distance
            self.rooms.append(new)

GENERATE_OPS = [
    {
        "gen": CustomGenerator,
        "args": [10],
        "kwargs": {},
        "name": "Default small-and-boring dungeon"
    },
    {
        "gen": CustomGenerator,
        "args": [15],
        "kwargs": {},
        "name": "Default medium dungeon"
    },
    {
        "gen": CustomGenerator,
        "args": [15],
        "kwargs": {"room_width_min": 5, "room_width_max": 25, "room_height_min": 4, "room_height_max": 23, "dist_max": 10},
        "name": "Experimental"
    }
]
            
class Map:
    def __init__(self):
        self.map = {}
        self.is_custom = False
        self.file = ""
        self.has_map = False
    def __getitem__(self, pos):
        if pos in self.map:
            return self.map[pos]
        else:
            return NoTile()
    def unhighlight(self):
        for tile in self.map.values():
            tile.highlight = False
    def unlit(self):
        for tile in self.map.values():
            tile.lit = 0
    def lit_known(self):
        for tile in self.map.values():
            if tile.lit == 0 and tile.known:
                tile.lit = 1
    def lit(self):
        for tile in self.map.values():
            tile.lit = 2
    def reset(self):
        for tile in self.map.values():
            tile.creatures.clear()
            tile.items.clear()
    def load_custom(self):
        #gen = BSP(60, 40, 3, dispatch=.5)
        self.custom = True
        self.has_map = True
        ops = GENERATE_OPS[2]
        gen = ops["gen"](*ops["args"], **ops["kwargs"])
        self.map = gen.generate()
        state.game_frame.pre_load()
        state.game_frame.load_creatures([creature.Hero(pos=(1,1),creature_id=0)])
        state.game_frame.load_items([])
    def load(self):
        self.map = {}
        with open(self.file) as f:
            objs, *self.map_lines = f.read().split("\n")
            for y, line in enumerate(self.map_lines):
                for x, char in enumerate(line):
                    if char == ".":
                        self.map[y,x] = Tile(".", False)
                    elif char == "#":
                        self.map[y,x] = Tile("#", True)
            objs = json.loads(objs)
        state.game_frame.pre_load()
        state.game_frame.load_creatures([creature.creature_map[c["creature_id"]](**c) for c in objs["creatures"]])
        state.game_frame.load_items([items.item_map[item["item_id"]](**item) for item in objs["items"]])
    def save(self):
        if not self.has_map or self.is_custom:
            return 0
        objs = {
            "creatures": [
                c.save() for c in state.game_frame.creatures.values()
            ],
            "items": [
                item.save() for item in state.game_frame.items.values()
            ]
        }
        with open(self.file, "w") as f:
            f.write(json.dumps(objs) + "\n")
            f.write("\n".join(self.map_lines))
        return 1
    def load_file(self, file):
        self.has_map = True
        self.custom = False
        self.file = file
        self.load()
