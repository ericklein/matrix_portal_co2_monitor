#
#  Project Name:   matrix_portal_co2_monitor
#  Description:    display large icon on HUB75 matrix display representing CO2 level
#
# modified from:
# SPDX-FileCopyrightText: 2021 Carter Nelson for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
import displayio
import adafruit_imageload
from adafruit_matrixportal.matrix import Matrix
import adafruit_scd4x

# --| User Config |----
CO2_CUTOFFS = (800, 1200, 2000)
UPDATE_RATE = 60
# ---------------------

# the sensor
# i2c = board.I2C()  # uses board.SCL and board.SDA
i2c = board.STEMMA_I2C()  # For using the built-in STEMMA QT connector on a microcontroller
scd4x = adafruit_scd4x.SCD4X(i2c)
scd4x.altitude = 90

scd4x.start_periodic_measurement()

# the display
matrix = Matrix(width=64, height=32, bit_depth=6)
display = matrix.display
display.rotation = 90  # matrixportal up
# display.rotation = 270 # matrixportal down

# current condition smiley face
smileys_bmp, smileys_pal = adafruit_imageload.load("/bmps/smileys.bmp")
smiley = displayio.TileGrid(
    smileys_bmp,
    pixel_shader=smileys_pal,
    x=0,
    y=0,
    width=1,
    height=1,
    tile_width=32,
    tile_height=32,
)

# current condition label
tags_bmp, tags_pal = adafruit_imageload.load("/bmps/tags.bmp")
label = displayio.TileGrid(
    tags_bmp,
    pixel_shader=tags_pal,
    x=0,
    y=32,
    width=1,
    height=1,
    tile_width=32,
    tile_height=16,
)

# current CO2 value
digits_bmp, digits_pal = adafruit_imageload.load("/bmps/digits.bmp")
co2_value = displayio.TileGrid(
    digits_bmp,
    pixel_shader=digits_pal,
    x=0,
    y=51,
    width=4,
    height=1,
    tile_width=8,
    tile_height=10,
)

# put em all together
splash = displayio.Group()
splash.append(smiley)
splash.append(label)
splash.append(co2_value)

# and show em
display.root_group = splash

def update_display(value):
    # Clamp/normalize
    if value is None or value != value:  # NaN check
        value = 0
    value = int(round(abs(value)))
    if value > 9999:
        value = 9999  # avoid negative index when > 4 digits

    # smiley and label bands
    if value < CO2_CUTOFFS[0]:
        idx = 0
    elif value < CO2_CUTOFFS[1]:
        idx = 1
    elif value < CO2_CUTOFFS[2]:
        idx = 2
    else:
        idx = 3
    smiley[0] = idx
    label[0] = idx

    # clear the 4 digits to "blank" (tile 10)
    for i in range(4):
        co2_value[i] = 10  # ensure your digits sheet HAS index 10

    # write digits right-aligned (handle zero explicitly)
    i = 3
    if value == 0:
        co2_value[i] = 0
    else:
        while value and i >= 0:
            co2_value[i] = value % 10
            value //= 10
            i -= 1

first_sample_shown = False
while True:
    try:
        if scd4x.data_ready:
            co2 = scd4x.CO2
            temp = scd4x.temperature
            rh = scd4x.relative_humidity

            update_display(co2)

            # print once to confirm it's alive, then occasionally
            if not first_sample_shown or (time.monotonic() % 10) < 0.2:
                print("CO2: %d ppm" % co2)
                print("Temperature: %0.1f *C" % temp)
                print("Humidity: %0.1f %%" % rh)
                print()
                first_sample_shown = True
    except Exception as e:
        # Show the real reason things failed (bad BMP index, missing file, etc.)
        print("ERR:", repr(e))
        time.sleep(0.5)
    time.sleep(UPDATE_RATE)