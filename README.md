# 🖥️ ✏️ stiler.py (v3.0)

* stiler.py - is a simple python script which does tiling on any X window-manager.
* stiler.py is known to work with pekwm, openbox, metacity, and compiz.

```
━━━━━━━━━━━━━━━━━━━━━━━━
┏┓  ┏┳┓•┓        ┏┓ ┏┓
┗┓━━ ┃ ┓┃┏┓┏┓  ┓┏ ┫ ┃┫
┗┛   ┻ ┗┗┗ ┛   ┗┛┗┛•┗┛
Simple Window Tiler
━━━━━━━━━━━━━━━━━━━━━━━━
```

# Requirements

* `wmctrl`          - used to get the window and desktop information and manage the windows
* `xprop`           - used to get the window information
* `xwininfo`        - used to get the window information
* `egrep`           - used to filter the window information
* `grep`            - used to filter the window information

# Usage

Usage: `stiler.py layout_option [flags]`

You can use `./stiler create_destops` to create .desktop files for layout commands. (For using with `rofi drun`)

## Put everything in to layout

* simple - The basic tiling layout . 1 Main + all other at the side.
* simple_col - Same as above but children are tiled in columns
* vertical - Simple vertical tiling
* horizontal - Simple horizontal tiling
* maximize - Maximize the active window/ for openbox which doesn't permit resizing of max windows
* max_all - Maximize all windows

## Modify current layout

* swap - Will swap the active window to master column
* cycle - Cycle all the windows in the master pane
* anticycle - Cycle all the windows (reverse)

## Move active window

* top_left - Place the active window in the top left corner of the screen
* top - Place the active window along the top of the screen
* top_right - Place the active window in the top right corner of the screen
* left,right - Does the new windows7 ish style of sticking to the sides.
* middle - Place the active window in the middle of the screen
* bottom_left - Place the active window in the bottom left corner of the screen
* bottom - Place the active window along the bottom of the screen
* bottom_right - Place the active window in the bottom right corner of the screen
* swap_grid - Swap the active window with the largest window

Multiple calls to any of the grid options on the same active window will select different widths.

On first run stiler will create a config file `~/.stilerrc`.
Modify the values to suit your window decorations/Desktop padding.
The two most influential values are the `winborder` and `wintitle` values.

## Flags

* -v - Enable DEBUG level verbosity
* -h - Display usage information

# Options

## ~/.stilerrc file options

* leftpadding - pads the left hand side of the screen the given number of pixels
* toppadding - pads the top of the screen the given number of pixels
* bottompadding - pads the bottom of the screen the given number of pixels
* rightpadding - pads the right hand side of the screen the given number of pixels

## Window padding options

* winborder - pads the given number of pixels around each window
* wintitle - pads the given number of pixels above each window

## miscellaneous options

* tempfile - cache file for holding window positions
* windowfilter - exclude minimized and UTILITY windows from being tiled

## simple layout options

* mwfactor - width of the bigger window in the simple layout

## grid layout options

* monitors - for a dual monitor setup set this to 2
* gridwidths - a list of locations on the screen at which to place the borders of the grid. Each location is mirrored
  across 1/2 the screen. For example, a gridwidths list of 0.17,0.33,0.50 creates grid borders at
  0.17,0.33,0.50,0.67,0.83
* widthadjustment - sometimes the gridwidths end up being rounded too high or low which can be common in a dual monitor
  setup. Use the widthadjustment to account for rounding error.

# Known Issues

* compiz - compiz says it has a single desktop even if there are 4 virtual desktops, which means all the windows you
  have will be tiled.
* firefox - firefox get a little stubborn when resized below a certain point

# License

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
