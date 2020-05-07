#!/usr/bin/python3
import lib
import sys
import classes
# TODO: Interface
# TODO: Items and Inventory
# TODO: Party and Pokemon
# IMPORTANT FUNCTIONS
def load_file(fp):
    with open(fp, "rb+") as f:
        return classes.save(f.read(), f)
def main(filepath=None):
    if filepath:
        playersav = load_file("filepath")
    else:
        filepath = input("Enter the path to the .sav file: ")
        playersav = load_file(filepath)
# RUNPOINT
if __name__ == '__main__':
    try:
        main(sys.argv[1])
    except IndexError:
        main()

