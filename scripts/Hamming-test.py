def calcRedundantBits(m):
    for i in range(m):
        if 2**i >= m + i + 1:
            return i


def posRedundantBits(data, r):
    j = 0
    k = 1
    m = len(data)
    res = ""
    for i in range(1, m + r + 1):
        if i == 2**j:
            res = res + "0"
            j += 1
        else:
            res = res + data[-1 * k]
            k += 1
    return res[::-1]


def calcParityBits(arr, r):
    n = len(arr)
    for i in range(r):
        val = 0
        for j in range(1, n + 1):
            if j & (2**i) == (2**i):
                val = val ^ int(arr[-1 * j])
        arr = arr[: n - (2**i)] + str(val) + arr[n - (2**i) + 1 :]
    return arr


def detectError(arr, nr):
    n = len(arr)
    res = 0
    for i in range(nr):
        val = 0
        for j in range(1, n + 1):
            if j & (2**i) == (2**i):
                val = val ^ int(arr[-1 * j])
        res = res + val * (10**i)
    return int(str(res), 2)


def fixError(arr, error_pos):
    if error_pos == 0:
        return arr
    n = len(arr)
    arr = list(arr)
    if arr[n - error_pos] == "0":
        arr[n - error_pos] = "1"
    else:
        arr[n - error_pos] = "0"
    return "".join(arr)


# Function to convert bytes to a string of bits
def bytes_to_bits(data):
    return "".join(format(byte, "08b") for byte in data)


# Function to convert a string of bits back to bytes
def bits_to_bytes(bits):
    return bytes(int(bits[i : i + 8], 2) for i in range(0, len(bits), 8))


# Enter the data to be transmitted
data = b"01101000011001010110110001101100011011110010000001110111011001010110110001100011011011110110110101100101"

# Convert bytes to bits
data_bits = bytes_to_bits(data)

print(f"data bits {data_bits}")

# Calculate the number of Redundant Bits Required
m = len(data_bits)
r = calcRedundantBits(m)

# Determine the positions of Redundant Bits
arr = posRedundantBits(data_bits, r)

# Determine the parity bits
arr = calcParityBits(arr, r)

# Data to be transferred
print("Data transferred is " + arr)

# Simulate error in transmission by changing a bit value
error_bits = b"01110000001100010011000100110000001100010011000000110000001100000011000000110001001100010011000000110000001100010011000000110001001100000011000100110001001100000011000100110001001100000011000000110000001100010011000100110000001100010011000100110000001100000011000000110001001100010011000000110001001100010011000100110001001100000011100000011000100110000001100000011000000110000001100000011000000110001001100010011000100110000001100010011000100110001001100000011000100110001001100000011000000110001001100000011000100110000001100010011000100110000001100010011000100110000001100000011000001011000100110001001100000011000000110000001100010011000100110000001100010011000100110000001100010011000100110001001100010011000010011000100110001001100000011000100110001001100000011000100110001000110001001100010011000000110010000110001001100000001100000100"
error_bits_str = error_bits.decode()
print(f"error bits {error_bits_str}")

# Detect error position
correction = detectError(error_bits_str, r)
if correction == 0:
    print("There is no error in the received message.")
else:
    print("The position of error is ", len(error_bits_str) - correction + 1, "from the left")
    corrected_bits = fixError(error_bits_str, correction)
    corrected_data_bits = corrected_bits[-len(data_bits):]  # Extract the data part
    corrected_data = bits_to_bytes(corrected_data_bits)
    print(f"Corrected Data bits: {corrected_data_bits}")
    print(f"Corrected Data as bytes: {corrected_data}")