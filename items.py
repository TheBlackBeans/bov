import state

WEAPON_CHAR = ")"
ITEMS_CHAR = "*"

NOTHING_ID = 0
SWORD_ID = 1
SHIELD_ID = 2
POTION_ID = 3

class InventoryWindow(state.Window):
    def draw(self):
        self.border()
        self.draw_items()
    def draw_items(self):
        inventory = state.game_frame.get_hero().inventory
        for i, item in enumerate(inventory.inventory):
            self.addstr(1+i,1,str(item))

class Effect:
    def __init__(self, name, modifiers):
        self.name = name
        self.modifiers = modifiers
    def __getattr__(self, key):
        return self.modifiers[key]
    def __contains__(self, key):
        return key in self.modifiers
    def __setattr__(self, key, value):
        self.modifiers[key] = value

class Inventory:
    def __init__(self, slots=None, inventory=None):
        if slots == None:
            self.slots = {
                "right": NoneItem(),
                "left": NoneItem(),
                "helmet": NoneItem(),
                "armor": NoneItem(),
                "shoes": NoneItem()
            }
        else:
            self.slots = slots
        if inventory == None:
            self.inventory = []
        else:
            self.inventory = inventory
    def __eq__(self, right):
        return self.slots == right.slots and self.inventory == right.inventory
    def add_item(self, item):
        self.inventory.append(item)
    @classmethod
    def load(cls, value):
        slots = value["slots"]
        if slots:
            slots = {key: Item(*value) if value[3] != NOTHING_ID else NoneItem() for key, value in slots.items()}
        inventory = value["inventory"]
        if inventory:
            inventory = [Item(*value) for value in inventory]
        return cls(slots=slots, inventory=inventory)
    @staticmethod
    def save(inventory):
        return {
            "slots": {key: value.save() for key, value in inventory.slots.items()},
            "inventory": [item.save() for item in inventory.inventory]
        }
    def inventory_effects(self):
        pass

        

class Item:
    def __init__(self, weight, char, name, id, properties=None):
        self.weight = weight
        self.char = char
        self.name = name
        self.id = id
        if properties == None:
            self.properties={}
        else:
            self.properties = properties
    def repr(self):
        return self.name
    def __str__(self):
        return self.char
    def __eq__(self, right):
        return self.id == right.id and self.properties == right.properties
    def save(self):
        return [self.weight, self.char, self.name, self.id, self.properties]

class Sword(Item):
    def __init__(self, weight, name, properties=None):
        Item.__init__(self, weight, WEAPON_CHAR, name, SWORD_ID, properties=properties)
    
class Potion(Item):
    def __init__(self, name, properties=None):
        Item.__init__(self, 1, ITEM_CHAR, name, POTION_ID, properties=properties)
        
    
class NoneItem(Item):
    def __init__(self):
        self.weight = 0
        self.char = " "
        self.id = NOTHING_ID
        self.name = "Nothing"
        self.properties = {}
    def __bool__(self):
        return False
