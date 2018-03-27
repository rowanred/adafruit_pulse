# Adafruit Circuit Playground Express
# Pulsing NeoPixels with capacitive touch controls for color, speed, brightness
#
# This will pulse the onboard NeoPixel ring from off to full brightness with
# a cycle period that can be changed.  It sets up three capacitive touch
# sensors that change the color of the LEDs, the maximum brightness of the
# pulse cycle, and the length of the pulse cycle.

# Python library imports
import board
import digitalio
import math
import neopixel
import time
import touchio

###########################################################################
# CONSTANTS
DOTSTAR_BRIGHTNESS = 0.7    # When initializing the NeoPixel ring, use this as
                            # brightness (setting the PWM) - even if the pulse
                            # cycle maximum brightness is changed, it will
                            # always be within this hardware range.  Values
                            # between 0 (off) and 1.0 (exceedingly bright).
                            # Higher values will use more battery power, and
                            # the practical difference between 0.7 and 1.0
                            # is minimal.

MAX_BRIGHTNESS = 255    # This is the maximum brightness of a pulse cycle.
                        # When the brightness sensor is touched it will
                        # change the current maximum brightness up to this
                        # value, and then cycle back down to 0 (off).

MAX_CYCLE_TIME = 10.0   # This is the longest pulse cycle time.
MIN_CYCLE_TIME = 0.5    # This is the shortest pulse cycle time.
                        # The pulse cycle is a sine wave brightness cycle
                        # that goes from brightness 0 (off) to the current
                        # maximum brightness and back in the cycle time.
                        # Touching the cycle time sensor will change the
                        # cycle time, increasing it to the maximum (long,
                        # slow pulses) and then decreasing it to the minimum
                        # (fast pulses).

###########################################################################
# FUNCTIONS

# Proportionally scale a number that is in the range of x0 to x1 to be
# within the range of y0 to y1.
def scale(x, x0, x1, y0, y1):
    return y0+(x-x0)*((y1-y0)/(x1-x0))

# A variation on the standard color wheel function that also sets the
# brightness of the color by scaling the color values to be within the
# range of 0 to max_brightness.  If the optional brightness and max_brightness
# are not included, it behaves the same as the usual wheel() function.
def wheel(pos, brightness=255, max_brightness=255):
    if (pos < 0) or (pos > 255):
        return (0, 0, 0)

    scaled_brightness = int(scale(brightness, 0, 255, 0, max_brightness))
    if pos < 85:
        red = int(scale(255 - (pos*3), 0, 255, 0, scaled_brightness))
        green = int(scale(pos*3, 0, 255, 0, scaled_brightness))
        blue = 0
    elif pos < 170:
        pos -= 85
        red = 0
        green = int(scale(255 - (pos*3), 0, 255, 0, scaled_brightness))
        blue = int(scale(pos*3, 0, 255, 0, scaled_brightness))
    else:
        pos -= 170
        red = int(scale(pos*3, 0, 255, 0, scaled_brightness))
        green = 0
        blue = int(scale(255 - (pos*3), 0, 255, 0, scaled_brightness))
    return (red, green, blue)

###########################################################################
# INITIAL SETTINGS
color = 1                               # Start with red
cycle = 2.0                             # 2 second pulse cycle
cycle_change = -0.1                     # Touch will shorten the cycle time
                                        # by 0.1 second
cycle_brightness = 255                  # Start with NeoPixels on
cycle_max_brightness = MAX_BRIGHTNESS   # Pulse will go to maximum brightness
max_brightness_change = -1              # Touch will dim the max brightness

# Make sure the on-board red LED is turned off.
red_led = digitalio.DigitalInOut(board.D13)
red_led.switch_to_output(value=False)

# Pause for 5 seconds - allow the board to be set down so that the
# touch sensors can calibrate properly
start = time.monotonic()
while time.monotonic() - start <= 5.0:
    # Blink the red LED on and off every half second.
    red_led.value = True
    time.sleep(0.5)
    red_led.value = False
    time.sleep(0.5)

# Set up the capacitive touch sensors on A1, A2, A3
sensor = dict()
sensor['color'] = touchio.TouchIn(board.A1)
sensor['speed'] = touchio.TouchIn(board.A2)
sensor['brightness'] = touchio.TouchIn(board.A3)

# Initialize the NeoPixels and turn them off to start
pixels = neopixel.NeoPixel(board.NEOPIXEL, 10, brightness=DOTSTAR_BRIGHTNESS)
pixels.fill(wheel(1, cycle_brightness, cycle_max_brightness))
pixels.show()

# MAIN LOOP
while True:
    current = time.monotonic()

    # Look for any capacitive touch inputs
    for pad in sensor.keys():
        if sensor[pad].value:
            if pad == 'color':
                # cycle color
                color = color + 1
                if color > 255:
                    color = 1
                pixels.fill(wheel(color, cycle_brightness, cycle_max_brightness))
                pixels.show()
            elif pad == 'speed':
                # change pulse cycle time by 0.1 second
                cycle = cycle + cycle_change
                if cycle > MAX_CYCLE_TIME:
                    cycle = MAX_CYCLE_TIME - 0.1
                    cycle_change = -0.1
                elif cycle < MIN_CYCLE_TIME:
                    cycle = MIN_CYCLE_TIME + 0.1
                    cycle_change = 0.1
            elif pad == 'brightness':
                # change max brightness
                cycle_max_brightness = cycle_max_brightness + max_brightness_change
                if cycle_max_brightness > MAX_BRIGHTNESS:
                    cycle_max_brightness = MAX_BRIGHTNESS - 1
                    max_brightness_change = -1
                elif cycle_max_brightness < 10:
                    cycle_max_brightness = 11
                    max_brightness_change = 1
                pixels.fill(wheel(color, cycle_brightness, cycle_max_brightness))
                pixels.show()

    # This section always runs - we might have changed the color or
    # brightness of the LEDs with a touch input, and it might continue to
    # change if the touch is held.  If we don't also keep the pulse cycle
    # running, then when the touch is released we'll see a sudden change
    # in the cycle brightness.  If this runs, it will update the cycle
    # brightness with any changes to the color or maximum brightness,
    # making for a smoother transition.

    # Pulse by changing the brightness based on the cycle time.
    # Use a sine wave function here for a nice pulse, but any kind of
    # wave generator function can be used that can take time.monotonic()
    # as input.
    s = math.sin(current * (2 * math.pi / cycle))

    # We use an "internal" brightness that is always between 0 and 255.  The
    # wheel() function will scale that to the current maximum brightness.
    # Sine returns values between -1 and 1, so scale that between 0 and 255
    cycle_brightness = int(scale(s, -1.0, 1.0, 0, 255))

    # Then set the LEDs to the current color at the pulse brightness scaled
    # to the current maximum brightness.
    pixels.fill(wheel(color, cycle_brightness, cycle_max_brightness))
    pixels.show()
