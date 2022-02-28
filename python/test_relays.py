import board
from digitalio import DigitalInOut, Direction
import time

RELAY_CLOSED = False
RELAY_OPEN   = not RELAY_CLOSED

# the output of "dir(board)" on a Pi3 (likely true of all Pi models: zero through 4)...
# ['CE0', 'CE1', 'D0', 'D1', 'D10', 'D11', 'D12', 'D13', 'D14', 'D15', 'D16', 'D17', 'D18', 'D19', 'D2', 'D20', 'D21', 'D22', 'D23', 'D24', 'D25', 'D26', 'D27', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9', 'I2C', 'MISO', 'MISO_1', 'MOSI', 'MOSI_1', 'RX', 'RXD', 'SCK', 'SCK_1', 'SCL', 'SCLK', 'SCLK_1', 'SDA', 'SPI', 'TX', 'TXD', '__blinka__', '__builtins__', '__cached__', '__doc__', '__file__', '__loader__', '__name__', '__package__', '__repo__', '__spec__', '__version__', 'ap_board', 'board_id', 'detector', 'pin', 'sys']

# Zone Valve Transformer @ 40VA / 24V AC (Red & White)
# ------------- A & C ---------------
# ---------- Normally Open ----------
# RELAY_01 @ board.D5     # Heat - 1, 5, 9, 13
RELAY_01 = DigitalInOut(board.D5)
RELAY_01.direction = Direction.OUTPUT
# RELAY_02 @ board.D6     # Heat - 2, 6, 10, 14
RELAY_02 = DigitalInOut(board.D6)
RELAY_02.direction = Direction.OUTPUT
# RELAY_03 @ board.D13    # Heat - 3, 7, 11, 15
RELAY_03 = DigitalInOut(board.D13)
RELAY_03.direction = Direction.OUTPUT
# RELAY_04 @ board.D16    # Heat - 4, 8, 12, 16
RELAY_04 = DigitalInOut(board.D16)
RELAY_04.direction = Direction.OUTPUT

# Kiosk Transformer @ 50VA / 24V AC (Orange & Black)
# ------------- A & B ---------------
# ---------- Normally Closed ----------
# RELAY_05 @ board.D19    # Kiosks - 1 & 3, 5 & 7,  9 & 11, 13 & 15
RELAY_05 = DigitalInOut(board.D19)
RELAY_05.direction = Direction.OUTPUT
# RELAY_06 @ board.D20    # Kiosks - 2 & 4, 6 & 8, 10 & 12, 14 & 16
RELAY_06 = DigitalInOut(board.D20)
RELAY_06.direction = Direction.OUTPUT
# RELAY_07 @ board.D21    # Entrance Pi Button Monitor - B1, B2, B3, B4
RELAY_07 = DigitalInOut(board.D21)
RELAY_07.direction = Direction.OUTPUT
# RELAY_08 @ board.D26    # Entrance TTGo VDB - B1, B2, B3, B4
RELAY_08 = DigitalInOut(board.D26)
RELAY_08.direction = Direction.OUTPUT

# Second bank of eight relays (10-wire harness connected to auxiliar GPIO header)
# (colors from the black side down)

# Locks Transformer @ 24VA / 12V DC (Green & Blue)
# ------------- A & C ---------------
# ---------- Normally Open ----------
# white
# RELAY_16 @ board.D23    # Apt Locks - 1, 5,  9, 13
RELAY_16 = DigitalInOut(board.D23)
RELAY_16.direction = Direction.OUTPUT
# green
# RELAY_15 @ board.D18    # Apt Locks - 2, 6, 10, 14
RELAY_15 = DigitalInOut(board.D18)
RELAY_15.direction = Direction.OUTPUT
# yellow
# RELAY_14 @ board.D15    # Apt Locks - 3, 7, 11, 15
RELAY_14 = DigitalInOut(board.D15)
RELAY_14.direction = Direction.OUTPUT
# blue
# RELAY_13 @ board.D14    # Apt Locks - 4, 8, 12, 16
RELAY_13 = DigitalInOut(board.D14)
RELAY_13.direction = Direction.OUTPUT
# yellow
# RELAY_12 @ board.D22    # Building Entrance Locks - B1, B2, B3, B4
RELAY_12 = DigitalInOut(board.D22)
RELAY_12.direction = Direction.OUTPUT

# VDb-R Transformer @ 30VA / 16V AC (Yellow & Brown)
# ------------- A & B ---------------
# ---------- Normally Closed ----------
# green
# RELAY_11 @ board.D27    # Apt VDBs - 1 & 3, 5 & 7,  9 & 11, 13 & 15
RELAY_11 = DigitalInOut(board.D27)
RELAY_11.direction = Direction.OUTPUT
# blue
# RELAY_10 @ board.D17    # Apt VDBs - 2 & 4, 6 & 8, 10 & 12, 14 & 16
RELAY_10 = DigitalInOut(board.D17)
RELAY_10.direction = Direction.OUTPUT

# --- No Transformer ---
# ------------- A & C ---------------
# ---------- Normally Open ----------
# red & white
# RELAY_09 @ board.D4     # End Switdh Override
RELAY_09 = DigitalInOut(board.D4)
RELAY_09.direction = Direction.OUTPUT

# DigitalInOut object dict...
digital_io_object_dict = {
# First bank of eight relays (direct connection to GPIO header)

    # Zone Valve Transformer @ 40VA / 24V AC (Red & White)
    # ------------- A & C ---------------
    # ---------- Normally Open ----------
    'relay_01': RELAY_01      # Heat - 1, 5, 9, 13
    , 'relay_02': RELAY_02    # Heat - 2, 6, 10, 14
    , 'relay_03': RELAY_03    # Heat - 3, 7, 11, 15
    , 'relay_04': RELAY_04    # Heat - 4, 8, 12, 16

    # Kiosk Transformer @ 50VA / 24V AC (Orange & Black)
    # ------------- A & B ---------------
    # ---------- Normally Closed ----------
    , 'relay_05': RELAY_05    # Kiosks - 1 & 3, 5 & 7,  9 & 11, 13 & 15
    , 'relay_06': RELAY_06    # Kiosks - 2 & 4, 6 & 8, 10 & 12, 14 & 16
    , 'relay_07': RELAY_07    # Entrance Pi Button Monitor - B1, B2, B3, B4
    , 'relay_08': RELAY_08    # Entrance TTGo VDB - B1, B2, B3, B4

# Second bank of eight relays (10-wire harness connected to auxiliar GPIO header)
    # (colors from the black side down)

    # Locks Transformer @ 24VA / 12V DC (Green & Blue)
    # ------------- A & C ---------------
    # ---------- Normally Open ----------
    # white
    , 'relay_16': RELAY_16    # Apt Locks - 1, 5,  9, 13
    # green
    , 'relay_15': RELAY_15    # Apt Locks - 2, 6, 10, 14
    # yellow
    , 'relay_14': RELAY_14    # Apt Locks - 3, 7, 11, 15
    # blue
    , 'relay_13': RELAY_13    # Apt Locks - 4, 8, 12, 16
    # yellow
    , 'relay_12': RELAY_12    # Building Entrance Locks - B1, B2, B3, B4

    # VDb-R Transformer @ 30VA / 16V AC (Yellow & Brown)
    # ------------- A & B ---------------
    # ---------- Normally Closed ----------
    # green
    , 'relay_11': RELAY_11    # Apt VDBs - 1 & 3, 5 & 7,  9 & 11, 13 & 15
    # blue
    , 'relay_10': RELAY_10    # Apt VDBs - 2 & 4, 6 & 8, 10 & 12, 14 & 16

    # --- No Transformer ---
    # ------------- A & C ---------------
    # ---------- Normally Open ----------
    # red & white
    , 'relay_09': RELAY_09     # End Switdh Override
}

def relay_test_all(relay_dict):
    print('relay_test_all()')
    count = 0
    # set all to open rapidly...
    for i in digital_io_object_dict:
        print("{} | Set {} GPIO {} to OFF by sending {}".format(count, i, repr(digital_io_object_dict[i]), RELAY_OPEN))
        digital_io_object_dict[i].value = RELAY_OPEN
        count += 1
    count = 0
    # close one by one slowly...
    for i in relay_dict:
        print("{} | Set {} GPIO {} to ON by sending {}".format(count, i, relay_dict[i], RELAY_CLOSED))
        relay_dict[i].value = RELAY_CLOSED
        time.sleep(0.5)
        count += 1
    count = 0
    # reset all to open rapidly...
    for i in digital_io_object_dict:
        print("{} | Set {} GPIO {} to OFF by sending {}".format(count, i, repr(digital_io_object_dict[i]), RELAY_OPEN))
        digital_io_object_dict[i].value = RELAY_OPEN
        count += 1

test_raw = False
if test_raw:
    print('relay raw test')
    count = 0
    # Initialize all to open...
    for i in digital_io_object_dict:
        print("{} | Set {} GPIO {} to OFF by sending {}".format(count, i, repr(digital_io_object_dict[i]), RELAY_OPEN))
        digital_io_object_dict[i].value = RELAY_OPEN
        count += 1
    try:
        while (True):
            count = 0
            # close one by one...
            for i in digital_io_object_dict:
                print("{} | Set {} GPIO {} to ON by sending {}".format(count, i, digital_io_object_dict[i], RELAY_CLOSED))
                digital_io_object_dict[i].value = RELAY_CLOSED
                time.sleep(0.5)
                count += 1
            count = 0
            # open one by one...
            for i in digital_io_object_dict:
                print("{} | Set {} GPIO {} to OFF by sending {}".format(count, i, digital_io_object_dict[i], RELAY_OPEN))
                digital_io_object_dict[i].value = RELAY_OPEN
                time.sleep(0.5)
                count += 1
            time.sleep(1)
    # catch CTRL-C to close open all relays before exiting the program..
    except KeyboardInterrupt:
        print("\nCTRL-C pressed.  Program exiting...Exited")

    # Turn all the relays OFF upon CTRL-C exit
    for i in digital_io_object_dict:
        digital_io_object_dict[i].value = RELAY_OPEN
else:
    relay_test_all(digital_io_object_dict)

