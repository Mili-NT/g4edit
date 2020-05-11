import lib
import string
import itertools
from platform import system

class interface:
    def __init__(self, saveobj):
        self.save = saveobj
        self.header = lib.get_title()
        self.general_info = self.save.player.display_trainer_info()
        print(self.header)
        print(self.general_info)
        pokemon(self.save.smallblock[0xA0:0x628][0:236]).decrypt()

class pokemon:
    def __init__(self, data_block):
        # Chunks
        self.whole = bytearray(data_block)
        self.blocks = bytearray(data_block[0x08:0x88])
        # Header Components
        self.personality_value = data_block[0x00:0x04]
        self.unused = data_block[0x04:0x06]
        self.checksum = int.from_bytes(data_block[0x06:0x08], "little")

    def shuffle(self, chunk, order):
        shift_value = ((int.from_bytes(self.personality_value, "little") & 0x3E000) >> 0xD) % 24
        shift_value = f"0{shift_value}" if shift_value < 10 else str(shift_value)
        # Shifts stored with shift_value:(block order, inverse) format
        shifts = {
                '00':('ABCD','ABCD'),
                '01':('ABDC','ABDC'),
                '02':('ACBD','ACBD'),
                '03':('ACDB','ADBC'),
                '04':('ADBC','ACDB'),
                '05':('ADCB','ADCB'),
                '06':('BACD','BACD'),
                '07':('BADC','BADC'),
                '08':('BCAD','CABD'),
                '09':('BCDA','DABC'),
                '10':('BDAC','CADB'),
                '11':('BDCA','DACB'),
                '12':('CABD','BCAD'),
                '13':('CADB','BDAC'),
                '14':('CBAD','CBAD'),
                '15':('CBDA','DBAC'),
                '16':('CDAB','CDAB'),
                '17':('CDBA','DCAB'),
                '18':('DABC','BCDA'),
                '19':('DACB','BDCA'),
                '20':('DBAC','CBDA'),
                '21':('DBCA','DBCA'),
                '22':('DCAB','CDBA'),
                '23':('DCBA','DCBA'),
                }
        # A=0, B=1, C=2, D=3
        blocks = [bytearray(chunk[0:32]), bytearray(chunk[32:64]),
                  bytearray(chunk[64:96]), bytearray(chunk[96:128])]
        block_order = (shifts[shift_value][1] if order == "inverse" else shifts[shift_value][0]).lower()
        combined_blocks = []
        for index in [string.ascii_lowercase.index(x) for x in block_order]:
            combined_blocks.extend(blocks[index])
        return bytearray(combined_blocks)
    def decrypt(self):
        def rand(seed):
            return (0x41C64E6D * seed + 0x00006073) >> (len(bin(0x41C64E6D * seed + 0x00006073)[2:]) - 16)
        split = [self.blocks[i:i + 2] for i in range(0, len(self.blocks), 2) if len(self.blocks[i:i + 2]) > 1]
        decrypted_bytes = []
        currentseed = self.checksum
        for y in split:
            unencrypted_byte = lib.xor_bytes(y, bytes(rand(currentseed)))
            decrypted_bytes.append(unencrypted_byte)
            currentseed = rand(currentseed)

        blocks = bytearray()
        for x in decrypted_bytes:
            blocks += x
        print(blocks)
        pkmn = self.shuffle(blocks, "inverse")





class party:
    def __init__(self, party_block):
        self.in_party = party_block[0x9C]
        self.slot_one = pokemon(party_block[0:236])
        self.slot_two = pokemon(party_block[236:472])
        self.slot_three = pokemon(party_block[472:708])
        self.slot_four = pokemon(party_block[708:944])
        self.slot_five = pokemon(party_block[944:1180])
        self.slot_six = pokemon(party_block[1180:1416])
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
            for c in lib.colors.values():
                uncolored = uncolored.replace(c, "")
            diff = 56 - len(uncolored)
            perside = ''.join(['-' for _ in range(diff // 2)])
            pad = f"{perside}{uncolored}{perside}"
            while len(pad) < 56:
                pad = f"{pad}-"
            return pad.replace(uncolored, string)
        lines = {
            "first_header": get_padded(f"Trainer: {lib.cstring(self.name, color='blu')}/{lib.cstring(self.gender, color='blu')}"),
            "first_id": f"Trainer ID:{''.join([' ' for _ in range(14 - len('Trainer ID:'))])}{lib.cstring(self.trainer_id, color='blu')}",
            "second_id": f"Secret ID:{''.join([' ' for _ in range(14 - len('Secret ID:'))])}{lib.cstring(self.secret_id, color='blu')}",
            "money": f"Money:{''.join([' ' for _ in range(14 - len('Money:'))])}{lib.cstring('$' + str(self.money), color='blu')}",
            "second_header": f"{get_padded('Game Progress')}",
            "badge_lines": f"{lib.cstring(self.name, color='blu')} has {', '.join(self.badges)}\n",
            "prog_bar": f"{lib.cstring(self.gym_progress[0], color='blu')} => {lib.cstring(self.gym_progress[1], color='blu')}",
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
        trainer_name = lib.hex_to_string(self.smallblock[0x68:0x77])
        trainer_gender = "male" if self.smallblock[0x80] == 0 else "female"
        trainer_id = int.from_bytes(self.smallblock[0x78:0x7a], "little")
        secret_id = int.from_bytes(self.smallblock[0x7a:0x7c], "little")
        trainer_badges = self.get_badge_info()
        money = int.from_bytes(self.smallblock[0x7C:0x7F], "little")
        # Progress
        bar = '/'.join(["*" for _ in range(len(self.get_badge_info()))] + ["-" for _ in range(8 - len(self.get_badge_info()))])
        gym_progress = (f"[{bar}]", f"{bar.count('*')}/8 Gyms Beaten!")
        # party:
        trainer_party = party(self.smallblock[0xA0:0x628])
        #
        trainer_data = {
            "name":trainer_name,
            "gender":trainer_gender,
            "tid":trainer_id,
            "sid":secret_id,
            "badges":trainer_badges,
            "money":money,
            "gym_progress":gym_progress,
            'party':trainer_party,
        }
        return trainer(trainer_data)