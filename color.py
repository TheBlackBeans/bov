import curses

colors = {}

def init_curses_color():
    # Colors definition
    colors["BLACK"] = curses.COLOR_BLACK
    colors["BLUE"] = curses.COLOR_BLUE
    colors["CYAN"] = curses.COLOR_CYAN
    colors["GREEN"] = curses.COLOR_GREEN
    colors["MAGENTA"] = curses.COLOR_MAGENTA
    colors["RED"] = curses.COLOR_RED
    colors["WHITE"] = curses.COLOR_WHITE
    colors["YELLOW"] = curses.COLOR_YELLOW
    if curses.can_change_color():
        curses.init_color(
            colors["WHITE"],
            1000,
            1000,
            1000
        )
        curses.init_color(
            colors["BLACK"],
            0,
            0,
            0
        )
    if curses.COLORS >= 10 and curses.can_change_color():
        colors["GREY"] = 9
        curses.init_color(
            colors["GREY"],
            600,
            600,
            600
        )
        # ...
        colors["RED2"] = 10
        curses.init_color(
            colors["RED2"],
            680,
            0,
            0
        )
        colors["ORANGE"] = 11
        curses.init_color(
            colors["ORANGE"],
            680,
            300,
            300
        )
    else:
        colors["GREY"] = colors["BLACK"]
        colors["RED2"] = colors["RED"]
        colors["ORANGE"] = colors["RED"]

    
        
    # Pair definition
    # TEXT
    # 1 - Default text
    curses.init_pair(1, colors["BLACK"], colors["WHITE"])
    # 5 - Highlighted text
    curses.init_pair(5, colors["RED2"], colors["WHITE"])
    # 6 - Selected text
    curses.init_pair(6, colors["RED2"], colors["MAGENTA"])
    # BARS
    # 2 - Life filled
    curses.init_pair(2, colors["RED"], colors["RED"])
    # 7 - Mana filled
    curses.init_pair(7, colors["BLUE"], colors["BLUE"])
    # 3 - Empty
    curses.init_pair(3, colors["WHITE"], colors["WHITE"])
    # 4 - Hero
    curses.init_pair(4, colors["BLACK"], colors["WHITE"])
    # MAP
    # 8 - Lit tile
    curses.init_pair(8, colors["BLACK"], colors["WHITE"])
    # 9 - Lit but hidden tile
    curses.init_pair(9, colors["GREY"], colors["WHITE"])
    # 10 - Highlighted tile
    curses.init_pair(10, colors["RED2"], colors["WHITE"])
    # 11 - Warning text
    curses.init_pair(11, colors["ORANGE"], colors["WHITE"])
