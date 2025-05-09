#!/usr/bin/python3
import logging
import os
from platform import system

"""
Logging functions
"""
# Opens g4edit.log with w, so it clears previous logs. The Format is datetime - level => message
logging.basicConfig(filename='g4edit.log',
                    filemode='w',
                    format='%(asctime)s - (%(levelname)s) => %(message)s\n',
                    datefmt='%d-%b-%y %H:%M:%S',
                    level=logging.NOTSET)


def log(message, level='error', crashmsg='G4Edit encountered a fatal error.'):
    """
    :param message: The message to log
    :param level: the level to log as. This can be a string ('error', 'debug'), a char ('e', 'd'), or an int (40, 10).
    Defaults to error
    :param crashmsg: If the error is critical, include a message to print
    :return: Nothing, write to log file
    """
    # Maps the first char to the integer ID of the corresponding level
    levels = {'c': 50,
              'e': 40,
              'w': 30,
              'i': 20,
              'd': 10,
              'n': 0}
    try:
        # If a string level is passed, it takes the first char and gets corresponding ID
        if isinstance(level, str):
            setlevel = levels[level.lower()[0]]
        # If an int is passed, it checks if the int is a valid id by checking for presence in levels.values()
        elif isinstance(level, int) and level in list(levels.values()):
            # If valid, simply use the int
            setlevel = level
        # If neither are true, likely because the int isnt a valid ID, raises an exception
        else:
            raise Exception
    except Exception:
        # Logs that an invalid level argument was passed
        logging.warning('Passed level argument is not valid, defaulting to error (40)\n')
        # Defaults to 40, aka the Error level
        setlevel = 40
    # If the level is error, it includes the traceback
    if setlevel == 40:
        logging.error(message, exc_info=True)
    # If critical, includes traceback, prints a crash message, and exits
    elif setlevel == 50:
        logging.critical(message, exc_info=True)
        print(f'{crashmsg} Check g4edit.log for traceback info.')
        exit()
    # If not, simply log and append a newline
    else:
        logging.log(setlevel, message)


"""
Misc functions for colors and formatting
"""
colors = {"grn": "\033[1;32m",
          "blu": "\033[7;34;47m",
          "prp": "\033[1;35m",
          "whi": "\033[1;37m",
          "end": "\033[1;m",
          }
badge_color = ["\033[1;30;40m", "\033[1;37;42m", "\033[1;37;41m", "\033[1;37;44m", "\033[1;37;45m",
               "\033[2;33;40m", "\033[1;37;46m", "\033[1;37;43m", "\033[1;m"]


def cstring(msg, color=None):
    if os.name == "nt":
        return msg
    else:
        formatted = f"{colors[color]}{msg}{colors['end']}" if color else f"{colors['whi']}{msg}{colors['end']}"
        return formatted


def stripcolor(msg):
    for c in colors:
        msg = msg.replace(c, '')
    for c in badge_color:
        msg = msg.replace(c, ' ')
    return msg


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


def get_padded(string):
    uncolored = string
    for c in colors.values():
        uncolored = uncolored.replace(c, "")
    diff = 56 - len(uncolored)
    perside = ''.join(['-' for _ in range(diff // 2)])
    pad = f"{perside}{uncolored}{perside}"
    while len(pad) < 56:
        pad = f"{pad}-"
    return pad.replace(uncolored, string)


def clear():
    if system().lower() == 'windows':
        os.system('cls')
    else:
        os.system('clear')
