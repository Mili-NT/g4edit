#!/usr/bin/python3
import os
# Misc
def bytearr_to_hexstring(bytearr):
    return ' '.join([f'{i:0>2X}' for i in bytearr])
#
# Color formatting
#
colors = {"grn": "\033[1;32m",
          "blu": "\033[7;34;47m",
          "prp": "\033[1;35m",
          "whi": "\033[1;37m",
          "end":"\033[1;m",
          }
def cstring(msg, color=None):
    if os.name == "nt":
        return msg
    else:
        formatted = f"{colors[color]}{msg}{colors['end']}" if color else f"{colors['whi']}{msg}{colors['end']}"
        return formatted
# Other
def get_title():
    title = """
--------------------------------------------------------
|    ______    __ __       ______      __    _    __   |
|   / ____/   / // /      / ____/ ____/ /   (_)  / /_  |
|  / /  __   / // /_     / __/   / __  /   / /  / __/  |
| / /__/ /  /__  __/    / /___  / /_/ /   / /  / /_    |
| \_____/     /_/      /_____/  \____/   /_/   \__/    |
--------------------------------------------------------
""".lstrip()
    return f"{cstring(title.rstrip(), 'prp')}\n{cstring('-----------A CLI Save Editor for Generation 4-----------', 'prp')}"
