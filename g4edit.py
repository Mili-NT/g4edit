#!/usr/bin/python3
import os
import sys
import misc
import classes
# TODO: Interface and Text Wrapping
# TODO: Items and Inventory
# TODO: Party
# IMPORTANT FUNCTIONS
def load_file(fp):
    """
    load_file reads the file at path `fp` and returns a save object for the data contained

    :param fp: Filepath to .sav file
    :return: save object for that data
    """
    try:
        with open(fp, "rb+") as f:
            misc.log(f"File loaded from: {fp}", 'debug')
            return classes.save(f.read())
    except Exception as e:
        misc.log(e, 'critical', crashmsg="Fatal error encountered loading file with load_file().")
def main(filepath=None):
    """
    The main function for the program. Takes an optional parameter `filepath`, so the user can specify what file to load
    when they call the script. If one isn't passed, the user enters the filepath manually.

    :param filepath: Path to .sav file to load
    """
    try:
        # if filepath is not passed from command line, ask for filepath.
        if not filepath:
            while True:
                filepath = input("Enter the path to the .sav file: ")
                if os.path.isfile(filepath):
                    break
                else:
                    misc.log("Invalid filepath entered.", "info")
                    print("No file found at specified path.")
                    continue
        playersav = load_file(filepath)
        interface = classes.interface(playersav)
    except KeyboardInterrupt:
        misc.log("User closed program via keyboard interrupt", 'info')
        exit()
# RUNPOINT
if __name__ == '__main__':
    try:
        main(sys.argv[1])
    except IndexError:
        misc.log("No filepath passed", 'info')
        main()

