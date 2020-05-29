import string
import struct
import indexes
# Important Conversion Functions
def char_conversion(data, encode=False, pad=None):
    """
    This function decodes the nasty proprietary character encoding scheme used by the game. For previous generations,
    a similar but different two-byte character encoding was used. I was able to figure out that uppercase letters
    have an offset of 22, and lowercase has an offset of 28. The symbols remain a mystery.

    :param data: The data to be operated on. This is either bytes to decode or a string to encode
    :param encode: True to decode, False to decode
    :param pad: Values to append to the encoded string to fill an offset.
    :return: decoded string or encoded bytes
    """
    symbols = {
        # Reveal your secrets to me, symbols
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
    # Combine all letters and symbols into with their OFFSET integer representation as a key:
    # This forms our encoded dictionary
    enc = {**{ord(x) - 22: x for x in string.ascii_uppercase},
           **{ord(x) - 28: x for x in string.ascii_lowercase},
           **symbols}
    # The decoded dictionary is literally just reversed key:value pairs
    dec = {letter:integer for integer, letter in enc.items()}

    if encode is False:
        # To decode, we first strip anything after the first detected 0xFF byte (These terminate the strings):
        terminated = [data[i] for i in range(len(data)) if 0xFF not in data[0:i] and data[i] != 0xFF]
        # The encoding scheme is split into two-byte chunks. The first byte is the character value, and the second is
        # 0x01. We split these and only deal with the character bytes.
        asints = [terminated[i:i + 2][0] for i in range(0, len(terminated), 2) if len(terminated[i:i + 2]) > 1]
        # Returns a string created by passing the isolated character bytes to the encoded dictionary
        return ''.join([enc[x] if x in enc.keys() else '?' for x in asints])
    else:
        # First, any weird symbol BS going on is replaced by a ?
        converted = [dec[x] if x in dec.keys() else dec['?'] for x in data]
        # First we intersperse the lists with ones to fit the two-byte encoding scheme
        formatted = [1] * (len(converted) * 2 - 1)
        formatted[0::2] = converted
        # Add an additional one at the end
        formatted = formatted + [1]
        # If a pad is passed, append that to the array
        if pad:
            formatted = formatted + pad
        # return an encoded bytearray
        return bytearray(formatted)

def byte_conversion(data, flag, encode=False):
    """
    This function serves as a wrapper around struct.pack and struct.unpack.
    This is used to encode integers into bytes or decode bytes into integers

    :param data: The data to encode/decode
    :param flag: The struct flag to use for packing/unpacking
    :param encode: True if encoding int->bytes, False if decoding bytes->int
    :return: the packed/unpacked data
    """
    if encode is False:
        return struct.unpack(flag, data)
    else:
        return struct.pack(flag, data)

def pokemon_conversion(pkmn_struct, encode=False):
    """
    This function serves to decrypt a 236 byte array containing party pokemon data, or encrypt same array

    :param pkmn_struct: The bytearray to decrypt/encrypt
    :param encode: Flag indicating which cryptographic operation to perform
    :return: encrypted/decrypted bytearray, personality value, and checksum
    """
    """
    ~~~~~ Pre-Cryptography ~~~~~
    There are 3 important components prior to performing cryptographic operations:
    [1]: The checksum: A 2 byte integer loctated at 0x06:0x08 that is used to verify the data after encrpytion, and 
    serves as the INITIAL seed to the decryption function.
    
    [2]: The personality value (PV/PID): A 4-byte (32bit) integer that contains data about the gender, nature, 
    shinyness, etc. It is used to get the shift value, which is calulated to find the order of the 32 byte data 
    blocks for shuffling.
    
    [3]: The shift value: Calculated by first performing a bitwise AND on the PV and 253952, then taking the resulting
    value and shifting right by 13 and performs modulo 24, resulting in a value between 00-23. That value is then passed
    to the indexes.shifts dictionary, which translated it into the four letter block order string.

    ~~~~~ Cryptography ~~~~~
    The encryption is done via an XOR Pad using a Linear Pseudorandom Number Generator:
    https://bulbapedia.bulbagarden.net/wiki/Pseudorandom_number_generation_in_Pok%C3%A9mon
    
    The PRNG can be represented by this function:
    X[n+1] = (0x41C64E6D * X[n] + 0x6073)
    
    Where x[n] is the seed, and the output x[n+1] is the seed for the next usage of the generator. The first use of the
    generator is seeded by the checksum.
    
    By taking the upper 16 bits of the output of the PRNG, we get the values we need to XOR by.
    """
    personality_value = byte_conversion(pkmn_struct[0x00:0x04], "<I")[0]
    checksum = byte_conversion(pkmn_struct[0x06:0x08], "<H")[0]
    shift_value = ((personality_value & 0x3E000) >> 0xD) % 24
    order = indexes.shifts[shift_value][0]
    # Misc
    def generate_checksum():
        # Initialize the new checksum as 0
        new_checksum = 0
        # For every two byte word between 0x08 and 0x88, we convert it to a 16bit int and add it to new_checksum
        for i in range(8, 136, 2):
            int16 = byte_conversion(bytearray([pkmn_struct[i], pkmn_struct[i + 1]]), 'H')[0]
            new_checksum += int16
        # Convert new checksum to bytes
        tobytes = byte_conversion(new_checksum, 'I', encode=True)
        count = 0
        # Write the checksum bytes to proper position
        for i in range(0x06, 0x08):
            pkmn_struct[i] = tobytes[0:2][count]
            count += 1
        # Return the new checksum bytes
        return byte_conversion(pkmn_struct[0x06:0x08], "<H")[0]
    # Cryptography Components
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
    def xor(data, seed, offset):
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
    def crypt(data, chk):
        xor(data, chk, (8, 136))
        if len(data) > (4 * 32) + 8:
            xor(data, personality_value, (136, len(data)))
    # Cryptography Processes
    def decrypt():
        # First we decrypt the bytes:
        crypt(pkmn_struct, checksum)
        # Then we deshuffle them from whatever the order[0] value is (i.e: CADB) to ABCD order
        blocks = [pkmn_struct[8:40], pkmn_struct[40:72], pkmn_struct[72:104], pkmn_struct[104:136]]
        positions = {y: blocks[x] for x, y in enumerate(order)}
        deordered = [positions[x] for x in "ABCD"]
        # Update the pkmn_struct with the decrypted data, and return it
        decrypted = write_to_offset(pkmn_struct, (0x08, 0x88), combine_bytestrings(deordered))
        return decrypted
    def encrypt():
        # First we generate the checksum to validate the data
        refreshed_checksum = generate_checksum()
        # We then shuffle the blocks from ABCD order to whatever order[0] is (i.e CADB)
        blocks = [pkmn_struct[8:40], pkmn_struct[40:72], pkmn_struct[72:104], pkmn_struct[104:136]]
        shuffled = [blocks[x] for x in letter_to_index(order)]
        # We write the SHUFFLED BUT NOT ENCRYPTED data to the correct position and assign that to `ordered`
        ordered = write_to_offset(pkmn_struct, (0x08, 0x88), combine_bytestrings(shuffled))
        # Now we call crypt and encrypt the data
        crypt(ordered, refreshed_checksum)
        return ordered
    # Calls and Return
    modified_struct = encrypt() if encode else decrypt()
    return modified_struct, personality_value, checksum
# General Conversion/Data Manipulation Functions
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

    I really only use this for debugging.

    :param bytearr: An array of bytes
    :return: Hex encoded data
    """
    return ' '.join([f'{i:0>2X}' for i in bytearr])

def combine_bytestrings(array):
    """
    This function combines an array of bytestrings into one big bytearray that can be cleanly passed to
    write_to_offset()

    :param array: An array of bytestrings
    :return: A bytearray consisting of the array values combined
    """
    combined = bytearray()
    for x in array:
        combined.extend(x)
    return combined

def letter_to_index(data, decode=False):
    """
    Converts a string to it's position in the alphabet, or vice versa.
    I thought I was going to use this function a lot more during the shuffling portion of pokemon decryption honestly.

    :param data: The string or array of ints to convert
    :param decode: False for string->index, True for index->string
    :return: The converted array
    """
    upper = string.ascii_uppercase
    if decode:
        array = upper[data] if isinstance(data, int) else [upper[index] for index in data]
    else:
        array = upper.index(data) if len(data) == 1 else [upper.index(l) for l in data.upper()]
    return array

def list_to_chunks(array, num_of_chunks):
    """
    :param array: The array to seperate into chunks
    :param num_of_chunks: The number of chunks to separate into
    :return: A linked list with `num_of_chunks` elements consisting of roughly equal size
    """
    num_of_chunks = max(1, num_of_chunks)
    return list((array[i:i + num_of_chunks] for i in range(0, len(array), num_of_chunks)))
# Read/Write Functions
def read_from_offset(whole, offset):
    """
    This function reads bytes from a given bytearray.

    :param whole: The bytearray to read values from
    :param offset: A tuple containing the starting and ending offset: (start, end). Alternatively, a single integer for
    reading a single value.
    :return: The byte(s) at specified offset
    """
    if isinstance(offset, int):
        return whole[offset]
    else:
        return whole[offset[0]:offset[1]]

def write_to_offset(data, offset, value):
    """
    This function writes a given bytestring/bytearray to an offset in a seperate bytearray

    :param data: The bytearray to write to
    :param offset: A tuple containing the starting and ending offset: (start, end). Alternatively, a single integer for
    reading a single value.
    :param value: The bytearray/bytestring to write to the offset
    :return: The modified bytearray, with the bytes at the specified offset replaced with the bytes specified by `value`
    """
    if isinstance(offset, int):
        data[offset] = value
    else:
        count = 0
        for i in range(offset[0], offset[1]):
            data[i] = value[count]
            count += 1
    return data

def get_index(index, element, from_val=False):
    """
    This function fetches an element from a dictionary, given both a dictionary and element.
    I wrote this function specifically for fetching keys when given a value, as I needed to do that frequently enough
    while operating on the indexes that it warranted making a function for cleanliness. I went ahead and made it a
    wrapper around python's default dictionary lookup for standardization.

    :param index: The dictionary to fetch keys/values from
    :param element: The element to fetch
    :param from_val: True if fetching a key from a value, False if fetching a value from a key
    :return: The opposite element in the k:v pair
    """
    try:
        if from_val:
            return list(index.keys())[list(index.values()).index(element)]
        else:
            return index[element]
    except Exception:
        return None

def is_valid(index, element, is_val=False):
    """
    This function checks to see if a given element exists in a specific position in the dictionary pairs.

    :param index: The dictionary to search through
    :param element: The element to check
    :param is_val: If True, checks for existence in the values instead of keys
    :return: True if element exists in specified position, otherwise False
    """
    return element in list(index.keys()) if is_val is False else element in list(index.values())
