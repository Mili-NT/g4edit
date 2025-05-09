# g4edit

## Update
*Updated: May 8th, 2026*

I revisited this project for a reverse engineering assignment in college. The code was horribly designed and completely nonfunctional when it came to editing the player's Pokémon. With a better understanding of how the code actually works—and a lot of banging my head against poor choices I made six years ago—it can now functionally change **at least** the first Pokémon in the player's party.

Trainer value editing was never really an issue.

I really enjoyed working on `data_functions.py` and the cryptography related to Pokémon data blocks, but the rest... not so much. It's to the point where it would be easier to tear out the insane `Interface` class and start from scratch with just `Save` and `main.py`, so I'll leave this one in a semi-working state.

If you're doing a similar project and found this on GitHub, read through:

- `char_conversion()`
- `pokemon_conversion()`
- `generate_checksum()`
- `rand()`
- `xor()`
- `crypt()`

Other than that, make your life easier and check out the resources below.

---

## Usage
**G4Edit** is a CLI save editor for Pokémon Generation IV games (Diamond, Pearl, Platinum).  
With it, you can modify:

### **Trainer Modifications**
- Trainer info (Name, Gender, TID, SID)
- Badges collected
- Money
- Party

### **Pokémon Modifications**
- Pokémon info (Name, Species, Gender)
- Shininess and Pokerus
- Nature
- Held items
- Battle info (Level, Moves, HP, Stats, etc.)
- *And more*

---

## Resources
1. [Bulbapedia: Save Data Structure (Gen IV)](https://bulbapedia.bulbagarden.net/wiki/Save_data_structure_(Generation_IV))
2. [pret/pokeplatinum GitHub](https://github.com/pret/pokeplatinum)
3. Leaked JP Platinum source code *(it's out there)*

---

## Running

```bash
python3 g4edit.py <path to .sav file>
