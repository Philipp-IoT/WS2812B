# MicroPython Driver for the WS2812B RGB LED Controller

This module provides a driver for the WS2812B. 
The library outputs a pulse train for a WS2812B LED chain using the RMT periphery of a Pycom board.
It is designed for driving large chains of LEDs using multiple GPIO pins.  
A list representing a color sequence can be set.
The length of the list is independed from the LED count and can have less or 
more elements than the number of LEDs.
The color sequence can be shifted to obtain a running light.

The module was designed for the pycom WiPy 3 module.

## Readme

The documentation was done using Sphinx. All documentation source files are located in the docs folder.
I've hosted the compiled documentation of Read The Docs. 

[WS2812B on ReadTheDocs.IO](https://ws2812b.readthedocs.io)

