import json, creature, state

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
            color = "\\C10"
        elif self.lit == 2:
            color = "\\C8"
        elif self.lit == 1:
            color = "\\C9"
        else:
            return "\\C1 "
        if self.creatures:
            char = state.game_frame.get_creature(self.creatures[-1]).draw()
        elif self.items:
            char = self.items[-1].draw()
        else:
            char = self.char
        return color + char
    def add_creature(self, creature):
        self.creatures.append(creature)
    def remove_creature(self, creature):
        self.creatures.remove(creature)
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

class Map:
    def __init__(self):
        self.map = {}
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
    def load(self):
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
        
    def load_file(self, file):
        self.file = file
        self.load()
