#!/usr/bin/python3
import os
# Variables
colors = {"grn": "\033[1;32m",
          "blu": "\033[7;34;47m",
          "prp": "\033[1;35m",
          "whi": "\033[1;37m",
          "end":"\033[1;m",
          }
offsets = {
            'small_block': (0x00000,0x0CF2B),
            'small_block_backup': ((0x00000 + 0x40000),(0x0CF2B + 0x40000)),
            'small_block_footer': (0x0CF2B - 0x14, 0x0CF2B),
            'big_block': (0x0CF2C, 0x1F10F),
            'big_block_backup': ((0x0CF2C + 0x40000),(0x1F10F + 0x40000)),
            'big_block_footer': (0x1F10F - 0x14, 0x1F10F),
            'trainer_name': (0x68,0x77),
            'trainer_id': (0x78,0x79),
            'secret_id': (0x7A,0x7B),
            'money': (0x7C,0x7F),
            'gender': 0x80,
            'badges': 0x82,
            'in_party': 0x9C,
            'party_blocks': (0xA0,0x627),
            'items_placeholder': (0x00630,0x008C3),
            'keyitems_placeholder': (0x008C4,0x0098B),
            'machines_placeholder': (0x0098C,0x00B4B),
            'medicine_placeholder': (0x00B4C,0x00BEB),
            'berries_placeholder': (0x00BDC,0x00CEB),
            'pokeballs_placeholder': (0x00CEC,0x00D27),
            'battleitems_placeholder': (0x00D28,0x00D5B),
            'mail_placeholder': (0x00D5C,0x00D8B),
            'item': (0x02,0x03),
            'item_amount':(0x02,0x03),
        }
# Misc
def bytearr_to_hexstring(bytearr):
    return ' '.join([f'{i:0>2X}' for i in bytearr])
def hex_to_string(bytearr):
    return ''.join([chr(bytearr[i:i + 2][0] + 22) for i in range(0, len(bytearr), 2)
                    if len(bytearr[i:i + 2]) > 1 and bytearr[i:i + 2][1] == 0x01])
def hexdump(bytearr, dumpname):
    with open(f"{dumpname}.txt", 'w+') as f:
        f.write(bytearr_to_hexstring(hex_to_string(bytearr)))
def xor_bytes(byte1, byte2):
    return bytes([_a ^ _b for _a, _b in zip(byte1, byte2)])

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
