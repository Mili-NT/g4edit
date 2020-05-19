import string
import struct
import indexes
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
    """
    This function serves as a wrapper around struct.pack and struct.unpack.
    This is used to encode integers -> bytes or decode bytes -> integers

    :param data: The data to encode/decode
    :param flag: The struct flag to use for packing/unpacking
    :param encode: True if encoding int->bytes, False if decoding bytes->int
    :return: the packed/unpacked data
    """
    if encode is False:
        return struct.unpack(flag, data)
    else:
        return struct.pack(flag, data)

def item_id_conversion(data, decode=True):
    """

    :param data: item ID or name
    :param decode: flag to indicate to do ID->name or name->ID
    :return: the name (str) associated with the passed ID, or the ID (int) associated with passed name
    """
    if decode:
        return indexes.item_assoc[data]
    else:
        return list(indexes.item_assoc.keys())[list(indexes.item_assoc.values()).index(data)]

def pokemon_conversion(pkmn_data, encrypt=False):
    """
    This function serves to decrypt a 236 byte array containing party pokemon data, or encrypt same array

    :param pkmn_data: The bytearray to decrypt/encrypt
    :param encrypt: Flag indicating which operation to perform
    :return: encrypted/decrypted bytearray
    """
    """
    There are two important non-encrypted components: the personality value (also called PV or PID) and the checksum
    
    The personality value is a 4-byte (32bit) integer that contains data about the pokemons gender, nature, shinyness, etc. It
    is used to get the order of the 32 byte data blocks for shuffling.
    
    The checksum is a 2 byte integer that is used to verify the data, but most importantly serves as the seed to the
    decryption function.
    """
    personality_value = byte_conversion(pkmn_data[0x00:0x04], "<I")[0]
    checksum = byte_conversion(pkmn_data[0x06:0x08], "<H")[0]
    """ 
    Get the shift value by performing a bitwise AND on the PV and 253952
    It then shifts right by 13 and performs modulo 24. The resulting value is between 00-23.
    
    It then gets the block order, a TUPLE containing a set of strings such as ABCD, CADB, BCDA, etc.
    The first (0th) element of the tuple is the order for re-shuffling prior to encrypting. The second (1st) element is
    the inverse, used for deshuffling after decryption.
    """
    shift_value = ((personality_value & 0x3E000) >> 0xD) % 24
    order = indexes.shifts[shift_value]
    """
    These are the actual function that do the *cryption operations.
    
    The encryption is done via a Linear Pseudorandom Number Generator:
    https://bulbapedia.bulbagarden.net/wiki/Pseudorandom_number_generation_in_Pok%C3%A9mon
    
    The PRNG can be represented by this function:
    X[n+1] = (0x41C64E6D * X[n] + 0x6073)
    
    Where x[n] is the seed, and the output x[n+1] is the seed for the next usage of the generator. The first use of the
    generator is seeded by the checksum.
    """
    def rand(data, i, seed):
        """
        :param data: the entire bytearray of the pokemon
        :param i: the index of the byte being operated on
        :param seed: If the first usage of the generator, this is the checksum. Else, the output of the previous usage
        :return: The new seed to be used next time the generator is called
        """
        # Implement the function with the passed seed
        seed = ((0xFFFFFFFF & (0x41C64E6D * seed)) + 0x00006073) & 0xFFFFFFFF
        # We need the "upper 16 bits" of the above function, so we convert first shift the seed 16 bits to the right,
        # then convert that to a 2-byte LITTLE-ENDIAN short. The return value is a tuple of (8 bits, 8 bits)
        bits = byte_conversion(seed >> 16, '<H', True)
        # Now we need to "apply the transformation: unencryptedByte = Y xor rand()" where rand() is our upper 16 bits
        # XOR byte at i by first 8 bits of upper 16 bits
        data[i] ^= bits[0]
        # XOR byte at i+1 by second 8 bits of upper 16 bits
        data[i + 1] ^= bits[1]
        # return seed for future generator calls
        return seed
    def crypt(data, seed, offset):
        """
        :param data: the entire bytearray of the pokemon
        :param seed: The seed to pass to rand() calls. This is initally the checksum
        :param offset: The offset is a TUPLE of the index of start byte and the index of the ending byte. So, for
        decryption we'd start at 8 and end at 136. offset would be (8, 136)
        :return: None, modifications are made in place
        """
        # The current seed is set to the passed value (checksum)
        currentseed = seed
        # We iterate over the values between our start and end integer, with a step of 2.
        # The step is because the transformation applied by rand() is "for each 2-byte word Y from 0x08 to 0x87"
        for i in range(offset[0], offset[1], 2):
            # Call rand() twice to perform the decryption
            rand(data, i, currentseed)
            rand(data, i, currentseed)
            # Call rand a third time to update the currentseed to the output of the PRNG
            currentseed = rand(data, i, currentseed)
    # We call the crypt function with a start of 8 and end of 136, with the checksum as the initial seed
    crypt(pkmn_data, checksum, (8, 136))
    # This decrypts the battle stats, which are encrypted but not shuffled
    if len(pkmn_data) > (4 * 32)+8:
        crypt(pkmn_data, personality_value, (136, len(pkmn_data)))

    if encrypt:
        return pkmn_data, personality_value, checksum
    else:
        # Separate the data into 32 byte blocks
        blocks = [pkmn_data[8:40], pkmn_data[40:72], pkmn_data[72:104], pkmn_data[104:136]]
        # Map the block order (ABCD, CDAB, etc.) to the bytes at the corresponding index in blocks.
        positions = {y: blocks[x] for x, y in enumerate(order[0])}
        # We create a new bytearray and arrange the bytes such that they are in ABCD order.
        ordered = bytearray()
        for x in "ABCD":
            ordered.extend(positions[x])
        # We return the entire pokemon bytearray, but substitute the encrypted, shuffled bytes at 8:136 with the
        # decrypted, unshuffled bytes. We also return the PV and checksum.
        return bytearray([x for x in pkmn_data][0:8] + [x for x in ordered] + [x for x in pkmn_data][136:236]), personality_value, checksum

def byte_to_bit(data):
    """
    This function splits bytes into an array of 8 bits.
    If a bytearray is passed, it splits it into a linked list of bits.

    :param data: The byte or bytearray to decode to bits
    :return: A list or linked list of bits
    """
    # If the data is a bytearray:
    if isinstance(data, bytearray):
        # Split into a flat list of ints for each byte
        x = [byte for byte in data]
        # If the data is a single byte, return a singleton list.
        # This is added to prevent a singleton linked list with a singleton list as an element
        if len(x) == 1:
            return [(x[0] >> i) & 1 for i in range(8)]
        else:
            # Return a linked list, with elements of length 8, for each byte in the array
            return [[(byte >> i) & 1 for i in range(8)] for byte in [byte for byte in data]]
    # If the data is a single int, aka a single byte that has been passed and automatically converted to an int:
    elif isinstance(data, int):
        return [(data >> i) & 1 for i in range(8)]

def bytearr_to_hexstring(bytearr):
    """
    This function converts a bytearray to a string of hex encoded data in the format you'd see in a hex editor.
    For example:
    bytearr => bytearray(b'>\x01I\x01W\x01X\x01\xff\xff\xff\xff\xff\xffR\x01\xff\xff\xb1\x01\xff')
    Decoded data: 3E 01 49 01 57 01 58 01 FF FF FF FF FF FF 52 01 FF FF B1 01 FF

    :param bytearr: An array of bytes
    :return: Hex encoded data
    """
    return ' '.join([f'{i:0>2X}' for i in bytearr])

def list_to_chunks(array, num_of_chunks):
    num_of_chunks = max(1, num_of_chunks)
    return (array[i:i + num_of_chunks] for i in range(0, len(array), num_of_chunks))
