#!/usr/bin/python3
import os
def bytearr_to_hexstring(bytearr):
    return ' '.join([f'{i:0>2X}' for i in bytearr])
def hex_to_string(bytearr):
    return ''.join([chr(bytearr[i:i + 2][0] + 22) for i in range(0, len(bytearr), 2)
                    if len(bytearr[i:i + 2]) > 1 and bytearr[i:i + 2][1] == 0x01])
#
# Color formatting
#
def cstring(msg, color=None):
    colors = {"grn":"\033[1;32m",
              "blu":"\033[1;34m",
              "prp":"\033[1;35m",
              "whi":"\033[1;37m"
              }
    if os.name == "nt":
        return msg
    else:
        formatted = f"{colors[color]}{msg}\033[1;m" if color else f"{colors['whi']}{msg}\033[1;m"
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
"""
    print(cstring(title.rstrip(), "prp"))
    print("---------A CLI Save Editor for Generation 4---------")
