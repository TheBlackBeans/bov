import os, state
icons = {}
def load_icons():
    global icons
    icons = {}
    pwd, _, files = next(os.walk(state.realpath('icons')))
    for file in files:
        if not file.endswith(".ico"):
            continue
        name = file[:-4]
        with open(os.path.join(pwd, file)) as f:
            icons[name] = f.read()

def get_icon(icon):
    return icons.get(icon, "�")
