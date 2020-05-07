#!/usr/bin/python3
import os
def bytearr_to_hexstring(bytearr):
    return ' '.join([f'{i:0>2X}' for i in bytearr])
def hex_to_string(bytearr):
    return ''.join([chr(bytearr[i:i + 2][0] + 22) for i in range(0, len(bytearr), 2)
                    if len(bytearr[i:i + 2]) > 1 and bytearr[i:i + 2][1] == 0x01])
#
# overloaded print
#
def cstring(msg, color=None):
    colors = {"g/blk":"\x1b[1;32;40m",
              "w/blk":"\x1b[0;37;40m",
              "w/blu":"\x1b[1;37;44m",
              "g/blu":"\x1b[1;32;44m",
              "g/whi":"\x1b[1;32;47m"
              }
    if os.name == "nt":
        return msg
    else:
        formatted = f"{colors[color]}{msg}\x1b[0m" if color else f"{colors['w/blk']}{msg}\x1b[0m"
        return formatted
