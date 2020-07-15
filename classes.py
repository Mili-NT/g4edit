from time import sleep
import misc
import indexes
import itertools
import random
from platform import system
import data_functions as df

class interface:
    def __init__(self, saveobj):
        self.save = saveobj
        self.header = misc.get_title()
        print(self.header)
        print(f"{self.save.player.display_trainer_info()}\n"
              f"{self.save.player.display_party_info()}")
        self.command()
    def command(self):
        while True:
            print(misc.get_padded("Command Input"))
            print("[1]. Edit Trainer\n[2]. Edit Party\n[3]. Save\n[4]. Exit")
            cmd = input("Command: ").lower()
            if cmd in ['1', 'edit trainer', 'edit t']:
                try:
                    self.save.player.edit()
                except Exception as e:
                    misc.log(e, 'e')
            elif cmd in ['2', 'edit party', 'edit p']:
                try:
                    self.save.player.trainer_party.edit()
                except Exception as e:
                    misc.log(e, 'e')
            elif cmd in ['3', 'save']:
                self.save.save()
                self.refresh()
            elif cmd in ['4', 'exit']:
                print("Warning! Unsaved modifications will disappear!")
                if input("Save? [y/n]: ").lower() in ['y', 'yes']:
                    self.save.save()
                exit()
            else:
                continue
            self.refresh()
    def refresh(self):
        misc.clear()
        print(self.header)
        print(f"{self.save.player.display_trainer_info()}\n{self.save.player.display_party_info()}")
class pokemon:
    def __init__(self, data_block, trainer_info, slotnumber=0):
        self.trainer_info = trainer_info
        self.whole = data_block
        self.decrypted = df.pokemon_conversion(data_block)
        self.pokemon = self.decrypted[0]
        self.pid = self.decrypted[1]
        self.checksum = self.decrypted[2]
        self.slotnumber = slotnumber
        # General
        self.general_info = {
            'species_id': df.byte_conversion(self.pokemon[0x08:0x0A], 'H')[0],
            'species': df.get_index(indexes.pkmn, df.byte_conversion(self.pokemon[0x08:0x0A], 'H')[0]),
            'name': df.char_conversion(self.pokemon[0x48:0x5D]),
            'gender':'Genderless' if self.pokemon[0x40] == 4 else ('Male' if self.pokemon[0x40] == 0 else 'Female'),
            'ratio': df.get_index(indexes.gender_ratios, df.byte_conversion(self.pokemon[0x08:0x0A], 'H')[0]),
            'nature': df.get_index(indexes.natures, self.pid % 25),
            'item': df.get_index(indexes.items, df.byte_conversion(self.pokemon[0x0A:0x0C], 'H')[0]),
            'pokeball': df.get_index(indexes.items, self.pokemon[0x83]),
            'pokerus': False if self.pokemon[0x82] == 0 else True,
            'plat_met_at': df.get_index(indexes.locations, df.byte_conversion(self.pokemon[0x46:0x48], 'H')[0]),
        }
        # Trainer info
        self.ot_info = {'tid': df.byte_conversion(self.pokemon[0x0C:0x0E], 'H')[0],
                        'sid': df.byte_conversion(self.pokemon[0x0E:0x10], 'H')[0],
                        'ot_name':df.char_conversion(self.pokemon[0x68:0x77])}
        # Battle related stats
        self.battle = {
            'level':self.pokemon[0x8C],
            'xp': df.byte_conversion(bytearray(self.pokemon[0x10:0x13] + b'\x00'), 'I')[0],
            'ability':df.get_index(indexes.abilities, self.pokemon[0x15]),
            'moveset': self.format_moves(),
            'current_hp':df.byte_conversion(self.pokemon[0x8E:0x8F], 'B')[0],
            'max_hp':df.byte_conversion(self.pokemon[0x90:0x91], 'B')[0],
            'attack': df.byte_conversion(self.pokemon[0x92:0x94], 'H')[0],
            'defense': df.byte_conversion(self.pokemon[0x94:0x95], 'B')[0],
            'speed': df.byte_conversion(self.pokemon[0x96:0x97], 'B')[0],
            'spec_attack': df.byte_conversion(self.pokemon[0x98:0x99], 'B')[0],
            'spec_defense': df.byte_conversion(self.pokemon[0x9A:0x9B], 'B')[0]
        }
        # If the slot is empty, set pokemon name to empty to prevent it returning ???????
        if df.byte_conversion(self.pokemon[0x08:0x0A], 'H')[0] == 0:
            self.general_info['name'] = 'Empty'
    # GENERAL METHODS
    def format_moves(self):
        tupled = [tuple(x) for x in df.list_to_chunks([x for x in self.pokemon[0x28:0x30]], 2)]
        moves = [df.get_index(indexes.moves, x[0]+256) if x[1] == 1 else df.get_index(indexes.moves, x[0]) for x in tupled]
        pp = [x for x in self.pokemon[0x30:0x34]]
        for x in range(len(pp)):
            if isinstance(moves[x]['pp'], tuple) is False:
                moves[x]['pp'] = (pp[x], moves[x]['pp'])
            else:
                moves[x]['pp'] = (pp[x], moves[x]['pp'][1])
        return moves
    def xp_to_next_lvl(self, specid, level):
        """
        This calculates how much XP is needed to get to the next level for the pokemon's experience group using
        the indexes stored in indexes.py

        :param specid: species ID of the pokemon (stored in self.general_info dict)
        :param level: The pokemon's level (stored in self.battle dict)
        :return: integer value representing the needed XP
        """
        # If level 100, it cant be leveled up
        if level == 100:
            return 0
        # placeholder variable to store the name of the experience group the pokemon is in
        rate = ''
        # Iterates over the names of the experience groups: Erratic, Fast, Medium-Fast, Medium-Slow, Slow and Fluctuating
        for category in indexes.growth_rates.keys():
            # The values of the growth_rates index is an array containing the names of all pokemon in that XP group
            # So we get the name via passing the species ID to the pkmn index and check if it is in the XP group
            if df.get_index(indexes.pkmn, specid) in indexes.growth_rates[category]:
                # Update the placeholder variable to the category name
                rate = category
        """
        This is where it gets a bit messy.
        
        The xp_growth index contains each level 0-100 as a key, with a value consisting of an array containing the 
        minimum amount of XP needed to level up for each category. The group_indexes index maps the group name to the
        that group's position in the xp_growth array. For example, group_indexes['fast'] is 4, so the 4th element in 
        the xp_growth array is the fast value.
        
        So indexes.xp_growth[level][indexes.group_indexes[rate]] ultimately gives us the minimum needed XP for the group
        the pokemon belongs to. But we want the XP to the next level, so we find the value for the previous level using
        the same look-ups, and get the difference.
        """
        return indexes.xp_growth[level][indexes.group_indexes[rate]] - indexes.xp_growth[level-1][indexes.group_indexes[rate]]
    def xp_min(self, specid, level):
        """
        This fetches the minimum XP needed to be the CURRENT LEVEL

        :param specid: species ID of the pokemon (stored in self.general_info dict)
        :param level: The pokemon's level (stored in self.battle dict)
        :return: The minimum XP to be that level
        """
        # If the level is 1, it doesnt need any
        if level <= 1:
            return 0
        # This is identical to the self.xp_to_next_lvl() lookup loop.
        # Iterates over the XP groups, finds which group the pokemon belongs to, assigns the group name to the rate variable
        rate = ''
        for category in indexes.growth_rates.keys():
            if df.get_index(indexes.pkmn, specid) in indexes.growth_rates[category]:
                rate = category
        return indexes.xp_growth[level-1][indexes.group_indexes[rate]]
    def set_new_pv(self, gender=None, nature=None, shiny=False):
        """
        This generates a new 4 byte personality value to account for changes. Any aspect not passed in as a parameter
        stays the same.

        !! Personality value is alternately referred to as PID or PV !!

        :param gender: 0 for male, 1 for female
        :param nature: string of nature to change to, i.e: 'hardy', 'adamant', 'lonely'
        :param shiny: True to generate a shiny PID, else False
        :return: New PID matching specifications passed as params
        """
        # The gender_ratio is a value that is used to determine gender. Values for each pokemon species are stored in
        # the gender_ratios index in indexes.py
        gender_ratio = self.general_info['ratio']
        # Sets nature to passed value, if any value is passed. Otherwise it defaults to the current nature.
        nature = nature if nature else self.pid % 25
        # Sets gender to passed value, if any value is passed. Otherwise it uses the lambda function below to
        # determine the gender from the personality value. If the personality value % 256 is less than the gender ratio
        # the pokemon is female. If it is greater than or equal to the gender ratio, it is male
        gender = gender if gender is not None else (lambda opv: 1 if opv % 256 < gender_ratio else 0)(self.pid)
        # If the pokemon is not being made shiny, it takes the current shinyness boolean as default
        if shiny is False:
            shiny = self.check_shiny(self.pid)
        # initiate a loop that we can exit when we get a PID that satisfies all set requirements
        while True:
            # Generate a new random 32 bit integer
            new_pid = random.getrandbits(32) & 0xffffffff
            # If the PID is greater than the max allowed, we continue and generate a new one
            if new_pid > 4294967295:
                continue
            # If the pokemon is always male (0), always female (254), or genderless (255) and the PID's gender value
            # doesn't equal the respective value, we try again
            if gender_ratio in [0, 254, 255] and new_pid % 256 != gender_ratio:
                continue
            # If the new PID doesn't have the correct gender, continue
            if (lambda pid: 1 if pid % 256 < gender_ratio else 0)(new_pid) != gender:
                continue
            # If the nature isnt correct, continue
            if new_pid % 25 != nature:
                continue
            # if we're making the pokemon shiny and the new PID isn't shiny, continue
            if shiny and self.check_shiny(new_pid) is False:
                continue
            else:
                """
                I noticed a slight margin of error when generating PIDs, this merely gets all attributes for the
                new PID, displays them, and asks if they're correct
                """
                new_gender = 'Female' if (lambda pv: 1 if pv % 256 < gender_ratio else 0)(new_pid) == 1 else 'Male'
                print(f"Gender: {new_gender}\nNature: {df.get_index(indexes.natures, new_pid % 25)}\nShiny: {self.check_shiny(new_pid)}")
                cont = input("Does this look correct? [y]/[n]: ")
                if cont.lower() in ['y', 'yes']:
                    # Updates the gender byte to match PID
                    if new_gender == 'Genderless':
                        df.write_to_offset(self.pokemon, 0x40, 4)
                    elif new_gender == 'Female':
                        df.write_to_offset(self.pokemon,0x40, 2)
                    elif new_gender == 'Male':
                        df.write_to_offset(self.pokemon,0x40, 0)
                    # Writes PID to offset and updates it
                    df.write_to_offset(self.pokemon,(0x00, 0x04), df.byte_conversion(new_pid, 'I', encode=True))
                    self.pid = new_pid
                    break
    def check_shiny(self, pid):
        """
        :param pid: personality value
        :return: True if shiny, False otherwise
        """
        # trainer ID
        tid = self.ot_info['tid']
        # secret ID
        sid = self.ot_info['sid']
        # The first half (2 bytes) of the personality value
        p1 = int(pid / 65536)
        # The second half (2 bytes) of the personality value
        p2 = pid % 65536
        # An XOR chain is performed to get the shiny value
        isShiny = tid ^ sid ^ p1 ^ p2
        # If the shiny value is less than 8, it is shiny
        return True if isShiny < 8 else False
    # UPDATE/SAVE
    def update(self):
        """
        The update function simply redeclares the three information dictionaries to update them
        """
        self.general_info = {
            'species_id': df.byte_conversion(self.pokemon[0x08:0x0A], 'H')[0],
            'species': df.get_index(indexes.pkmn, df.byte_conversion(self.pokemon[0x08:0x0A], 'H')[0]),
            'name': df.char_conversion(self.pokemon[0x48:0x5D]),
            'gender': 'Genderless' if self.pokemon[0x40] == 4 else ('Male' if self.pokemon[0x40] == 0 else 'Female'),
            'ratio': df.get_index(indexes.gender_ratios, df.byte_conversion(self.pokemon[0x08:0x0A], 'H')[0]),
            'nature': df.get_index(indexes.natures, self.pid % 25),
            'item': df.get_index(indexes.items, df.byte_conversion(self.pokemon[0x0A:0x0C], 'H')[0]),
            'pokeball': df.get_index(indexes.items, self.pokemon[0x83]),
            'pokerus': False if self.pokemon[0x82] == 0 else True,
            'plat_met_at': df.get_index(indexes.locations, df.byte_conversion(self.pokemon[0x46:0x48], 'H')[0]),
        }
        self.ot_info = {'tid': df.byte_conversion(self.pokemon[0x0C:0x0E], 'H')[0],
                        'sid': df.byte_conversion(self.pokemon[0x0E:0x10], 'H')[0],
                        'ot_name': df.char_conversion(self.pokemon[0x68:0x77])}
        self.battle = {
            'level': self.pokemon[0x8C],
            'xp': df.byte_conversion(bytearray(self.pokemon[0x10:0x13] + b'\x00'), 'I')[0],
            'ability': df.get_index(indexes.abilities, self.pokemon[0x15]),
            'moveset': self.format_moves(),
            'current_hp': df.byte_conversion(self.pokemon[0x8E:0x8F], 'B')[0],
            'max_hp': df.byte_conversion(self.pokemon[0x90:0x91], 'B')[0],
            'attack': df.byte_conversion(self.pokemon[0x92:0x94], 'H')[0],
            'defense': df.byte_conversion(self.pokemon[0x94:0x95], 'B')[0],
            'speed': df.byte_conversion(self.pokemon[0x96:0x97], 'B')[0],
            'spec_attack': df.byte_conversion(self.pokemon[0x98:0x99], 'B')[0],
            'spec_defense': df.byte_conversion(self.pokemon[0x9A:0x9B], 'B')[0]
        }
    def save(self):
        """
        save encodes and shuffles the pokemon bytearray and returns it

        :return: Encoded and shuffled pokemon bytearray
        """
        enc = df.pokemon_conversion(self.pokemon, encode=True)[0]
        return enc
    # DISPLAYS
    def display(self, item):
        """
        display formats the dictionaries and returns them as a string for printing

        :param item: Which dict to print
        :return: Formatted display string
        """
        if item == 'general':
            lines = [
                misc.get_padded(f"General Info for Slot {self.slotnumber}"),
                f"Name: {self.general_info['name']}",
                f"Species: {self.general_info['species']}",
                f"Gender: {self.general_info['gender']} (Ratio: {self.general_info['ratio']})",
                f"Held Item: {self.general_info['item']}",
                f"Caught in: {self.general_info['pokeball']}",
                f"Met at {self.general_info['plat_met_at']}",
                f"Pokerus: {self.general_info['pokerus']}",
                f"Shiny: {self.check_shiny(self.pid)}"
            ]
        elif item == 'ot':
            lines = [
                misc.get_padded(f"OT Info for Slot {self.slotnumber}"),
                f"Trainer ID: {self.ot_info['tid']}",
                f"Secret ID: {self.ot_info['tid']}",
                f"OT Name: {self.ot_info['ot_name']}",
            ]
        elif item == 'stats':
            lines = [
                misc.get_padded(f"Battle Info for Slot {self.slotnumber}"),
                f"Level: {self.battle['level']}",
                f"Experience: {self.battle['xp']} ({self.xp_to_next_lvl(self.general_info['species_id'], self.battle['level'])} to next level)",
                f"Ability: {self.battle['ability'][0]}\n{self.battle['ability'][1]}",
                f"Current HP: {self.battle['current_hp']}",
                misc.get_padded("Stats"),
                f"Max HP: {self.battle['max_hp']}",
                f"Attack: {self.battle['attack']}",
                f"Defense: {self.battle['defense']}",
                f"Speed: {self.battle['speed']}",
                f"Special Attack: {self.battle['spec_attack']}",
                f"Special Defense: {self.battle['spec_defense']}",
                misc.get_padded("Moves")
            ]
            for index,item in enumerate(self.battle['moveset']):
                lines.append(f"[{index+1}]: {item['name']} ({item['pp'][0]}pp/{item['pp'][1]}pp)")
            return '\n'.join(lines), lines
        return '\n'.join(lines)
    def display_pkmn(self):
        """
        The initial display shown upon selecting the pokemon from the party editor screen
        """
        misc.clear()
        print(misc.get_padded(f"Slot Number {self.slotnumber}"))
        print(f"PV: {self.pid}")
        print(self.display('general'))
        print(self.display('ot'))
        print(self.display('stats')[0])
    # EDITS
    def edit(self):
        while True:
            self.update()
            misc.clear()
            print(misc.get_padded(f"Edit Menu For Slot {self.slotnumber}"))
            self.display_pkmn()
            print(misc.get_padded("Edit"))
            print("[1]. General Info (Species, Name, Etc.)\n[2]. OT Info (OT name, ID, SID)\n[3]. Battle Stats\n"
                  "['back' to return to previous menu.]")
            editchoice = input("Edit which: ")
            if editchoice.lower() in ['g', 'gen', 'general', 'general info', '1']:
                self.edit_general()
            elif editchoice.lower() in ['ot', 'trainer', 'ot info', 't', 'trainer info', '2']:
                self.edit_ot()
            elif editchoice.lower() in ['battle', 'b', 'battle info', 'stats', 's', 'stats info', 'battle stats', '3']:
                self.edit_battle()
            elif editchoice.lower() == 'back':
                  break
            else:
                sleep(0.5)
                print("Invalid Option.")
            continue
    # EDIT SUBMENUS
    def edit_general(self):
        while True:
            self.update()
            misc.clear()
            print(misc.get_padded(f"General Info for Slot {self.slotnumber}"))
            self.display('general')
            opts = {
                '1':'species',
                '2':'name',
                '3':'gender',
                '4':'nature',
                '5':'item',
                '6':'pokeball',
                '7':'pokerus',
                '8': 'location',
                '9': 'shinyness'
            }
            for x in opts:
                print(f"[{x}]: {opts[x]}")
            print("['back' to return to the previous menu.]")
            print(''.join('-' for _ in range(56)))
            element = input("Edit which: ")
            if element == 'back':
                break
            elif element in ['1', 'species']:
                while True:
                    print("Note: For Nidoran variants, do Nidoran-f or Nidoran-m respectively.")
                    new_species = input("Enter the name of the new species: ").title()
                    # Special cases
                    if new_species == "Nidoran-M":
                        new_species = "Nidoran♂"
                    elif new_species == "Nidoran-F":
                        new_species = "Nidoran♀"
                    elif new_species == "Mr Mime":
                        new_species = "Mr. Mime"
                    elif new_species == "Mime Jr":
                        new_species = "Mime Jr."
                    if df.is_valid(indexes.pkmn, new_species, is_val=True):
                        spec_id = df.get_index(indexes.pkmn, new_species, from_val=True)
                        spec_id_to_bytes = df.byte_conversion(spec_id, 'H', encode=True)
                        misc.log(f"New SPECID: {spec_id}. Writing {spec_id_to_bytes} to 0x08:0x0A")
                        df.write_to_offset(self.pokemon, (0x08,0x0A), spec_id_to_bytes)
                        break
                    else:
                        print("No such pokemon found. Only pokemon from Gen I -> Gen IV are valid.")
                        continue
            elif element in ['2', 'name']:
                while True:
                    new_name = input("Enter a new name: ")
                    if len(f"{new_name}") == 10:
                        encoded = df.char_conversion(new_name, encode=True, pad=[255])
                    elif 0 < len(f"{new_name}") < 10:
                        encoded = df.char_conversion(data=new_name, encode=True, pad=[255, 255] + [0 for _ in range((21 - len(new_name * 2)) - 2)])
                    else:
                        print("Name must be greater than 0 and no more than 10 characters.")
                        continue
                    df.write_to_offset(self.pokemon, (0x48, 0x5D), encoded)
                    break
            elif element in ['3', 'gender']:
                while True:
                    new_gender = input("Make [Male] or [Female]: ")
                    if self.general_info['ratio'] == 255:
                        print(f"{self.general_info['species']} is genderless.")
                    elif self.general_info['ratio'] == 254:
                        print(f"{self.general_info['species']} is Female-Only.")
                    elif self.general_info['ratio'] == 0:
                        print(f"{self.general_info['species']} is Male-Only.")
                    else:
                        gender_as_int = 0 if new_gender.lower() in ['m', 'male', '0'] else 1
                        self.set_new_pv(gender=gender_as_int)
                    break
            elif element in ['4', 'nature']:
                while True:
                    new_nature = input("Enter the new nature (hardy, brave, etc.): ").title()
                    if df.is_valid(indexes.natures, new_nature, is_val=True):
                        self.set_new_pv(nature=df.get_index(indexes.natures, new_nature, from_val=True))
                        break
                    else:
                        print("No such nature found.")
                        print("Check https://bulbapedia.bulbagarden.net/wiki/Nature or indexes.py for valid natures.")
                        continue
            elif element in ['5', 'item']:
                while True:
                    new_item = input("Enter the name of the item: ")
                    if df.is_valid(indexes.items, new_item, is_val=True):
                        itemid = df.get_index(indexes.items, new_item, from_val=True)
                        df.write_to_offset(self.pokemon, 0x83, itemid)
                        break
                    else:
                        print("No such item found.")
                        print("Check https://bulbapedia.bulbagarden.net/wiki/List_of_items_by_index_number_(Generation_IV)")
                        continue
            elif element in ['6', 'pokeball']:
                while True:
                    new_ball = input("Enter new ball name: ").title()
                    if new_ball in ['Pokeball', 'Poke Ball']:
                        new_ball_id = 4
                    else:
                        new_ball_id = df.get_index(indexes.items, new_ball, from_val=True)
                    if new_ball_id:
                        df.write_to_offset(self.pokemon, 0x83, new_ball_id)
                        break
                    else:
                        continue
            elif element in ['7', 'pokerus']:
                while True:
                    new_pkrus = input("Enable pokerus: [y]/[n]: ")
                    if new_pkrus.lower() in ['y', 'yes']:
                        df.write_to_offset(self.pokemon, 0x82, 1)
                    elif new_pkrus.lower() in ['n', 'no']:
                        df.write_to_offset(self.pokemon, 0x82, 1)
                    else:
                        print("Invalid option.")
                        continue
                    break
            elif element in ['8', 'location']:
                while True:
                    new_loc = input("Enter the name of the new location: ")
                    new_loc_id = 0
                    for x in indexes.locations.keys():
                        if indexes.locations[x].lower().replace(' ', '') == new_loc.lower().replace(' ', ''):
                            new_loc_id = x
                    if new_loc_id == 0:
                        print("Invalid location name.")
                        continue
                    encoded = df.byte_conversion(new_loc_id, 'H', encode=True)
                    df.write_to_offset(self.pokemon, (0x46,0x48), encoded)
                    break
            elif element in ['9', 'shinyness']:
                while True:
                    make_shiny = input("Make shiny: [y]/[n]: ")
                    if make_shiny.lower() in ['y', 'yes']:
                        self.set_new_pv(shiny=True)
                    elif make_shiny.lower() in ['n', 'no']:
                        self.set_new_pv(shiny=False)
                    else:
                        print("Invalid option.")
                        continue
                    break
    def edit_ot(self):
        while True:
            self.update()
            misc.clear()
            print(misc.get_padded(f"OT Info for Slot {self.slotnumber}"))
            self.display('ot')
            print("[1]. Trainer ID\n[2]. Secret ID\n[3]. OT Name\n['back' to return to edit menu]")
            element = input("Edit which: ")
            if element not in ['1', '2', '3', 'back']:
                print("Invalid Option")
                continue
            elif element in ['1', '2']:
                while True:
                    try:
                        id_type = 'trainer' if element == '1' else 'secret'
                        new_id = input(f"Enter new {id_type} ID (leave blank to set your current ID): ")
                        if new_id == '':
                            new_id = self.trainer_info['tid'] if id_type == 'trainer' else self.trainer_info['sid']
                            encoded = df.byte_conversion(new_id, 'H', encode=True)
                            if id_type == 'trainer':
                                df.write_to_offset(self.pokemon, (0x0C, 0x0E), encoded)
                            else:
                                df.write_to_offset(self.pokemon, (0x0E, 0x10), encoded)
                        else:
                            new_id = int(new_id)
                            if 0 < new_id <= 65535:
                                encoded = df.byte_conversion(new_id, 'H', encode=True)
                                if id_type == 'trainer':
                                    df.write_to_offset(self.pokemon, (0x0C,0x0E), encoded)
                                else:
                                    df.write_to_offset(self.pokemon, (0x0E,0x10), encoded)
                                break
                            else:
                                raise ValueError
                    except Exception as e:
                        misc.log(e, 'error')
                        print(f"New {'trainer' if element == '1' else 'secret'} ID must be greater than 0 and less than 65535.")
                        continue
            elif element == '3':
                while True:
                    try:
                        new_name = input("New trainer name (leave blank to apply your name as OT name): ")
                        if new_name == '':
                            misc.log(self.trainer_info['name'], 'd')
                            encoded = df.char_conversion(self.trainer_info['name'],
                                                         encode=True,
                                                         pad=df.generate_pad(15, len(self.trainer_info['name'])))
                            misc.log(df.bytearr_to_hexstring(encoded), 'd')
                            df.write_to_offset(self.pokemon, (0x68, 0x77), encoded)
                        else:
                            if len(new_name) < 0 or len(new_name) > 7:
                                raise ValueError
                            encoded = df.char_conversion(new_name, encode=True, pad=df.generate_pad(15, len(new_name)))
                            df.write_to_offset(self.pokemon, (0x68,0x77), encoded)
                        break
                    except Exception as e:
                        misc.log(e, 'e')
                        print("OT name must be greater than 0 and less than 7 characters in length.")
                        continue
            else:
                break
    def edit_battle(self):
        # SUBMENU SUBMENUS (have I gone too deep here?)
        def battle_info_subeditor():
            while True:
                self.update()
                misc.clear()
                print('\n'.join(self.display('stats')[1][0:5]))
                print(misc.get_padded("Edit"))
                battle_opts = {
                    '1': 'Level',
                    '2': 'Ability',
                    '3': 'Current HP'
                }
                for i in battle_opts:
                    print(f"[{i}]: {battle_opts[i]}")
                print("['back' to return to previous menu.]")
                battle_input = input("Edit which: ")
                if battle_input == 'back':
                    break
                elif battle_input.lower() in ['1', 'level', 'l', 'lvl']:
                    while True:
                        try:
                            new_lvl = int(input("Enter new level: "))
                            if new_lvl < 0 or new_lvl > 100:
                                raise ValueError
                            df.write_to_offset(self.pokemon, 0x8C, new_lvl)
                            new_xp = self.xp_min(self.general_info['species_id'], new_lvl)
                            to_bytes = df.byte_conversion(new_xp, 'I', encode=True)
                            df.write_to_offset(self.pokemon, (0x10,0x13), to_bytes)
                            break
                        except Exception as e:
                            misc.log(e, 'e')
                            print("Value must be between 0 and 100.")
                            continue
                elif battle_input.lower() in ['2', 'ability', 'a']:
                    while True:
                        try:

                            species_name = df.get_index(indexes.pkmn, self.general_info['species_id'])
                            ability_entry = df.get_index(indexes.valid_abilities, species_name)
                            print(f"Available abilities: {', '.join(ability_entry['abilities'])}")
                            print(f"Hidden ability: {ability_entry['hidden']}")
                            while True:
                                new_ability = input("Enter the name of the ability (or HA for hidden ability): ")
                                if new_ability.lower() == 'ha' and ability_entry['hidden'] != 'None':
                                    new_ability = ability_entry['hidden']
                                    break
                                elif new_ability.lower() in [a.lower() for a in ability_entry['abilities']]:
                                    break
                                else:
                                    print("Invalid selection.")
                                    continue
                            new_ability_id = 0
                            for x in indexes.abilities.values():
                                if x[0].lower() == new_ability.lower():
                                    new_ability_id = df.get_index(indexes.abilities, x, from_val=True)
                            if new_ability_id == 0:
                                raise ValueError
                            df.write_to_offset(self.pokemon, 0x15, new_ability_id)
                            break
                        except Exception as e:
                            misc.log(e, 'e')
                            print("No such ability found.")
                            print("Check bulbapedia or indexes.py for a list of abilities.")
                            continue
                elif battle_input.lower() in ['3', 'current hp', 'hp', 'c']:
                    while True:
                        try:
                            new_hp = int(input(f"Enter new HP value (less than {self.battle['max_hp']}): "))
                            if new_hp < 0 or new_hp > self.battle['max_hp']:
                                raise ValueError
                            df.write_to_offset(self.pokemon, (0x8E,0x8F), df.byte_conversion(new_hp, 'B', encode=True))
                            break
                        except Exception as e:
                            misc.log(e, 'e')
                            print(f"Value must be greater or equal to than 0 and less than {self.battle['max_hp']}")
                            continue
                continue
        def stats_subeditor():
            while True:
                self.update()
                misc.clear()
                print('\n'.join(self.display('stats')[1][5:12]))
                print(misc.get_padded("Edit"))
                stats_opts = {
                    '1':'Max HP',
                    '2':'Attack',
                    '3':'Defense',
                    '4':'Speed',
                    '5':'Special Attack',
                    '6':'Special Defense'
                }
                for i in stats_opts:
                    print(f"[{i}]: {stats_opts[i]}")
                print("['back' to return to previous menu.]")
                stats_input = input("Edit which: ")
                if stats_input == 'back':
                    break
                elif stats_input.lower() in ['1', 'max hp', 'm', 'hp']:
                    pass
                elif stats_input.lower() in ['2', 'attack', 'a', 'atk']:
                    pass
                elif stats_input.lower() in ['3', 'defense', 'd', 'def']:
                    pass
                elif stats_input.lower() in ['4', 'speed', 's']:
                    pass
                elif stats_input.lower() in ['5', 'special attack', 'sp atk']:
                    pass
                elif stats_input.lower() in ['6', 'special defense', 'sp def']:
                    pass
                continue
        def moves_subeditor():
            while True:
                self.update()
                misc.clear()
                print('\n'.join(self.display('stats')[1][12:len(self.display('stats')[1])]))
                print("['back' to return to previous menu.]")
                print(misc.get_padded("Edit"))
                try:
                    moves_input = input("Edit which (enter index): ")
                except Exception as e:
                    misc.log(e, 'e')
                    print("Must be int between 1 and 4.")
                    continue
                if moves_input == 'back':
                    break
                elif 4 <= int(moves_input) - 1 < 0:
                    print("Invalid index.")
                    continue
                else:
                    while True:
                        misc.clear()
                        position = int(moves_input) - 1
                        move = self.battle['moveset'][position]
                        print(misc.get_padded("Individual Move Editor"))
                        print(f"Name: {move['name']}")
                        print(f"Category: {move['category']}")
                        print(f"Type: {move['type']}")
                        print(f"{move['pp'][0]}pp/{move['pp'][1]}pp ({move['power']} power with {move['accuracy']} accuracy)")
                        print(misc.get_padded("Edit"))
                        print(f"[1]: Change Move\n[2]: Change PP")
                        move_edit = input("Edit which: ")
                        if move_edit == '1':
                            movelist = [x for x in self.pokemon[0x28:0x30]]
                            print(movelist)
                            while True:
                                new_move = input("Enter the name of the move to swap: ").title()
                                new_move_id = None
                                for d in indexes.moves.keys():
                                    if indexes.moves[d]['name'] == new_move:
                                        new_move_id = d
                                if new_move_id:
                                    break
                                print("Invalid move entered.")
                                continue
                            wrapped_id = (new_move_id-256, 1) if new_move_id >= 256 else (new_move_id, 0)
                            movelist = [x for x in self.pokemon[0x28:0x2F]]
                            movelist[position*2] = wrapped_id[0]
                            movelist[(position*2)+1] = wrapped_id[1]
                            df.write_to_offset(self.pokemon, (0x28,0x2F), bytearray(movelist))
                        elif move_edit == '2':
                            print(f"Current PP: {move['pp'][0]} out of maximum {move['pp'][1]}")
                            while True:
                                new_pp = int(input("Amount to set current PP to: "))
                                if 256 <= new_pp < 0:
                                    print("Must be integer above or equal to 0 and below or equal to 256.")
                                    continue
                                if new_pp > move['pp'][1]:
                                    print("Warning: Amount exceeds legal limit for this move")
                                    cont = input("Proceed: [y]/[n]: ")
                                    if cont.lower() not in ['y', 'yes']:
                                        continue
                                break
                            pp = [x for x in self.pokemon[0x30:0x34]]
                            pp[position] = new_pp
                            df.write_to_offset(self.pokemon, (0x30, 0x34), bytearray(pp))
                        else:
                            continue
                        break
        while True:
            self.update()
            misc.clear()
            print(self.display('stats')[0])
            opts = {
                '1': 'Battle Info',
                '2': 'Stats',
                '3': 'Moves',
            }
            print(''.join(['-' for _ in range(56)]))
            for x in opts.keys():
                print(f"[{x}]: {opts[x]}")
            print("['back' to return to previous menu.]")
            edit_choice = input("Edit which: ")
            if edit_choice.lower() in ['1', 'battle info', 'battle', 'info']:
                battle_info_subeditor()
            elif edit_choice.lower() in ['2', 'stats']:
                stats_subeditor()
            elif edit_choice.lower() in ['3', 'moves']:
                moves_subeditor()
            elif edit_choice.lower() == 'back':
                break
class party:
    def __init__(self, party_block, saveobj, trainer_info):
        self.saveobj = saveobj
        self.trainer_info = trainer_info
        self.whole = party_block
        self.in_party = self.whole[0x9C]
        self.contents = self.load_party()
    def load_party(self):
        blocks = [self.whole[0:236], self.whole[236:472], self.whole[472:708],
                  self.whole[708:944], self.whole[944:1180], self.whole[1180:1416]]
        return {index+1:pokemon(data, self.trainer_info, index+1) for index,data in enumerate(blocks)}
    def save_party(self):
        blocks = [pkmn.save() for pkmn in self.contents.values()]
        combined = df.combine_bytestrings(blocks)
        self.whole = combined
        self.contents = self.load_party()
        self.saveobj.update_offset((0xA0, 0x628), combined)
    def edit(self):
        while True:
            misc.clear()
            print(misc.get_padded("Party Edit"))
            for x in self.contents.keys():
                print(f"Slot #{x}: {self.contents[x].general_info['name']}")
            print(f"['back' to return to main menu.]")
            try:
                print(misc.get_padded("Command Input"))
                select = input("Enter index corresponding to pokemon to modify: ")
                if select.lower() == 'back':
                    self.save_party()
                    break
                else:
                    self.contents[int(select)].edit()
                    self.save_party()
                    continue
            except Exception as e:
                misc.log(e, 'e')
                sleep(0.5)
                print("Invalid Index/Command.")
                continue
class trainer:
    def __init__(self, datablock, saveobj):
        self.saveobj = saveobj
        self.whole = datablock
        self.offsets = {
            "trainer_name": (0x68,0x77),
            "trainer_gender": 0x80,
            "trainer_id": (0x78, 0x7a),
            "secret_id": (0x7a, 0x7c),
            "money": (0x7C, 0x7F),
            "badges": 0x82,
        }
        self.trainer_info = self.get_trainer_info()
        self.trainer_party = party(self.whole[0xA0:0x628], self.saveobj, self.trainer_info)
    # EDIT
    def update(self):
        self.trainer_info = self.get_trainer_info()
        self.trainer_party = party(self.whole[0xA0:0x628], self.saveobj, self.trainer_info)
    def edit(self):
        while True:
            self.update()
            misc.clear()
            print(misc.get_padded("Trainer Edit"))
            opts = {
                '1':"trainer_name",
                '2':"trainer_gender",
                '3':"trainer_id",
                '4':"secret_id",
                '5':"money",
                '6':"badges",
            }
            for x in opts.keys():
                print(f"[{x}]: {opts[x]}")
            print("['back' to return to main menu.]")
            while True:
                ele_input = input("Select index corresponding to element to modify: ")
                if ele_input in opts.keys():
                    element = opts[ele_input]
                    break
                elif ele_input == 'back':
                    element = 'back'
                    break
                else:
                    sleep(0.5)
                    print("Invalid index.")
                    continue
            if element == "money":
                while True:
                    try:
                        new_amt = int(input("New money amount: "))
                        if 0 <= new_amt <= 999999:
                            encoded = df.byte_conversion(new_amt, '<I', encode=True)[:-1]
                            self.saveobj.update_offset(self.offsets['money'], bytearray(encoded))
                            break
                        else:
                            raise ValueError
                    except Exception as e:
                        print("New amount must be an integer between 0 and 999,999.")
                        misc.log(e, 'error')
                        continue
            if element == "trainer_name":
                while True:
                    try:
                        new_name = input("New trainer name: ")
                        encoded = df.char_conversion(data=new_name,
                                                     encode=True,
                                                     pad=df.generate_pad(15, len(new_name)))
                        self.saveobj.update_offset(self.offsets['trainer_name'], bytearray(encoded))
                        break
                    except Exception as e:
                        misc.log(e, 'e')
                        print("Character name must be greater than 0 and less than 7 characters in length.")
                        continue
            if element == "trainer_gender":
                while True:
                    new_gender = input("New gender (Male/Female): ")
                    if new_gender.lower() in ['m', 'male']:
                        self.saveobj.update_offset(self.offsets['trainer_gender'], 0)
                    elif new_gender.lower() in ['f', 'female']:
                        self.saveobj.update_offset(self.offsets['trainer_gender'], 1)
                    else:
                        print("Enter M, Male, F, or Female.")
                        continue
                    break
            if element in ['trainer_id', 'secret_id']:
                while True:
                    try:
                        new_id = int(input(f"New {element.split('_')[0]} ID: "))
                        if 0 < new_id <= 99999:
                            encoded = df.byte_conversion(new_id, '<H', encode=True)
                            if element == 'trainer_id':
                                self.saveobj.update_offset(self.offsets['trainer_id'], bytearray(encoded))
                            else:
                                self.saveobj.update_offset(self.offsets['secret_id'], bytearray(encoded))
                            break
                        else:
                            raise ValueError
                    except Exception as e:
                        print("New ID must be an integer between 0 and 99999.")
                        misc.log(e, 'error')
                        continue
            if element == 'badges':
                while True:
                    for x,y in enumerate(list(indexes.badge_dict.values())):
                        print(f"[{x}]: {y}")
                    try:
                        selected = input("Enter the index corresponding with the badges you want, "
                                         "separated by a comma ('none' for zero badges): ")
                        if 'none' in selected:
                            badge_value = 0
                        else:
                            selected = [int(x) for x in selected.split(',')]
                            badge_value = sum([list(indexes.badge_dict.keys())[x] for x in selected])
                        self.saveobj.update_offset(self.offsets['badges'], badge_value)
                        break
                    except Exception:
                        print("Enter valid indexes.")
                        continue
            if ele_input == 'back':
                break
            else:
                continue
    # READ FUNCTIONS
    def get_badge_info(self):
        value = self.whole[0x82]
        badge_counts = {y:x+1 for x, y in enumerate([sum(list(indexes.badge_dict.keys())[:-x]) if x != 0 else sum(list(indexes.badge_dict.keys())) for x in reversed(range(8))])}
        if value in indexes.badge_dict.keys():
            badgelist = [f"{indexes.badge_dict[value]} Badge"]
        elif value in badge_counts.keys():
            badgelist = [f"{list(indexes.badge_dict.values())[x]} Badge" for x in range(badge_counts[value])]
        else:
            combos = list(itertools.chain.from_iterable(itertools.combinations(list(indexes.badge_dict.keys()), r) for r in range(len(list(indexes.badge_dict.keys()))+1)))[1:]
            combolist = {sum(list(sublist)):list(sublist) for sublist in combos}
            badgelist = [f"{indexes.badge_dict[x]} Badge" for x in combolist[value]]
        if system().lower() == "windows":
            return badgelist
        else:
            return [f"{indexes.badge_to_color[x]}{x}\033[1;m" for x in badgelist]
    def get_trainer_info(self):
        # General
        trainer_name = df.char_conversion(df.read_from_offset(self.whole, self.offsets["trainer_name"]))
        trainer_gender = "Male" if df.read_from_offset(self.whole, self.offsets['trainer_gender']) == 0 else "Female"
        trainer_id = int.from_bytes(df.read_from_offset(self.whole, self.offsets['trainer_id']), "little")
        secret_id = int.from_bytes(df.read_from_offset(self.whole, self.offsets['secret_id']), "little")
        trainer_badges = self.get_badge_info()
        money = int.from_bytes(df.read_from_offset(self.whole, self.offsets['money']), "little")
        # Progress
        bar = '/'.join(["*" for _ in range(len(self.get_badge_info()))] + ["-" for _ in range(8 - len(self.get_badge_info()))])
        gym_progress = (f"[{bar}]", f"{bar.count('*')}/8 Gyms Beaten!")
        #
        # party:
        #
        trainer_data = {
            "name":trainer_name,
            "gender":trainer_gender,
            "tid":trainer_id,
            "sid":secret_id,
            "badges":trainer_badges,
            "money":money,
            "gym_progress":gym_progress,
        }
        return trainer_data
    # DISPLAY FUNCTIONS
    def display_trainer_info(self):
        info_lines = [
            misc.get_padded(f"Trainer: {misc.cstring(self.trainer_info['name'], color='blu')}/{misc.cstring(self.trainer_info['gender'], color='blu')}"),
            f"Trainer ID:{''.join([' ' for _ in range(14 - len('Trainer ID:'))])}{misc.cstring(self.trainer_info['tid'], color='blu')}",
            f"Secret ID:{''.join([' ' for _ in range(14 - len('Secret ID:'))])}{misc.cstring(self.trainer_info['sid'], color='blu')}",
            f"Money:{''.join([' ' for _ in range(14 - len('Money:'))])}{misc.cstring('$' + str(self.trainer_info['money']), color='blu')}\n",
            ]
        # TODO: Awful, fix this
        badges = []
        for index,chunk in enumerate(df.list_to_chunks(self.trainer_info['badges'], 2)):
            if index == 0:
                if len(chunk) < 2:
                    row = f"{misc.cstring(self.trainer_info['name'], color='blu')} has: {chunk[0]}"
                else:
                    if '\033' in chunk[0]:
                        row = f"{misc.cstring(self.trainer_info['name'], color='blu')} has: {chunk[0]}      {chunk[1]}"
                    else:
                        row = f"{misc.cstring(self.trainer_info['name'], color='blu')} has: {chunk[0]}        {chunk[1]}"
                badges.append(row)
            else:
                if len(chunk) < 2:
                    row = f"{chunk[0]}"
                else:
                    stripped_first_chunk = misc.stripcolor(chunk[0])
                    row = f"{chunk[0]}{''.join([' ' for x in range(8-(len(f'{stripped_first_chunk}')-10))])}{chunk[1]}"
                offset = len(f"{self.trainer_info['name']} has:")
                badges.append(f"{''.join([' ' for _ in range(offset)])} {row}")
        game_progress = [
            f"{misc.get_padded('Game Progress')}\n",
            '\n'.join(badges),
            '\n\n',
            f"{misc.cstring(self.trainer_info['gym_progress'][0], color='blu')} => {misc.cstring(self.trainer_info['gym_progress'][1], color='blu')}",
            ]

        display = "\n".join(info_lines) + ''.join(game_progress)
        return display
    def display_party_info(self):
        party_lines = [
            misc.get_padded('Party')
        ]
        for slot in self.trainer_party.contents.keys():
            if self.trainer_party.contents[slot].general_info['name'] == 'Empty':
                info = ''
            else:
                info = f"({self.trainer_party.contents[slot].general_info['gender']} {self.trainer_party.contents[slot].general_info['species']})"
            party_lines.append(f"[{slot}]: {self.trainer_party.contents[slot].general_info['name']} {info}")
        return "\n".join(party_lines)
class save:
    def __init__(self, savedata, filepath):
        """
        :param savedata: the file object of the sav file
        :param filepath: the path to the sav file, used for saving changes
        """
        self.allblocks = bytearray(savedata)
        self.path = filepath
        try:
            self.player = trainer(self.allblocks, self)
        except Exception as e:
            misc.log(e, 'c', "Error creating trainer object!")
    def validate_crc_checksums(self):
        """
        The blocks have a 0x14 footer that contains the save number (0x04:0x07), the block size (0x08:0x0B), and most
        importantly the 2 byte checksum (0x12:0x13) used to validate the block data.

        The checksum is calculated with a CRC-16-CCITT (17 bit) cyclic redundancy check algorithm.
                        https://en.wikipedia.org/wiki/Cyclic_redundancy_check
        --------------------------------------------------------------------------------------------------
        Here is a basic explanation of how CRCs are computed.
        To compute an n-bit binary CRC, line the bits representing the input in a row,
        and position the (n + 1)-bit pattern representing the CRC's divisor (called a "polynomial")
        underneath the left-hand end of the row... The polynomial is written in binary as the coefficients
        --------------------------------------------------------------------------------------------------

        This function takes no input, as the function calculates every blocks checksum and modifies the block in the
        self.allblocks bytearray using self.update_offset()
        """
        block_offsets = [(0x00000,0x0CF2C), (0x00000 + 0x40000,0x0CF2C + 0x40000),
                         (0x0CF2C,0x1f110), (0x0CF2C + 0x40000,0x1f110 + 0x40000)]
        for block_offset in block_offsets:
            block = self.allblocks[block_offset[0]:block_offset[1]]
            # The current checksum of the block is gotten by reading the last two bytes. This value may be incorrect.
            current_checksum = df.byte_conversion(block[-0x14:][-2:], 'H')[0]
            high_order, low_order = 0xFF, 0xFF
            # checksums are calculated from a whole block without taking the footer (last 0x14 bytes)
            for i in range(0, len(block)-0x14):
                current_byte = block[i] ^ high_order
                current_byte ^= (current_byte >> 4)
                # The bitwise AND here is really important, as leaving it out will cause extremely large integer results
                high_order = (low_order ^ (current_byte >> 3) ^ (current_byte << 4)) & 255
                low_order = (current_byte ^ (current_byte << 5)) & 255
            correct_checksum = high_order << 8 | low_order
            misc.log(f"{hex(block_offset[0]), hex(block_offset[1])}: {current_checksum} -> {correct_checksum}", 'd')
            if current_checksum != correct_checksum:
                corrected_block = block[:-2] + df.byte_conversion(correct_checksum, 'H', encode=True)
                self.update_offset(block_offset, corrected_block)
    def update_offset(self, offset, value):
        """
        :param offset: a tuple containing the (start, end) values off the offset
        :param value: bytearray or byte to write to the offset
        :return: None, modified in place

        This is really just a way to neatly update the save data without calling the write_to_offset data function in
        a bunch of places. View write_to_offset in data_functions.py, lines 307-324, for more info.
        """
        self.allblocks = df.write_to_offset(self.allblocks, offset, value)
    def save(self):
        while True:
            try:
                savecheck = int(input("[1]: Save to original file\n[2]: Save to new file\n>>> "))
                if savecheck not in [1, 2]:
                    raise ValueError
                break
            except Exception:
                misc.log("Invalid save option entered.", 'i')
                print("Enter either 1 or 2.")
                continue
        self.validate_crc_checksums()
        if savecheck == 1:
            with open(self.path, 'wb') as f:
                f.write(self.allblocks)
        else:
            fp = input("Enter filepath to save to: ")
            with open(fp, 'wb') as f:
                f.write(self.allblocks)