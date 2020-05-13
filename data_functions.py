import misc
import string
import struct
import sys
# Functions
def char_conversion(data, decode=True, pad=None):
    """
    :param data: The data to be operated on. This is either bytes to decode or a string to encode
    :param decode: True to decode, False to decode
    :param pad: Values to append to the encoded string to fill an offset. For example, the trainer name is
    0x68 -> 0x77. If we encode "AAAA", we would pass [255, 255, 0, 0, 0, 0] as the pad to fill the remaining bytes
    :return: decoded string or encoded bytes
    """
    if decode:
        return ''.join([chr(data[i:i + 2][0] + 22) for i in range(0, len(data), 2) if len(data[i:i + 2]) > 1 and data[i:i + 2][1] == 0x01])
    else:
        converted = [1] * (len([ord(x) - 22 for x in data]) * 2 - 1)
        converted[0::2] = [ord(x) - 22 for x in data]
        if pad:
            for item in pad:
                converted.append(item)
        return bytearray(converted)
def item_id_conversion(data, decode=True):
    if decode:
        return misc.item_associations[f'{data}']
    else:
        return list(misc.item_associations.keys())[list(misc.item_associations.values()).index(data)]
def decrypt_pokemon(encrypted_data):
    # Values
    # D1 D8 D5 FE
    personality_value = struct.unpack(">I", encrypted_data[0x00:0x04])[0]
    checksum = struct.unpack(">H", encrypted_data[0x06:0x08])[0]
    shift_value = ((personality_value & 0x3E000) >> 0xD) % 24
    print(f"Checksum: {checksum}")
    print(f"Initial function (seeded with checksum): (0x41C64E6D * {checksum}) + 0x00006073 = {(0x41C64E6D * checksum) + 0x00006073}")
    print(f"PV of {personality_value} resulting in a shift value of {shift_value}")
    # PRNG
    def Crypt(data, value, seed):
        # Get seed
        seed = ((0xFFFFFFFF & (0x41C64E6D * seed)) + 0x00006073) & 0xFFFFFFFF
        print(seed)
        last16 = struct.pack('>H', seed % (2 ** 16))
        # Convert back to unsigned short (two bytes) -> (7801,)
        data[value] ^= (last16[0])
        data[value + 1] ^= (last16[1])
        return seed
    def CryptArray(data, seed, end):
        # initialize currentseed to be checksum
        currentseed = seed
        # Loop over every two bytes:
        # "Sequentially, for each 2-byte word Y from 0x08 to 0x87, apply the transformation: unencryptedByte = Y xor rand()"
        for i in range(8, end, 2):
            # Crypt twice
            Crypt(data, i, currentseed)
            # Update current seed
            currentseed = Crypt(data, i, currentseed)
    # Shuffle
    def unshuffle(data, sv):
        sv = f"0{sv}" if sv < 10 else str(sv)
        blocks = [bytearray(data[8:40]), bytearray(data[40:72]),
                  bytearray(data[72:104]), bytearray(data[104:136])]
        combined_blocks = []
        for index in [string.ascii_uppercase.index(x.upper()) for x in misc.shifts[sv][1]]:
            combined_blocks.extend(blocks[index])
        return bytearray(combined_blocks)

    CryptArray(encrypted_data, checksum, 0x88)
    theoretically_decrypted_data = unshuffle(encrypted_data, shift_value)
    #print(len(theoretically_decrypted_data))
    print(theoretically_decrypted_data)
    print(f"OT: {theoretically_decrypted_data[0x68:0x77]}\n{misc.bytearr_to_hexstring(theoretically_decrypted_data[0x68:0x77])}")