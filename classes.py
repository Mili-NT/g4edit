import os
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
        self.general_info = self.save.player.display_trainer_info()
        self.party_info = self.save.player.display_party_info()
        print(self.header)
        print(f"{self.general_info}\n{self.party_info}")
        self.command()
    def command(self):
        while True:
            valid_cmds = ['edit gen', 'edit pkmn', 'save', 'exit']
            cmd = input("Command (h for opts): ")
            if cmd not in valid_cmds:
                print("Enter 'edit gen' to edit trainer info and gym progress")
                print("Enter 'edit pkmn' to edit pokemon in party.")
                print("Enter 'save' to save modifications.")
                print("Enter 'exit' to exit.")
                continue
            if cmd == 'edit gen':
                self.save.player.edit()
                self.refresh()
            elif cmd == 'edit pkmn':
                self.save.player.trainer_party.edit()
                self.refresh()
            elif cmd == 'save':
                self.save.save()
            elif cmd == 'exit':
                print("Warning! Unsaved modifications will disappear!")
                cont = input("Save? [y/n]: ")
                if cont.lower() in ['y', 'yes']:
                    self.save.save()
                exit()
    def refresh(self):
        misc.clear()
        print(self.header)
        print(f"{self.general_info}\n{self.party_info}")
class pokemon:
    def __init__(self, data_block, slotnumber=0):
        self.decrypted = df.pokemon_conversion(data_block)
        self.pokemon = self.decrypted[0]
        self.pid = self.decrypted[1]
        self.checksum = self.decrypted[2]
        self.slotnumber = slotnumber
        # General
        self.general_info = {
            'species_id': df.byte_conversion(self.pokemon[0x08:0x0A], 'H')[0],
            'species': indexes.pkmn_indexes[df.byte_conversion(self.pokemon[0x08:0x0A], 'H')[0]],
            'name': df.char_conversion(self.pokemon[0x48:0x5D]),
            'gender':'Male' if self.pokemon[0x40] == 0 else 'Female',
            'nature': indexes.nature_indexes[self.pid % 25],
            'item': df.item_id_conversion(df.byte_conversion(self.pokemon[0x0A:0x0C], 'H')[0]),
            'pokeball': df.item_id_conversion(self.pokemon[0x83]),
            'pokerus': False if self.pokemon[0x82] == 0 else True,
            'plat_met_at': indexes.location_indexes[df.byte_conversion(self.pokemon[0x46:0x48], 'H')[0]],
        }
        # Trainer info
        self.ot_info = {'tid': df.byte_conversion(self.pokemon[0x0C:0x0E], 'H')[0],
                        'sid': df.byte_conversion(self.pokemon[0x0E:0x10], 'H')[0],
                        'ot_name':df.char_conversion(self.pokemon[0x68:0x77])}
        # Battle related stats
        self.battle = {
            'level':self.pokemon[0x8C],
            'xp': df.byte_conversion(bytearray(self.pokemon[0x10:0x13] + b'\x00'), 'I')[0],
            'ability':indexes.ability_indexes[self.pokemon[0x15]],
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
        moves = [indexes.moves_indexes[x] for x in [x for x in self.pokemon[0x28:0x2F]][::2]]
        pp = [x for x in self.pokemon[0x30:0x34]]
        if pp != [0, 0, 0, 0]:
            for x in range(len(pp)):
                moves[x]['pp'] = (moves[x]['pp'], pp[x])
                if moves[x]['pp'][1] > moves[x]['pp'][0]:
                    tup = moves[x]['pp']
                    moves[x]['pp'] = (tup[0], tup[0])
        return moves
    def set_new_pv(self, specid, gender=None, nature=None, shiny=False):
        gender_ratio = indexes.gender_ratios[specid]
        if nature:
            nature = list(indexes.nature_indexes.keys())[list(indexes.nature_indexes.values()).index(nature)]
        else:
            nature = self.pid % 25
        while True:
            new_pv = random.getrandbits(32) & 0xffffffff
            while len(f'{new_pv}') != 10:
                new_pv = int(f'{new_pv}{random.randint(0, 9)}')
            if gender_ratio in [0, 254, 255] and new_pv % 256 != gender_ratio:
                continue
            elif (gender == 1 and new_pv % 256 >= gender_ratio) or (gender == 0 and new_pv % 256 < gender_ratio):
                continue
            if new_pv % 25 != nature:
                continue
            if shiny and self.check_shiny(new_pv) is False:
                continue
            self.pid = new_pv
            break
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
            'species': indexes.pkmn_indexes[df.byte_conversion(self.pokemon[0x08:0x0A], 'H')[0]],
            'name': df.char_conversion(self.pokemon[0x48:0x5D]),
            'gender':'Male' if self.pokemon[0x40] == 0 else 'Female',
            'nature': indexes.nature_indexes[self.pid % 25],
            'item': df.item_id_conversion(df.byte_conversion(self.pokemon[0x0A:0x0C], 'H')[0]),
            'pokeball': df.item_id_conversion(self.pokemon[0x83]),
            'pokerus': False if self.pokemon[0x82] == 0 else True,
            'plat_met_at': indexes.location_indexes[df.byte_conversion(self.pokemon[0x46:0x48], 'H')[0]],
        }
        self.ot_info = {'tid': df.byte_conversion(self.pokemon[0x0C:0x0E], 'H')[0],
                        'sid': df.byte_conversion(self.pokemon[0x0E:0x10], 'H')[0],
                        'ot_name':df.char_conversion(self.pokemon[0x68:0x77])}
        self.battle = {
            'level':self.pokemon[0x8C],
            'xp': df.byte_conversion(bytearray(self.pokemon[0x10:0x13] + b'\x00'), 'I')[0],
            'ability':indexes.ability_indexes[self.pokemon[0x15]],
            'moveset': self.format_moves(),
            'current_hp':df.byte_conversion(self.pokemon[0x8E:0x8F], 'B')[0],
            'max_hp':df.byte_conversion(self.pokemon[0x90:0x91], 'B')[0],
            'attack': df.byte_conversion(self.pokemon[0x92:0x94], 'H')[0],
            'defense': df.byte_conversion(self.pokemon[0x94:0x95], 'B')[0],
            'speed': df.byte_conversion(self.pokemon[0x96:0x97], 'B')[0],
            'spec_attack': df.byte_conversion(self.pokemon[0x98:0x99], 'B')[0],
            'spec_defense': df.byte_conversion(self.pokemon[0x9A:0x9B], 'B')[0]
        }
    # DISPLAYS
    def display_general(self):
        lines = [
            misc.get_padded(f"General Info for Slot {self.slotnumber}"),
            f"Name: {self.general_info['name']}",
            f"Species: {self.general_info['species']}",
            f"Gender: {self.general_info['gender']}"
            f"Held Item: {self.general_info['item']}",
            f"Caught in: {self.general_info['pokeball']}"
            f"Pokerus: {self.general_info['pokerus']}"
            f"Met at {self.general_info['plat_met_at']}"
        ]
        return '\n'.join(lines)
    def display_ot(self):
        lines = [
            misc.get_padded(f"OT Info for Slot {self.slotnumber}"),
            f"Trainer ID: {self.ot_info['tid']}"
            f"Secret ID: {self.ot_info['tid']}"
            f"OT Name: {self.ot_info['ot_name']}"
        ]
        return '\n'.join(lines)
    def display_stats(self):
        lines = [
            misc.get_padded(f"Battle Info for Slot {self.slotnumber}"),
            f"Level: {self.battle['level']}",
            f"Experience: {self.battle['xp']}",
            f"Ability: {self.battle['ability']}",
            f"Current HP: {self.battle['current_hp']}",
            misc.get_padded("Stats: "),
            f"Max HP: {self.battle['max_hp']}",
            f"Attack: {self.battle['attack']}",
            f"Defense: {self.battle['defense']}",
            f"Speed: {self.battle['speed']}",
            f"Special Attack: {self.battle['spec_attack']}",
            f"Special Defense: {self.battle['spec_defense']}"
        ]
        return "\n".join(lines)
    # EDITS TODO: IMPLEMENT
    def edit_general(self):
        self.display_general()
    def edit_ot(self):
        self.display_ot()
    def edit_stats(self):
        self.display_stats()

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
            while True:
                try:
                    select = input("Enter index corresponding to pokemon to modify (or exit to exit): ")
                    if select.lower() == 'exit':
                        exit()
                    else:
                        # TODO: IMPLEMENT
                        pass
                except Exception:
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
        misc.clear()
        print(misc.get_padded("Trainer Edit"))
        opts = {
            1:"trainer_name",
            2:"trainer_gender",
            3:"trainer_id",
            4:"secret_id",
            5:"money",
            6:"badges",
        }
        for x in opts.keys():
            print(f"[{x}]: {opts[x]}")
        while True:
            ele_input = int(input("Select index corresponding to element to modify: "))
            if ele_input in opts.keys():
                element = opts[ele_input]
                break
            else:
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
                    selected = input("Enter the index corresponding with the badges you want, separated by a coma: ").replace(' ', '')
                    selected = [int(x) for x in selected.split(',')]
                    badge_value = sum([list(indexes.badge_dict.keys())[x] for x in selected])
                    self.saveobj.update_offset(self.offsets['badges'], badge_value)
                    break
                except Exception:
                    print("Enter valid indexes.")
                    continue
        self.trainer_info = self.get_trainer_info()
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
        trainer_gender = "male" if df.read_from_offset(self.whole, self.offsets['trainer_gender']) == 0 else "female"
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