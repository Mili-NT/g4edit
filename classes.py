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
        print(f"{self.save.player.display_trainer_info()}\n{self.save.player.display_party_info()}")
        self.command()
    def command(self):
        # TODO: Something needs to be done here. Way too tangled with ifs/elifs/elses
        while True:
            cmd = input("Command (h for opts): ")
            if cmd == 'edit':
                while True:
                    editchoice = input("Edit which: [t]rainer or [p]arty: ")
                    if editchoice.lower() in ['t', 'trainer', '1']:
                        self.save.player.edit()
                    elif editchoice.lower() in ['p', 'party', 'pkmn', '2']:
                        self.save.player.trainer_party.edit()
                    else:
                        continue
                    break
            elif cmd in ['edit trainer', 'edit t']:
                try:
                    self.save.player.edit()
                except Exception as e:
                    misc.log(e, 'e')
            elif cmd in ['edit party', 'edit p', '1', '2', '3', '4', '5', '6']:
                try:
                    self.save.player.trainer_party.edit()
                except Exception as e:
                    misc.log(e, 'e')
            elif cmd == 'save':
                self.save.save()
                self.refresh()
            elif cmd == 'exit':
                print("Warning! Unsaved modifications will disappear!")
                if input("Save? [y/n]: ").lower() in ['y', 'yes']:
                    self.save.save()
                exit()
            else:
                print("Enter 'edit' to access the editor prompt")
                print("Enter 'edit t' or 'edit p' to directly edit trainer and party.")
                print("Enter 'exit' to exit and save or 'save' to save directly.")
                continue
            self.refresh()
    def refresh(self):
        misc.clear()
        print(self.header)
        print(f"{self.save.player.display_trainer_info()}\n{self.save.player.display_party_info()}")
class pokemon:
    def __init__(self, data_block, slotnumber=0):
        self.decrypted = df.pokemon_conversion(data_block)
        self.pokemon = self.decrypted[0]
        self.pid = self.decrypted[1]
        self.checksum = self.decrypted[2]
        self.slotnumber = slotnumber
        # General
        # genderless = 4, Female = 2, Male = 0,
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
    def format_moves(self):
        tupled = [tuple(x) for x in df.list_to_chunks([x for x in self.pokemon[0x28:0x30]], 2)]
        moves = [df.get_index(indexes.moves, x[0]+256) if x[1] == 1 else df.get_index(indexes.moves, x[0]) for x in tupled]
        pp = [x for x in self.pokemon[0x30:0x34]]
        misc.log(f"{moves}", 'd')
        for x in range(len(pp)):
            if isinstance(moves[x]['pp'], tuple) is False:
                moves[x]['pp'] = (pp[x], moves[x]['pp'])
            else:
                moves[x]['pp'] = (pp[x], moves[x]['pp'][1])
        return moves
    def set_new_pv(self, gender=None, nature=None, maintain_block_order=True, shiny=False):
        """
        :param gender: 'm' for male, 'f' for female
        :param nature: string of nature to change to, i.e: 'hardy', 'adamant', 'lonely'
        :param maintain_block_order: Discards PVs that results in a different Shift Value (SV) than the original
        :param shiny: True to generate a shiny PV, else False
        :return: New PV matching specifications passed as params
        """
        gender_ratio = self.general_info['ratio']
        nature = nature if nature else self.pid % 25
        while True:
            new_pv = random.getrandbits(32) & 0xffffffff
            while len(f'{new_pv}') != 10:
                new_pv = int(f'{new_pv}{random.randint(0, 9)}')
            if gender_ratio in [0, 254, 255] and new_pv % 256 != gender_ratio:
                continue
            elif (gender == 0 and new_pv % 256 < gender_ratio) or (gender == 1 and new_pv % 256 >= gender_ratio):
                continue
            if new_pv % 25 != nature:
                continue
            if shiny and self.check_shiny(new_pv) is False:
                continue
            if maintain_block_order and ((self.pid & 0x3E000) >> 0xD) % 24 != ((new_pv & 0x3E000) >> 0xD) % 24:
                continue
            print(f"New PV: {new_pv}")
            ng = "Genderless" if gender_ratio == 255 else ('Male' if new_pv % 256 >= gender_ratio else 'Female')
            print(f"Gender: {ng}\nNature: {df.get_index(indexes.natures, new_pv % 25)}\nShiny: {self.check_shiny(new_pv)}")
            cont = input("Does this look correct? [y]/[n]: ")
            if cont.lower() in ['y', 'yes']:
                if ng == 'Genderless':
                    self.update(0x40, 4)
                elif ng == 'Female':
                    self.update(0x40, 2)
                elif ng == 'Male':
                    self.update(0x40, 0)
                self.pid = new_pv
                break
            else:
                continue
    def check_shiny(self, pv):
        tid = self.ot_info['tid']
        sid = self.ot_info['sid']
        p1 = int(pv / 65536)
        p2 = pv % 65536
        isShiny = tid ^ sid ^ p1 ^ p2
        return True if isShiny < 8 else False
    # UPDATE/ADD
    def update(self, offset, value):
        if isinstance(offset, int):
            self.pokemon[offset] = value
        else:
            count = 0
            for i in range(offset[0], offset[1]):
                self.pokemon[i] = value[count]
                count += 1
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
    # DISPLAYS
    def display(self, item):
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
                f"Experience: {self.battle['xp']}",
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
            misc.log(f"{self.battle['moveset']}", 'd')
            for index,item in enumerate(self.battle['moveset']):
                lines.append(f"[{index+1}]: {item['name']} ({item['pp'][0]}pp/{item['pp'][1]}pp)")
            return '\n'.join(lines), lines
        return '\n'.join(lines)
    def display_pkmn(self):
        misc.clear()
        print(misc.get_padded(f"Slot Number {self.slotnumber}"))
        print(f"PV: {self.pid}")
        print(self.display('general'))
        print(self.display('ot'))
        print(self.display('stats')[0])
    # EDITS
    def edit(self):
        while True:
            misc.clear()
            print(misc.get_padded(f"Edit Menu For Slot {self.slotnumber}"))
            self.display_pkmn()
            print(misc.get_padded("Edit"))
            print("[1]. General Info (Species, Name, Etc.)\n[2]. OT Info (OT name, ID, SID)\n[3]. Battle Stats\n"
                  "['back' to return to previous menu.]")
            editchoice = input("Edit which: ")
            if editchoice.lower() in ['g', 'gen', 'general', 'general info', '1']:
                self.edit_gen()
            elif editchoice.lower() in ['ot', 'trainer', 'ot info', 't', 'trainer info', '2']:
                self.edit_ot()
            elif editchoice.lower() in ['battle', 'b', 'battle info', 'stats', 's', 'stats info', 'battle stats', '3']:
                self.edit_stats()
            elif editchoice.lower() == 'back':
                  break
            else:
                sleep(0.5)
                print("Invalid Option.")
            continue
    # EDIT SUBMENUS
    def edit_gen(self):
        while True:
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
                    new_species = input("Enter the name of the new species: ").lower()
                    if df.is_valid(indexes.pkmn, new_species, 'value'):
                        self.update((0x08,0x0A), df.get_index(indexes.pkmn, new_species, from_val=True))
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
                    self.update((0x48, 0x5D), encoded)
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
                    if df.is_valid(indexes.natures, new_nature, pos='val'):
                        self.set_new_pv(nature=df.get_index(indexes.natures, new_nature, from_val=True))
                        break
                    else:
                        print("No such nature found.")
                        print("Check https://bulbapedia.bulbagarden.net/wiki/Nature or indexes.py for valid natures.")
                        continue
            elif element in ['5', 'item']:
                while True:
                    new_item = input("Enter the name of the item: ")
                    if df.is_valid(indexes.items, new_item, pos='val'):
                        itemid = df.get_index(indexes.items, new_item, from_val=True)
                        self.update(0x83, itemid)
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
                        self.update(0x83, new_ball_id)
                        break
                    else:
                        continue
            elif element in ['7', 'pokerus']:
                while True:
                    new_pkrus = input("Enable pokerus: [y]/[n]: ")
                    if new_pkrus.lower() in ['y', 'yes']:
                        self.update(0x82, 1)
                    elif new_pkrus.lower() in ['n', 'no']:
                        self.update(0x82, 1)
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
                    self.update((0x46,0x48), encoded)
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
                        new_id = int(input(f"Enter new {id_type} ID: "))
                        if 0 < new_id <= 65535:
                            encoded = df.byte_conversion(new_id, 'H', encode=True)
                            if id_type == 'trainer':
                                self.update((0x0C,0x0E), encoded)
                            else:
                                self.update((0x0E,0x10), encoded)
                            break
                        else:
                            raise ValueError
                    except Exception as e:
                        misc.log(e, 'error')
                        print(f"New {'trainer' if element == '1' else 'secret'} ID must be greater than 0 and less than 65535.")
                        continue
            elif element == '3':
                pass
            else:
                break
            continue
    # TODO: FINISH STATS SUBEDITOR
    def edit_stats(self):
        def battle_info_subeditor():
            while True:
                misc.clear()
                print('\n'.join(self.display('stats')[1][0:5]))
                print(misc.get_padded("Edit"))
                battle_opts = {
                    '1': 'Level',
                    '2': 'Experience',
                    '3': 'Ability',
                    '4': 'Current HP'
                }
                for i in battle_opts:
                    print(f"[{i}]: {battle_opts[i]}")
                print("['back' to return to previous menu.]")
                battle_input = input("Edit which: ")
                if battle_input == 'back':
                    break
                elif battle_input.lower() in ['1', 'level', 'l', 'lvl']:
                    pass
                elif battle_input.lower() in ['2', 'experience', 'e', 'xp']:
                    pass
                elif battle_input.lower() in ['3', 'ability', 'a']:
                    pass
                elif battle_input.lower() in ['4', 'current hp', 'hp', 'c']:
                    pass
                continue
        def stats_subeditor():
            while True:
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
                            self.update((0x28,0x2F), bytearray(movelist))
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
                            self.update((0x30, 0x34), bytearray(pp))
                        else:
                            continue
                        break
        while True:
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
            elif edit_choice.lower() in ['3', 'stats']:
                moves_subeditor()
            elif edit_choice.lower() == 'back':
                break

class party:
    def __init__(self, party_block):
        self.whole = party_block
        self.in_party = self.whole[0x9C]
        self.contents = self.load_party()
    def load_party(self):
        blocks = [self.whole[0:236], self.whole[236:472], self.whole[472:708],
                  self.whole[708:944], self.whole[944:1180], self.whole[1180:1416]]
        return {index+1:pokemon(data, index+1) for index,data in enumerate(blocks)}
    def edit(self):
        while True:
            misc.clear()
            print(misc.get_padded("Party Edit"))
            for x in self.contents.keys():
                print(f"[{x}]: {self.contents[x].general_info['name']}")
            try:
                select = input("Enter index corresponding to pokemon to modify (or back to return to main menu): ")
                if select.lower() == 'back':
                    break
                else:
                    # TODO: IMPLEMENT
                    self.contents[int(select)].edit()
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
        self.trainer_party = party(self.whole[0xA0:0x628])
    # EDIT
    def edit(self):
        while True:
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
                    new_name = input("New trainer name: ")
                    if len(new_name) == 7:
                        encoded = df.char_conversion(data=new_name, encode=True, pad=[255])
                    elif 0 < len(new_name) < 7:
                        encoded = df.char_conversion(data=new_name, encode=True, pad=[255, 255] + [0 for _ in range((15-len(new_name*2))-2)])
                    else:
                        print("Character name must be greater than 0 and less than 7 characters in length.")
                        misc.log("Incorrect character name entered.", 'i')
                        continue
                    self.saveobj.update_offset(self.offsets['trainer_name'], bytearray(encoded))
                    break
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
            self.trainer_info = self.get_trainer_info()
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

        display = "\n".join(info_lines) + ''.join(game_progress) + '\n' + ''.join(['-' for _ in range(56)])
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
        party_lines.append(''.join(['-' for _ in range(56)]))
        return "\n".join(party_lines)
class save:
    def __init__(self, savedata, filepath):
        self.allblocks = bytearray(savedata)
        self.path = filepath
        try:
            self.player = trainer(self.allblocks, self)
        except Exception as e:
            misc.log(e, 'c', "Error creating trainer object!")
    def update_offset(self, offset, value):
        if isinstance(offset, int):
            self.allblocks[offset] = value
        else:
            count = 0
            for i in range(offset[0], offset[1]):
                self.allblocks[i] = value[count]
                count += 1
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
        if savecheck == 1:
            with open(self.path, 'wb') as f:
                f.write(self.allblocks)
        else:
            fp = input("Enter filepath to save to: ")
            with open(fp, 'wb') as f:
                f.write(self.allblocks)