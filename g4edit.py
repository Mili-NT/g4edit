#!/usr/bin/python3
import classes
import sys
"""
LITTLE ENDIAN
In Platinum:
---------------------------------------------------------------
1. the first small block starts at 0x00000 and ends at 0x0CF2B
2. the first big block starts at 0x0CF2C and ends at 0x1F10F. 
3. The second pair of blocks are at the same address plus 0x40000 for all the three games.
---------------------------------------------------------------
One block pair is always a backup of the other block pair. 


Name -> DUMB : AAAAAAA (max 7 char)
Rival Name -> FAGGOT : BBBBBBB
TID -> 29156 : 48611
SID -> 30151 : 45433
"""
# IMPORTANT FUNCTIONS
def load_file(fp):
    with open(fp, "rb") as f:
        return classes.save(f.read())
def main(filepath=None):
    if filepath:
        playersav = load_file(filepath)
    else:
        filepath = input("Enter the path to the .sav file: ")
        playersav = load_file(filepath)
    playersav.player.display_trainer_info()
# RUNPOINT
if __name__ == '__main__':
    try:
        main(sys.argv[1])
    except IndexError:
        main()

