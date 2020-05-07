import lib
import itertools
class trainer:
    def __init__(self, trainer_info):
            self.name = trainer_info["name"]
            self.gender = trainer_info["gender"]
            self.trainer_id = trainer_info["tid"]
            self.secret_id = trainer_info["sid"]
            self.badges = trainer_info["badges"]
            self.money = trainer_info["money"]
            self.gym_progress = trainer_info["gym_progress"]
    def display_trainer_info(self):
        lines = {
            "first_header":f"-----Trainer: {lib.cstring(self.name, color='w/blu')}/{lib.cstring(self.gender, color='w/blu')}-----",
            "first_id":f"Trainer ID:{''.join([' ' for _ in range(14-len('Trainer ID:'))])}{lib.cstring(self.trainer_id, color='w/blu')}",
            "second_id":f"Secret ID:{''.join([' ' for _ in range(14-len('Secret ID:'))])}{lib.cstring(self.secret_id, color='w/blu')}",
            "money":f"Money:{''.join([' ' for _ in range(14-len('Money:'))])}{lib.cstring('$' + str(self.money), color='g/blu')}",
            "badge_lines":f"{lib.cstring(self.name, color='w/blu')} has {', '.join(self.badges)}\n",
            "prog_bar":f"{lib.cstring(self.gym_progress[0], color='g/blu')} => {lib.cstring(self.gym_progress[1], color='w/blu')}"
        }

        lines['border'] = (''.join(['-' for _ in range(len(f"-----{lines['first_header']}-----") + 5)])) + '\n'
        lines['head_pad'] = ''.join(['-' for _ in range((len(lines['first_header']) - len('Game Progress')) // 2)])
        lines['second_header'] = f"{lines['head_pad']}Game Progress{lines['head_pad']}"
        full_display = f"""{lines['border']}{lines['first_header']}\n{lines['first_id']}\n{lines['second_id']}\n{lines['money']}\n{lines['second_header']}\n{lines['badge_lines']}\n{lines['prog_bar']}\n{lines['border']}"""
        print(full_display)
class save:
    def __init__(self, savedata):
        self.smallblock = savedata[0x00000:0x0CF2B]
        self.bigblock = savedata[0x0CF2C:0x1F10F]
        self.smallblock_backup = savedata[(0x00000 + 0x40000):(0x0CF2B + 0x40000)]
        self.bigblock_backup = savedata[(0x0CF2C + 0x40000):(0x1F10F + 0x40000)]
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
        badge_counts = {y:x+1 for x, y in enumerate([sum(list(badge_dict.keys())[:-x]) if x != 0
                                                        else sum(list(badge_dict.keys())) for x in reversed(range(8))])}
        if value in badge_dict.keys():
            return [f"{badge_dict[value]} Badge"]
        elif value in badge_counts.keys():
            return [f"{list(badge_dict.values())[x]} Badge" for x in range(badge_counts[value])]
        else:
            combos = list(itertools.chain.from_iterable(itertools.combinations(list(badge_dict.keys()), r) for r in range(len(list(badge_dict.keys()))+1)))[1:]
            combolist = {sum(list(sublist)):list(sublist) for sublist in combos}
            return [f"{badge_dict[x]} Badge" for x in combolist[value]]

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
        trainer_data = {
            "name":trainer_name,
            "gender":trainer_gender,
            "tid":trainer_id,
            "sid":secret_id,
            "badges":trainer_badges,
            "money":money,
            "gym_progress":gym_progress
        }
        return trainer(trainer_data)