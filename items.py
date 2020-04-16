import state, os, configparser

WEAPON_CHAR = ")"
ITEMS_CHAR = "*"


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
        self.inventory.append(get_item(item.item))
    @classmethod
    def load(cls, value):
        slots = value["slots"]
        if slots:
            slots = {key: Item.load(value[0], **value[1]) if value[0] != None else NoneItem() for key, value in slots.items()}
        inventory = value["inventory"]
        if inventory:
            inventory = [Item.load(value[0], **value[1]) for value in inventory]
        return cls(slots=slots, inventory=inventory)
    @staticmethod
    def save(inventory):
        return {
            "slots": {key: value.save() for key, value in inventory.slots.items()},
            "inventory": [item.save() for item in inventory.inventory]
        }
    def inventory_effects(self):
        pass

items = {}
    
def load_items():
    global items
    items = {}
    pwd, _, files = next(os.walk(state.realpath('items')))
    for file in files:
        if not file.endswith(".it"):
            continue
        name = file[:-3]
        item = configparser.ConfigParser()
        item.read(os.path.join(pwd, file))
        items[name] = it2item(item, name)

def get_item(name):
    return items[name]

def it2item(item, name):
    default_values = {
        "entity": {
            "str": "item",
            "char": "item"
        },
        "item": {
            "slot": "",
            "slot-effect": "",
            "weight": "0",
            "id": "0",
            "name": "item",
            "icon": "item"
        }
    }
    
    for section in item.sections():
        if section not in default_values:
            state.warning("item %s is defining a custom section %s" % (name, section))
            default_values[section] = {}
        for key, value in item[section].items():
            if key not in default_values[section]:
                state.warning("item %s is defining a custom entry %s.%s=%s" % (name, section, key, value))
            default_values[section][key] = value
    return Item(name, **default_values)
       
class Item:
    @staticmethod
    def load(i, **properties):
        item = get_item(i)
        item.properties.update(properties)
        return item
    def __init__(self, i, **properties):
        self.item = i
        self.properties = properties
        self.entity["char"] = state.icon.get_icon(self.entity["char"])
    @property
    def weight(self):
        return int(self.properties['item']['weight'])
    @weight.setter
    def weight(self, value):
        self.properties['item']['weight'] = str(value)
    @property
    def char(self):
        return state.icon.get_icon(self.properties['item']['icon'])
    @char.setter
    def char(self, value):
        self.properties['item']['icon'] = value
    @property
    def name(self):
        return self.properties['item']['name']
    @name.setter
    def name(self, value):
        self.properties['item']['name'] = value
    @property
    def id(self):
        return int(self.properties['item']['id'])
    @id.setter
    def id(self, value):
        self.properties['item']['id'] = str(value)
    @property
    def entity(self):
        return self.properties['entity']
    @entity.setter
    def entity(self, value):
        self.properties['entity'] = value
                                            
    def repr(self):
        return self.name
    def __str__(self):
        return self.char
    def __eq__(self, right):
        return self.id == right.id
    def save(self):
        return (self.item, self.properties)

        
    
class NoneItem(Item):
    def __init__(self):
        self.properties = {
            'item': {
                'weight': '0',
                'char': " ",
                'id': '0',
                'name': 'Nothing'
            },
            'entity': {}
        }
        self.item = None
    def __bool__(self):
        return False
