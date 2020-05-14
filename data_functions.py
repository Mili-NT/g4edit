import misc
import string
import struct
import sys
# Functions
def char_conversion(data, encode=False, pad=None):
    """
    :param data: The data to be operated on. This is either bytes to decode or a string to encode
    :param encode: True to decode, False to decode
    :param pad: Values to append to the encoded string to fill an offset. For example, the trainer name is
    0x68 -> 0x77. If we encode "AAAA", we would pass [0, 0, 0, 0] as the pad to fill the remaining bytes
    :return: decoded string or encoded bytes
    """
    symbols = {
        171:'!',
        208:'@',
        192:'#',
        168:'$',
        210:'%',
        222:' ',
        173:',',
        174:'.',
        196:':',
        197:';',
        172:'?',
        189:'+',
        190:'-',
        193:'=',
        177:'/',
        195:'~',
        191:'*',
        238:'♂',
        239:'♀',
    }
    enc = {**{ord(x) - 22: x for x in string.ascii_uppercase},
           **{ord(x) - 28: x for x in string.ascii_lowercase},
           **symbols}
    dec = {letter:integer for integer, letter in enc.items()}

    if encode is False:
        terminated = [data[i] for i in range(len(data)) if 0xFF not in data[0:i] and data[i] != 0xFF]
        asints = [terminated[i:i + 2][0] for i in range(0, len(terminated), 2) if len(terminated[i:i + 2]) > 1]
        return ''.join([enc[x] if x in enc.keys() else '?' for x in asints])
    else:
        converted = [dec[x] if x in dec.keys() else dec['?'] for x in data]
        formatted = [1] * (len(converted) * 2 - 1)
        formatted[0::2] = converted
        formatted = formatted + [1, 255, 255]
        if pad:
            formatted = formatted + pad
        return bytearray(formatted)

def byte_conversion(data, flag, encode=False):
    if encode is False:
        return struct.unpack(flag, data)
    else:
        return struct.pack(flag, data)

def item_id_conversion(data, decode=True):
    if decode:
        return misc.item_associations[f'{data}']
    else:
        return list(misc.item_associations.keys())[list(misc.item_associations.values()).index(data)]

def decrypt_pokemon(encrypted_data):
    personality_value = byte_conversion(encrypted_data[0x00:0x04], "<I")[0]
    checksum = byte_conversion(encrypted_data[0x06:0x08], "<H")[0]
    def rand(data, i, seed):
        seed = ((0xFFFFFFFF & (0x41C64E6D * seed)) + 0x00006073) & 0xFFFFFFFF
        bits = byte_conversion(seed >> 16, '<H', True)
        data[i] ^= bits[0]
        data[i + 1] ^= bits[1]
        return seed
    def decrypt(data, seed, offset):
        currentseed = seed
        for i in range(offset[0], offset[1], 2):
            rand(data, i, currentseed)
            rand(data, i, currentseed)
            currentseed = rand(data, i, currentseed)
    decrypt(encrypted_data, checksum, (8, 136))
    if len(encrypted_data) > (4 * 32)+8:
        decrypt(encrypted_data, personality_value, (136, len(encrypted_data)))
    return encrypted_data

