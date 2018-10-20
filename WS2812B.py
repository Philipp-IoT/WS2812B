# WS2812B driver for MicroPython on ESP32
# MIT license; Copyright (c) 2018 Philipp Bolte (philipp@bolte.engineer)
# Version 0.2 beta (2018/10/20)

""" WS2812B driver module for the WiPy 3 board

This module provides a driver for the WS2812B. 
The library outputs a pulse train for a WS2812B LED chain using the RMT periphery of a Pycom board.
It is designed for driving large chains of LEDs using multiple GPIO pins.  
A list representing a color sequence can be set.
The length of the list is independed from the LED count and can have less or 
more elements than the number of LEDs.
The color sequence can be shifted to obtain a running light.

The module was designed for the pycom WiPy 3 module.

Example:
    The WS2812B driver can be used as follows:

    .. code-block:: html
        :linenos:

        ws2812b = chain(100, gpio_pin='P22')

        led_seq = [[127, 0, 0], [0, 127, 0], ...]
        ws2812b.set_seq(led_seq)
        ws2812b.output_buffer()

        ws2812b.shift_buffer()
        ws2812b.output_buffer()

"""

from machine import RMT
from machine import Pin
import utime

# See datasheet (https://cdn-shop.adafruit.com/datasheets/WS2812B.pdf) for time constants
T0H = 4 # 400ns
T0L = 9 # 900ns

T1H = 8 # 800ns
T1L = 5 # 500ns

TRST = 5000 # 50us

# Timings for transmitting binary 0
T0 = [T0H, T0L]
# Timings for Transmitting binary 1
T1 = [T1H, T1L]

class chain:
    """Represents a WS2812 LED chain.
	
    Args:
        led_count (int): Number of LEDs in the chain
        gpio_pin (string, optional): GPIO pin of the chain (Default pin: P22)
	
    """

    # Constructor used to initialize the internal variables
    def __init__(self, led_count, gpio_pin='P22'):
        # Create RMT instance and set idle level to 0
        self.led_count = led_count
        self.gpio_pin = gpio_pin
        # This module uses the RMT peripheral to output a pulse train
        # See https://docs.pycom.io/tutorials/all/rmt, https://docs.pycom.io/firmwareapi/pycom/machine/rmt
        self.rmt = RMT(channel=3, gpio=gpio_pin, tx_idle_level=0)
        self.timing_buffer = None
        self.seq_buffer = None
        self.seq_buffer_len = 0
        self.shift_pos = 0

    
    def set_seq(self, led_seq):
        """Set the LED sequence pattern for the LED chain.

		Args:
			led_seq (list([int, int, int])): List of LED sequence pattern. Each Entry has three sub entries (R, G, B).
		
        Example:
            .. code-block:: html
                :linenos:

                chain.set_seq([ [255, 0, 0], [0, 255, 0], [0, 0, 255] ])
		
        """
        # check of data is list
        if  isinstance(led_seq, list):
            self.seq_buffer = led_seq
            self.shift_pos = 0
            self.seq_buffer_len = len(led_seq)
            self.convert_seq()
        else:
            # reset internal data on error
            self.seq_buffer = None
            self.timing_buffer = None
            self.shift_pos = 0
            self.seq_buffer_len = 0
            self._printHelp("Argument led_seq is not a list!")
    
    def shift_buffer(self):
        """Shift the output buffer. The LED sequence pattern is shifted by one.

        Example:
            .. code-block:: html
                :linenos:

                chain.shift_buffer()

        """

        if self.timing_buffer is not None:
            # increment shift pos and reset if at end
            self.shift_pos = self.shift_pos + 1
            if self.shift_pos >= self.seq_buffer_len:
                self.shift_pos = 0
            # cut off first 48 entries (3(R/G/B)x8(Bits)x2(High/Low)) and convert the next LED from seq. buffer
            self.timing_buffer = self.timing_buffer[48:] + tuple(self.convert_step(self.seq_buffer[self.shift_pos]))
    
    def output_buffer(self):
        """Outputs the timing buffer.

        Example:
            .. code-block:: html
                :linenos:

                chain.output_buffer()

        """    

        # Output timing buffer
        if self.timing_buffer is not None:
            timing_complete = self.timing_buffer + (TRST, )
            self.rmt = RMT(channel=3, gpio=self.gpio_pin, tx_idle_level=0)
            self.rmt.pulses_send(timing_complete, start_level=RMT.HIGH)
            self.rmt.deinit()

    # internal function
    # convert one LED of the sequence from RGB to High/Low timing
    def convert_step(self, led):
        timing = []
        # loop through all 8 bits of the value for green hue
        # MSB first: bit 7 -> bit 6 -> ... bit 0
        for j in range(7,-1,-1): # green
            # check for bit
            if(led[1]&(1<<j) != 0):
                # append timing for a logic 1
                timing.extend(T1)
            else:
                # append timing for a logic 0
                timing.extend(T0)
        for j in range(7,-1,-1): # red
            if(led[0]&(1<<j) != 0):
                timing.extend(T1)
            else:
                timing.extend(T0)
        for j in range(7,-1,-1): # blue
            if(led[2]&(1<<j) != 0):
                timing.extend(T1)
            else:
                timing.extend(T0)
        return timing

    # internal function
    # converts the whole LED pattern from RGB to High/Low timing
    def convert_seq(self):
        timing = []
        seq_len = len(self.seq_buffer)
        # loop through all LEDs of the chain
        for i in range(0, self.led_count):
            # get color values for the LED position, restart if more LEDs than sequence entries
            led = self.seq_buffer[(i%seq_len)]
            # check if entry is a list
            if not isinstance(led, list):
                print("Child of sequence buffer is not a list. Ignoring.")
                pass
            # check if list has 3 entries
            if len(led) != 3:
                print("Child of sequence buffer has not 3 elements (R, G, B) Ignoring.")
                pass
            # Convert RGB list entry to RMT timing
            timing.extend(self.convert_step(led))
        # convert list to tuple (RMT periphery expects tuple)
        self.timing_buffer = tuple(timing)

    # internal function
    def _printHelp(self, msg):
        print(msg + ' ex.:')
        print('colorValues = [\n\t[led1_r, led1_g, led1_b], '
            '[led2_r, led2_g, led2_b], ... ]')

# test sensor in case the module is directly executed by python
if __name__ == "__main__":
    ws2812b = chain(4, gpio_pin='P22')

    led_seq = []
    led_brightness = 64
    step_size = 2

    for i in range(step_size-1, led_brightness, step_size):
        led_seq.append([led_brightness-1, i, 0])
    for i in range(step_size-1, led_brightness, step_size):
        led_seq.append([led_brightness-1-i, led_brightness-1, 0])
    for i in range(step_size-1, led_brightness, step_size):
        led_seq.append([0, led_brightness-1, i])
    for i in range(step_size-1, led_brightness, step_size):
        led_seq.append([0, led_brightness-1-i, led_brightness-1])
    for i in range(step_size-1, led_brightness, step_size):
        led_seq.append([i, 0, led_brightness-1])
    for i in range(step_size-1, led_brightness, step_size):
        led_seq.append([led_brightness-1, 0, led_brightness-1-i])

    #led_seq = [[127, 0, 0], [0, 127, 0], [0, 0, 127], [63, 0, 63], [0, 63, 63], [63, 63, 0], [31, 31, 31]]

    #led_seq = [[127, 0, 0], [0, 127, 0]]

    ws2812b.set_seq(led_seq)
    ws2812b.output_buffer()

    while True:
        ws2812b.shift_buffer()
        ws2812b.output_buffer()
        utime.sleep_ms(50)
