#!/usr/bin/env python

############################################################################
# Copyright (c) 2009   unohu <unohu0@gmail.com> and Contributors           #
#                                                                          #
# Contributors: John Elkins <soulfx@yahoo.com>                             #
# Contributors: Bhathiya Perera (JaDogg)                                   #
#                                                                          #
# Permission to use, copy, modify, and/or distribute this software for any #
# purpose with or without fee is hereby granted, provided that the above   #
# copyright notice and this permission notice appear in all copies.        #
#                                                                          #
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES #
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF         #
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR  #
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES   #
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN    #
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF  #
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.           #
#                                                                          #
############################################################################

import configparser as conf
import logging
import os
import pickle
import sys
from functools import reduce
from subprocess import check_output, check_call, CalledProcessError

PROGRAM_NAME = "Simple Window Tiler"
PROGRAM_VERSION = "0.3"
PROGRAM_SOURCE = "https://github.com/JaDogg/stiler"
BANNER = """
━━━━━━━━━━━━━━━━━━━━━━━━
┏┓  ┏┳┓•┓        ┏┓ ┏┓
┗┓━━ ┃ ┓┃┏┓┏┓  ┓┏ ┫ ┃┫
┗┛   ┻ ┗┗┗ ┛   ┗┛┗┛•┗┛
  Simple Window Tiler
━━━━━━━━━━━━━━━━━━━━━━━━
""".strip()


# Reference: https://stackoverflow.com/a/70796089
class Color:
    """A class for terminal color codes."""

    BOLD = "\033[1m"
    BLUE = "\033[94m"
    WHITE = "\033[97m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    BOLD_WHITE = BOLD + WHITE
    BOLD_BLUE = BOLD + BLUE
    BOLD_GREEN = BOLD + GREEN
    BOLD_YELLOW = BOLD + YELLOW
    BOLD_RED = BOLD + RED
    END = "\033[0m"


class ColorLogFormatter(logging.Formatter):
    """A class for formatting colored logs."""

    FORMAT = "%(prefix)s%(msg)s%(suffix)s"

    LOG_LEVEL_COLOR = {
        "DEBUG": {'prefix': '🐛', 'suffix': ''},
        "INFO": {'prefix': '👉' + Color.CYAN, 'suffix': Color.END},
        "WARNING": {'prefix': '⚠️' + Color.BOLD_YELLOW, 'suffix': Color.END},
        "ERROR": {'prefix': '🛑' + Color.BOLD_RED, 'suffix': Color.END},
        "CRITICAL": {'prefix': '🛑🛑' + Color.BOLD_RED, 'suffix': Color.END},
    }

    def format(self, record):
        """Format log records with a default prefix and suffix to terminal color codes that corresponds to the log
        level name."""
        if not hasattr(record, 'prefix'):
            record.prefix = self.LOG_LEVEL_COLOR.get(record.levelname.upper()).get('prefix')

        if not hasattr(record, 'suffix'):
            record.suffix = self.LOG_LEVEL_COLOR.get(record.levelname.upper()).get('suffix')

        formatter = logging.Formatter(self.FORMAT)
        return formatter.format(record)


log = logging.getLogger(PROGRAM_NAME)
log.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(ColorLogFormatter())
log.addHandler(ch)


def get_output(cmd): return check_output(cmd, shell=True).decode('utf-8').strip()


def lfilter(f, lst): return list(filter(f, list(lst)))


def lmap(f, lst): return list(map(f, list(lst)))


def lreduce(f, lst): return reduce(f, list(lst))


def initconfig():
    rcfile = os.getenv('HOME') + "/.stilerrc"

    config_defaults = {
        'BottomPadding': '3',
        'TopPadding': '3',
        'LeftPadding': '3',
        'RightPadding': '3',
        'WinTitle': '21',
        'WinBorder': '2',
        'MwFactor': '0.5',
        'Monitors': '2',
        'GridWidths': '0.5',
        'WidthAdjustment': '0.0',
        'TempFile': '/tmp/tile_winlist',
        'WindowFilter': 'on',
    }

    config = conf.RawConfigParser(config_defaults)

    if not os.path.exists(rcfile):
        log.info("writing new config file to " + rcfile)
        with open(rcfile, 'w+') as cfg:
            config.write(cfg)

    config.read(rcfile)
    return config


def version_option():
    """
    Display program version information
    """
    print(f"{PROGRAM_NAME} {PROGRAM_VERSION}  <{PROGRAM_SOURCE}>")


def v_flag():
    """
    Enable DEBUG level verbosity
    """
    log.setLevel(logging.DEBUG)
    ch.setLevel(logging.DEBUG)


def has_required_programs(program_list):
    success = True
    for program in program_list:
        try:
            log.info("checking for " + program)
            check_call("which " + program, shell=True)
        except CalledProcessError as _:
            log.error(program + " is required by " + PROGRAM_NAME)
            success = False

    return success


def is_valid_window(window):
    if WindowFilter:
        window_type = get_output("xprop -id " + window + " _NET_WM_WINDOW_TYPE | cut -d_ -f10").split("\n")[0]
        window_state = get_output("xprop -id " + window +
                                  " WM_STATE | grep \"window state\" | cut -d: -f2").split("\n")[0].lstrip()
        log.debug("%s is type %s, state %s" % (window, window_type, window_state))
        if window_type == "UTILITY" or window_type == "DESKTOP" or window_state == "Iconic" or window_type == "DOCK":
            return False

    return True


def initialize():
    desk_output = get_output("wmctrl -d").split("\n")
    desk_list = [line.split()[0] for line in desk_output]

    current = lfilter(lambda x: x.split()[1] == "*", desk_output)[0].split()

    desktop = current[0]
    width = current[8].split("x")[0]
    height = current[8].split("x")[1]
    orig_x = current[7].split(",")[0]
    orig_y = current[7].split(",")[1]

    win_output = get_output("wmctrl -lG").split("\n")
    win_list = {}

    for desk in desk_list:
        win_list[desk] = lmap(lambda y: hex(int(y.split()[0], 16)), lfilter(lambda x: x.split()[1] == desk, win_output))

    return desktop, orig_x, orig_y, width, height, win_list


def get_active_window():
    active = get_output("xprop -root _NET_ACTIVE_WINDOW | cut -d' ' -f5 | cut -d',' -f1")
    if is_valid_window(active):
        log.debug("obtained active window: '" + str(active) + "'")
        return active
    else:
        return 0


def get_window_width_height(window_id):
    """
    return the given window's [width, height]
    """
    return get_output(" xwininfo -id " + window_id + " | egrep \"Height|Width\" | cut -d: -f2 | tr -d \" \"").split(
        "\n")


def get_window_x_y(windowid):
    """
    return the given window's [x,y] position
    """
    return get_output("xwininfo -id " + windowid + " | grep 'Corners' | cut -d' ' -f5 | cut -d'+' -f2,3").split("+")


def store(ob, file: str):
    with open(file, 'wb+') as f:
        pickle.dump(ob, f)


def retrieve(file: str):
    try:
        with open(file, 'rb+') as f:
            obj = pickle.load(f)
        return obj
    except (OSError, IOError, EOFError) as _:
        with open(file, 'wb+'):
            pass
        dc = {}
        return dc


def get_width_constant(width, width_constant_array):
    """
    Returns the current closest width constant from the given constant_array and given current width
    """
    return min(lmap(lambda y: [abs(y - width), y], width_constant_array))[1]


def get_next_width(current_width, width_array):
    """
    Returns the next width to use based on the given current width, and width constants
    """
    active_width = float(current_width) / MaxWidth

    active_width_constant = width_array.index(get_width_constant(active_width, width_array))

    width_multiplier = width_array[(active_width_constant + 1) % len(width_array)]

    return int((MaxWidth - (WinBorder * 2)) * width_multiplier)


def persist_layout(layout_function_name: str):
    """
    Persist the last used layout
    """
    store({"layout": layout_function_name}, TempFile + "_last_layout")
    log.info("Persisted last used layout: " + layout_function_name)


def get_simple_tile(wincount):
    persist_layout("get_simple_tile")
    rows = wincount - 1
    layout = []
    if rows == 0:
        layout.append((OrigX, OrigY, MaxWidth, MaxHeight - WinTitle - WinBorder))
        return layout
    else:
        layout.append((OrigX, OrigY, int(MaxWidth * MwFactor), MaxHeight - WinTitle - WinBorder))

    x = OrigX + int((MaxWidth * MwFactor) + (2 * WinBorder))
    width = int((MaxWidth * (1 - MwFactor)) - 2 * WinBorder)
    height = int(MaxHeight / rows - WinTitle - WinBorder)

    for n in range(0, rows):
        y = OrigY + int((MaxHeight / rows) * n)
        layout.append((x, y, width, height))

    return layout


def get_column_tile(wincount):
    persist_layout("get_column_tile")
    columns = wincount - 1
    layout = []
    if columns == 0:
        layout.append((OrigX, OrigY, MaxWidth, MaxHeight - WinTitle - WinBorder))
        return layout
    else:
        layout.append((OrigX, OrigY, int(MaxWidth * MwFactor), MaxHeight - WinTitle - WinBorder))

    x0 = OrigX + int((MaxWidth * MwFactor) + (2 * WinBorder))
    y = OrigY
    height = int(MaxHeight - WinBorder - WinTitle)
    width = int((MaxWidth * (1 - MwFactor)) / columns - 2 * WinBorder)

    for n in range(0, columns):
        x = x0 + (width + WinBorder) * n
        layout.append((x, y, width, height))

    return layout


def get_vertical_tile(wincount):
    persist_layout("get_vertical_tile")
    layout = []
    y = OrigY
    width = int(MaxWidth / wincount)
    height = MaxHeight - WinTitle - WinBorder
    for n in range(0, wincount):
        x = OrigX + n * width
        layout.append((x, y, width, height))

    return layout


def get_horiz_tile(wincount):
    persist_layout("get_horiz_tile")
    layout = []
    x = OrigX
    height = int(MaxHeight / wincount - WinTitle - WinBorder)
    width = MaxWidth
    for n in range(0, wincount):
        y = OrigY + int((MaxHeight / wincount) * n)
        layout.append((x, y, width, height))

    return layout


def retrieve_last_used_layout():
    fnc = retrieve(TempFile + "_last_layout").get("layout", "get_simple_tile")
    log.info("Retrieved last used layout: " + fnc)
    for key, value in globals().items():
        if key == fnc and callable(value):
            return value
    return get_simple_tile


def get_max_all(wincount):
    layout = []
    x = OrigX
    y = OrigY
    height = MaxHeight - WinTitle - WinBorder
    width = MaxWidth
    for n in range(0, wincount):
        layout.append((x, y, width, height))

    return layout


def move_active(PosX, PosY, Width, Height):
    windowid = ":ACTIVE:"
    move_window(windowid, PosX, PosY, Width, Height)


def move_window(windowid, PosX, PosY, Width, Height):
    """
    Resizes and moves the given window to the given position and dimensions
    """
    PosX = int(PosX)
    PosY = int(PosY)

    log.debug("moving window: %s to (%s,%s,%s,%s) " % (windowid, PosX, PosY, Width, Height))

    if windowid == ":ACTIVE:":
        window = "-r " + windowid
    else:
        window = "-i -r " + windowid

    # NOTE: metacity doesn't like resizing and moving in the same step
    # unmaximize
    os.system("wmctrl " + window + " -b remove,maximized_vert,maximized_horz")
    # resize
    command = "wmctrl " + window + " -e 0,-1,-1," + str(Width) + "," + str(Height)
    os.system(command)
    # move
    command = "wmctrl " + window + " -e 0," + str(max(PosX, 0)) + "," + str(max(PosY, 0)) + ",-1,-1"
    os.system(command)
    # set properties
    command = "wmctrl " + window + " -b remove,hidden,shaded"
    os.system(command)


def raise_window(windowid):
    if windowid == ":ACTIVE:":
        command = "wmctrl -a :ACTIVE: "
    else:
        command = "wmctrl -i -a " + windowid

    os.system(command)


def get_next_posx(current_x, new_width):
    if current_x < MaxWidth / Monitors:
        if new_width < MaxWidth / Monitors - WinBorder:
            PosX = OrigX + new_width
        else:
            PosX = OrigX
    else:
        if new_width < MaxWidth / Monitors - WinBorder:
            PosX = MaxWidth / Monitors + OrigX + new_width
        else:
            PosX = OrigX + MaxWidth / Monitors

    return PosX


def top_option():
    """
    Place the active window along the top of the screen
    """
    active = get_active_window()
    Width = get_middle_Width(active)
    Height = get_top_Height()
    PosX = get_middle_PosX(active, Width)
    PosY = get_top_PosY()
    move_window(active, PosX, PosY, Width, Height)
    raise_window(active)


def middle_option():
    """
    Place the active window in the middle of the screen
    """
    active = get_active_window()
    Width = get_middle_Width(active)
    Height = get_middle_Height()
    PosX = get_middle_PosX(active, Width)
    PosY = get_middle_PosY()
    move_window(active, PosX, PosY, Width, Height)
    raise_window(active)


def top_left_option():
    """
    Place the active window in the top left corner of the screen
    """
    active = get_active_window()
    Width = get_corner_Width(active)
    Height = get_top_Height()
    PosX = get_left_PosX(active, Width)
    PosY = get_top_PosY()
    move_window(active, PosX, PosY, Width, Height)
    raise_window(active)


def top_right_option():
    """
    Place the active window in the top right corner of the screen
    """
    active = get_active_window()
    Width = get_corner_Width(active)
    Height = get_top_Height()
    PosX = get_right_PosX(active, Width)
    PosY = get_top_PosY()
    move_window(active, PosX, PosY, Width, Height)
    raise_window(active)


def get_top_Height():
    return get_bottom_Height()


def get_middle_Height():
    return MaxHeight - WinTitle - WinBorder


def get_bottom_Height():
    return MaxHeight / 2 - WinTitle - WinBorder


def get_bottom_PosY():
    return MaxHeight / 2 + OrigY + WinBorder / 2 - (BottomPadding) / WinBorder


def get_middle_PosY():
    return get_top_PosY()


def get_top_PosY():
    return OrigY - TopPadding / WinBorder


def get_middle_Width(active):
    return get_next_width(int(get_window_width_height(active)[0]), CENTER_WIDTHS) + WinBorder


def get_corner_Width(active):
    return get_next_width(int(get_window_width_height(active)[0]), CORNER_WIDTHS)


def get_middle_PosX(active, Width):
    return get_next_posx(int(get_window_x_y(active)[0]), (MaxWidth / Monitors - Width) / 2) + WinBorder / 4


def get_right_PosX(active, Width):
    return get_next_posx(int(get_window_x_y(active)[0]), MaxWidth / Monitors - Width) - (
            RightPadding + LeftPadding) / WinBorder


def get_left_PosX(active, Width):
    return get_next_posx(int(get_window_x_y(active)[0]), 0)


def bottom_option():
    """
    Place the active window along the bottom of the screen
    """
    active = get_active_window()
    Width = get_middle_Width(active)
    Height = get_bottom_Height()
    PosX = get_middle_PosX(active, Width)
    PosY = get_bottom_PosY()
    move_window(active, PosX, PosY, Width, Height)
    raise_window(active)


def bottom_right_option():
    """
    Place the active window in the bottom right corner of the screen
    """
    active = get_active_window()
    Width = get_corner_Width(active)
    Height = get_bottom_Height()
    PosX = get_right_PosX(active, Width)
    PosY = get_bottom_PosY()
    move_window(active, PosX, PosY, Width, Height)
    raise_window(active)


def bottom_left_option():
    """
    Place the active window in the bottom left corner of the screen
    """
    active = get_active_window()
    Width = get_corner_Width(active)
    Height = get_bottom_Height()
    PosX = get_left_PosX(active, Width)
    PosY = get_bottom_PosY()
    move_window(active, PosX, PosY, Width, Height)
    raise_window(active)


def left_option():
    """
    Place the active window in the left corner of the screen
    """
    active = get_active_window()
    Width = get_corner_Width(active)
    Height = get_middle_Height()
    PosX = get_left_PosX(active, Width)
    PosY = get_middle_PosY()
    move_window(active, PosX, PosY, Width, Height)
    raise_window(active)


def right_option():
    """
    Place the active window in the right corner of the screen
    """
    active = get_active_window()
    Width = get_corner_Width(active)
    Height = get_middle_Height()
    PosX = get_right_PosX(active, Width)
    PosY = get_middle_PosY()
    move_window(active, PosX, PosY, Width, Height)
    raise_window(active)


def compare_win_list(newlist, oldlist):
    templist = []
    for window in oldlist:
        if newlist.count(window) != 0:
            templist.append(window)
    for window in newlist:
        if oldlist.count(window) == 0:
            templist.append(window)
    return templist


def create_win_list():
    Windows = WinList[Desktop]

    if OldWinList == {}:
        pass
    else:
        OldWindows = OldWinList[Desktop]
        if Windows == OldWindows:
            pass
        else:
            Windows = compare_win_list(Windows, OldWindows)

    for win in Windows:
        if not is_valid_window(win):
            Windows.remove(win)

    return Windows


def arrange(layout, windows):
    for win, lay in zip(windows, layout):
        move_window(win, lay[0], lay[1], lay[2], lay[3])
    WinList[Desktop] = windows
    store(WinList, TempFile)


def simple_option():
    """
    The basic tiling layout . 1 Main + all other at the side.
    """
    Windows = create_win_list()
    arrange(get_simple_tile(len(Windows)), Windows)


def simple_col_option():
    """
    The basic tiling layout . 1 Main + all other at the side (*Column).
    """
    Windows = create_win_list()
    arrange(get_column_tile(len(Windows)), Windows)


def swap_windows(window1, window2):
    """
    Swap window1 and window2
    """
    window1_area = lmap(lambda y: int(y), get_window_width_height(window1))
    window1_position = lmap(lambda y: int(y) - WinBorder / 2, get_window_x_y(window1))
    window2_area = lmap(lambda y: int(y), get_window_width_height(window2))
    window2_position = lmap(lambda y: int(y) - WinBorder / 2, get_window_x_y(window2))

    move_window(window1, window2_position[0], window2_position[1] - WinTitle, window2_area[0], window2_area[1])
    move_window(window2, window1_position[0], window1_position[1] - WinTitle, window1_area[0], window1_area[1])


def get_largest_window():
    """
    Returns the window id of the window with the largest area
    """
    winlist = create_win_list()

    max_area = 0
    max_win = winlist[0]

    for win in winlist:
        win_area = lreduce(lambda x, y: int(x) * int(y), get_window_width_height(win))
        if win_area > max_area:
            max_area = win_area
            max_win = win

    return max_win


def swap_grid_option():
    """
    Swap the active window with the largest window
    """
    active_window = get_active_window()
    largest_window = get_largest_window()

    swap_windows(active_window, largest_window)
    raise_window(active_window)


def swap_option():
    """
    Will swap the active window to master column
    """
    winlist = create_win_list()
    active = get_active_window()
    winlist.remove(active)
    winlist.insert(0, active)
    arrange(retrieve_last_used_layout()(len(winlist)), winlist)


def vertical_option():
    """
    Simple vertical tiling
    """
    winlist = create_win_list()
    active = get_active_window()
    winlist.remove(active)
    winlist.insert(0, active)
    arrange(get_vertical_tile(len(winlist)), winlist)


def horizontal_option():
    """
    Simple horizontal tiling
    """
    winlist = create_win_list()
    active = get_active_window()
    winlist.remove(active)
    winlist.insert(0, active)
    arrange(get_horiz_tile(len(winlist)), winlist)


def cycle_option():
    """
    Cycle all the windows in the master pane
    """
    winlist = create_win_list()
    winlist.insert(0, winlist[len(winlist) - 1])
    winlist = winlist[:-1]
    arrange(retrieve_last_used_layout()(len(winlist)), winlist)


def anticycle_option():
    """
    Cycle all the windows in the master pane in reverse
    """
    winlist = create_win_list()
    winlist.insert(len(winlist), winlist[0])
    winlist = winlist[1:]
    arrange(retrieve_last_used_layout()(len(winlist)), winlist)


def maximize_option():
    """
    Maximize the active window
    """
    Width = MaxWidth
    Height = MaxHeight - WinTitle - WinBorder
    PosX = LeftPadding
    PosY = TopPadding
    move_active(PosX, PosY, Width, Height)
    raise_window(":ACTIVE:")


def max_all_option():
    """
    Maximize all windows
    """
    winlist = create_win_list()
    active = get_active_window()
    winlist.remove(active)
    winlist.insert(0, active)
    arrange(get_max_all(len(winlist)), winlist)


def create_desktop(name: str, comment: str):
    log.info("Creating a .desktop file for " + name)
    desktop_file_content = f"""
    [Desktop Entry]
    Name=🖥️✏️ [Stiler] {name}
    Exec=python3 {os.path.abspath(__file__)} {name}
    Type=Application
    Comment={comment}
    GenericName={comment}
    """
    desktop_file_content = "\n".join(desktop_file_content.strip().splitlines(keepends=False)) + "\n"
    filename = f"tiler_op_{name}.desktop"
    desktop_file_path = os.path.join(os.path.expanduser("~"), ".local/share/applications", filename)
    with open(desktop_file_path, 'w') as desktop_file:
        desktop_file.write(desktop_file_content)
    log.info("Created: " + desktop_file_path)


def create_desktops_option():
    """
    Create .desktop files for all the options
    """
    for k, v in globals().items():
        if (k.endswith("_option")
                and k != "create_desktops_option"
                and k != "version_option"
                and k != "help_option"):
            create_desktop(k.rsplit("_", 1)[0], v.__doc__.strip())


def h_flag():
    """
    Display usage information
    """
    help_option()


def help_option():
    """
    Display usage information
    """
    print(f"\nUsage: {os.path.basename(sys.argv[0])} [FLAG] [OPTION]\n")

    option_list = []
    flag_list = []

    for key, value in globals().items():
        if callable(value):
            if key.endswith("_option"):
                option_list.append((key.rsplit("_", 1)[0], value.__doc__))
            elif key.endswith("_flag"):
                flag_list.append((key.rsplit("_", 1)[0], value.__doc__))

    option_list.sort()
    flag_list.sort()

    print(" Options:")
    for option, description in option_list:
        print(" {:<16} - {}".format(option, description.replace("\n", " ")))

    print()

    print(" Flags:")
    for flag, description in flag_list:
        print(" -{:<16} - {}".format(flag, description.replace("\n", " ")))

    print()
    version_option()


def eval_function(function_string):
    """
    Evaulate the given function.
    """
    for key, value in globals().items():
        if key == function_string and callable(value):
            value()
            return

    log.warning("Unrecognized option: " + function_string.rsplit("_", 1)[0])


def initialize_global_variables():
    """
    Initialize the global variables
    """

    # Screen Padding
    global BottomPadding, TopPadding, LeftPadding, RightPadding
    # Window Decoration
    global WinTitle, WinBorder
    # Grid Layout
    global CORNER_WIDTHS, CENTER_WIDTHS, Monitors, WidthAdjustment
    # Simple Layout
    global MwFactor
    # System Desktop and Screen Information
    global MaxWidth, MaxHeight, OrigX, OrigY, Desktop, WinList, OldWinList
    # Miscellaneous
    global TempFile, WindowFilter

    Config = initconfig()
    cfgSection = "DEFAULT"

    # use "default" for configurations written using the original stiler
    if Config.has_section("default"):
        cfgSection = "default"

    BottomPadding = Config.getint(cfgSection, "BottomPadding")
    TopPadding = Config.getint(cfgSection, "TopPadding")
    LeftPadding = Config.getint(cfgSection, "LeftPadding")
    RightPadding = Config.getint(cfgSection, "RightPadding")
    WinTitle = Config.getint(cfgSection, "WinTitle")
    WinBorder = Config.getint(cfgSection, "WinBorder")
    MwFactor = Config.getfloat(cfgSection, "MwFactor")
    TempFile = Config.get(cfgSection, "TempFile")
    Monitors = Config.getint(cfgSection, "Monitors")
    WidthAdjustment = Config.getfloat(cfgSection, "WidthAdjustment")
    WindowFilter = Config.getboolean(cfgSection, "WindowFilter")
    CORNER_WIDTHS = lmap(lambda y: float(y), Config.get(cfgSection, "GridWidths").split(","))

    # create the opposite section for each corner_width
    opposite_widths = []
    for width in CORNER_WIDTHS:
        opposite_widths.append(round(abs(1.0 - width), 2))

    # add the opposites
    CORNER_WIDTHS.extend(opposite_widths)

    CORNER_WIDTHS = list(set(CORNER_WIDTHS))  # filter out any duplicates
    CORNER_WIDTHS.sort()

    CENTER_WIDTHS = lfilter(lambda y: y < 0.5, CORNER_WIDTHS)
    CENTER_WIDTHS = lmap(lambda y: round(abs(y * 2 - 1.0), 2), CENTER_WIDTHS)
    CENTER_WIDTHS.append(1.0)  # always allow max for centers
    CENTER_WIDTHS = list(set(CENTER_WIDTHS))  # filter dups
    CENTER_WIDTHS.sort()

    # Handle multiple monitors
    CORNER_WIDTHS = lmap(lambda y: round(y / Monitors, 2) + WidthAdjustment, CORNER_WIDTHS)
    CENTER_WIDTHS = lmap(lambda y: round(y / Monitors, 2) + WidthAdjustment, CENTER_WIDTHS)

    log.debug("corner widths: %s" % CORNER_WIDTHS)
    log.debug("center widths: %s" % CENTER_WIDTHS)

    (Desktop, OrigXstr, OrigYstr, MaxWidthStr, MaxHeightStr, WinList) = initialize()
    MaxWidth = int(MaxWidthStr) - LeftPadding - RightPadding
    MaxHeight = int(MaxHeightStr) - TopPadding - BottomPadding
    OrigX = int(OrigXstr) + LeftPadding
    OrigY = int(OrigYstr) + TopPadding
    OldWinList = retrieve(TempFile)


def main():
    print(BANNER)
    if len(sys.argv) == 1:
        help_option()
        sys.exit(1)

    for arg in sys.argv:
        if arg == sys.argv[0]:
            continue
        elif arg.startswith("-"):
            eval_function(arg.split("-")[1] + "_flag")

    required_programs = ["wmctrl", "xprop", "xwininfo", "egrep", "grep"]
    if not has_required_programs(required_programs):
        sys.exit(1)

    initialize_global_variables()

    for arg in sys.argv:
        if arg == sys.argv[0]:
            continue
        elif arg.startswith("-"):
            continue
        else:
            eval_function(arg + "_option")


if __name__ == "__main__":
    main()
else:
    log.warning("Importing is not fully tested.  Use at your own risk.")
