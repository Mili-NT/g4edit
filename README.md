# g4edit
## Update:
Updating this on May 8th, 2026. 

I revisited this project for a reverse engineering project for college. The code is horribly
designed and was completely nonfunctional as far as editing the player's pokemon went. Through some better understanding
of how the code is actually written and a lot of banging my head against poor coding choices I made 6 years ago, it can
now functionally change AT LEAST the first pokemon in the player's party into another. Editing trainer values was never
a problem either.

I really enjoyed working on the data_functions.py stuff and the cryptography part of the pokemon data block, but the rest
not so much. It's to the point where it would be easier to tear out the insane Interface class and start from scratch
with just Save and main.py, so i'll leave this one in a semi-working state.

If you're doing a similar project and stumbled on this on github, read through char_conversion(), pokemon_conversion(),
generate_checksum(), rand(), xor(), crypt(). Other than that, make your life easier and check out the resources below.

## Usage:
G4Edit is a CLI save editor for pokemon generation 4 games (Diamond, Pearl, Platinum).

With it you can modify:

**Trainer Modifications**

* Trainer info (Name, Gender, TID, SID)
* Badges Collected
* Money
* Party

**Pokemon Modifications**

* Pokemon Info (Name, Species, Gender)
* Shinyness and Pokerus
* Nature
* Held Items
* Battle Info (Level, Moves, HP, Stats, etc.)
* And More

## Resources:

[1]. https://bulbapedia.bulbagarden.net/wiki/Save_data_structure_(Generation_IV)

[2]. https://github.com/pret/pokeplatinum

[3]. Leaked JP platinum source code (its out there)

## Usage:

`python3 g4edit.py <path to .sav file>`

or

`python3 g4edit.py`
