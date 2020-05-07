#!/usr/bin/python3
import os
# Variables
colors = {"grn": "\033[1;32m",
          "blu": "\033[7;34;47m",
          "prp": "\033[1;35m",
          "whi": "\033[1;37m",
          "end":"\033[1;m",
          }
# Misc
def bytearr_to_hexstring(bytearr):
    return ' '.join([f'{i:0>2X}' for i in bytearr])
def hex_to_string(bytearr):
    return ''.join([chr(bytearr[i:i + 2][0] + 22) for i in range(0, len(bytearr), 2)
                    if len(bytearr[i:i + 2]) > 1 and bytearr[i:i + 2][1] == 0x01])
#
# Color formatting
#
def cstring(msg, color=None):
    if os.name == "nt":
        return msg
    else:
        formatted = f"{colors[color]}{msg}{colors['end']}" if color else f"{colors['whi']}{msg}{colors['end']}"
        return formatted
# Other
def print_title():
    title = """
----------------------------------------------------
|    ______   __ __    ______      __    _    __   |
|   / ____/  / // /   / ____/ ____/ /   (_)  / /_  |
|  / / __   / // /_  / __/   / __  /   / /  / __/  |
| / /_/ /  /__  __/ / /___  / /_/ /   / /  / /_    |
| \____/     /_/   /_____/  \__,_/   /_/   \__/    |
----------------------------------------------------
""".lstrip()
    print(cstring(title.rstrip(), "prp"))
    print(cstring("---------A CLI Save Editor for Generation 4---------", 'prp'))
