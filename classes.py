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
        print(self.header)
        print(self.general_info)
        pkmn = pokemon(self.save.smallblock[0xA0:0x628][0:236])
        print(pkmn.pokemon[0x48:0x5D])
        print(df.bytearr_to_hexstring(pkmn.pokemon[0x48:0x5D]))

class pokemon:
    def __init__(self, data_block):
        self.decrypted = df.pokemon_conversion(data_block)
        self.pokemon = self.decrypted[0]
        self.pid = self.decrypted[1]
        self.checksum = self.decrypted[2]
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
    def format_moves(self):
        moves = [indexes.moves_indexes[x] for x in [x for x in self.pokemon[0x28:0x2F]][::2]]
        pp = [x for x in self.pokemon[0x30:0x34]]
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

class trainer:
    def __init__(self, trainer_info):
        self.name = trainer_info["name"]
        self.gender = trainer_info["gender"]
        self.trainer_id = trainer_info["tid"]
        self.secret_id = trainer_info["sid"]
        self.badges = trainer_info["badges"]
        self.money = trainer_info["money"]
        self.gym_progress = trainer_info["gym_progress"]
        self.party = trainer_info['party']

    def display_trainer_info(self):
        def get_padded(string):
            uncolored = string
            for c in misc.colors.values():
                uncolored = uncolored.replace(c, "")
            diff = 56 - len(uncolored)
            perside = ''.join(['-' for _ in range(diff // 2)])
            pad = f"{perside}{uncolored}{perside}"
            while len(pad) < 56:
                pad = f"{pad}-"
            return pad.replace(uncolored, string)
        lines = {
            "first_header": get_padded(f"Trainer: {misc.cstring(self.name, color='blu')}/{misc.cstring(self.gender, color='blu')}"),
            "first_id": f"Trainer ID:{''.join([' ' for _ in range(14 - len('Trainer ID:'))])}{misc.cstring(self.trainer_id, color='blu')}",
            "second_id": f"Secret ID:{''.join([' ' for _ in range(14 - len('Secret ID:'))])}{misc.cstring(self.secret_id, color='blu')}",
            "money": f"Money:{''.join([' ' for _ in range(14 - len('Money:'))])}{misc.cstring('$' + str(self.money), color='blu')}",
            "second_header": f"{get_padded('Game Progress')}",
            "badge_lines": f"{misc.cstring(self.name, color='blu')} has {', '.join(self.badges)}\n",
            "prog_bar": f"{misc.cstring(self.gym_progress[0], color='blu')} => {misc.cstring(self.gym_progress[1], color='blu')}",
            'border': (''.join(['-' for _ in range(56)])) + '\n'}
        return "\n".join([lines[x] for x in list(lines.keys())])

class save:
    def __init__(self, savedata):
        self.allblocks = bytearray(savedata)
        self.smallblock = self.allblocks[0x00000:0x0CF2B]
        self.bigblock = self.allblocks[0x0CF2C:0x1F10F]
        self.smallblock_backup = self.allblocks[(0x00000 + 0x40000):(0x0CF2B + 0x40000)]
        self.bigblock_backup = self.allblocks[(0x0CF2C + 0x40000):(0x1F10F + 0x40000)]
        self.player = self.get_trainer_info()
    def update_value(self, offset, bytestr):
        self.allblocks[(offset[0]):(offset[1])] = bytestr
        self.player = self.get_trainer_info()
    def get_badge_info(self):
        value = self.smallblock[0x82]
        badge_dict = {
            1: "Coal",
            2: "Forest",
            4: "Cobble",
            8: "Fen",
            16: "Relic",
            32: "Mine",
            64: "Icicle",
            128: "Beacon",
        }
        badge_to_color = {
            "Coal Badge": "\033[1;30;40m",
            "Forest Badge": "\033[1;37;42m",
            "Cobble Badge": "\033[1;37;41m",
            "Fen Badge": "\033[1;37;44m",
            "Relic Badge": "\033[1;37;45m",
            "Mine Badge": "\033[2;33;40m",
            "Icicle Badge": "\033[1;37;46m",
            "Beacon Badge": "\033[1;37;43m",
        }
        badge_counts = {y:x+1 for x, y in enumerate([sum(list(badge_dict.keys())[:-x]) if x != 0 else sum(list(badge_dict.keys())) for x in reversed(range(8))])}
        if value in badge_dict.keys():
            badgelist = [f"{badge_dict[value]} Badge"]
        elif value in badge_counts.keys():
            badgelist = [f"{list(badge_dict.values())[x]} Badge" for x in range(badge_counts[value])]
        else:
            combos = list(itertools.chain.from_iterable(itertools.combinations(list(badge_dict.keys()), r) for r in range(len(list(badge_dict.keys()))+1)))[1:]
            combolist = {sum(list(sublist)):list(sublist) for sublist in combos}
            badgelist = [f"{badge_dict[x]} Badge" for x in combolist[value]]
        if system().lower() == "windows":
            return badgelist
        else:
            return [f"{badge_to_color[x]}{x}\033[1;m" for x in badgelist]
    def get_trainer_info(self):
        # General
        trainer_name = df.char_conversion(self.smallblock[0x68:0x77])
        trainer_gender = "male" if self.smallblock[0x80] == 0 else "female"
        trainer_id = int.from_bytes(self.smallblock[0x78:0x7a], "little")
        secret_id = int.from_bytes(self.smallblock[0x7a:0x7c], "little")
        trainer_badges = self.get_badge_info()
        money = int.from_bytes(self.smallblock[0x7C:0x7F], "little")
        # Progress
        bar = '/'.join(["*" for _ in range(len(self.get_badge_info()))] + ["-" for _ in range(8 - len(self.get_badge_info()))])
        gym_progress = (f"[{bar}]", f"{bar.count('*')}/8 Gyms Beaten!")
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
            'party':'trainer_party',
        }
        return trainer(trainer_data)