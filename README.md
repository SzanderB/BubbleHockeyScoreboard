# Project Title: Bubble Hockey Scoreboard
Custom manufactured Bubble Hockey (or any goal related game) Scoreboard from schematic to case!
This includes Version 1 (just PCB for a class) and Version 2 (changed design and fully built out to finished product)

Video link: https://youtu.be/nwzQTY0Y3hk

## Description
Fully custom scoreboard. It will automatically tally points when puck goes through the net, play audio corresponding to events in the game, select different game modes to play, such as to a set score or time limit. Version 2 also controls external LEDs for ambiance and light, and finally is containied in a easily modifiable and removable box that mounts to the table.

## Purpose
My bubble hockey table's scoreboard was broken, and I wanted it not to be broken. Also, I wanted to try my hand at more complex builds that required total level of thinking, from PCB design to mechanical placement. This project taught me that it's pretty easy to design a system in one lens, for example, the schematic and PCB are easy. However, when it comes to combining them with the mechanical design, things get much more challenging. Deciding where to place components to hae the smallest or most effective routing battles with how the board can be mounted or enclosed. Having to learn CAD while doing this as also a fun challenge that I tackled.

## Methods
Both versions are controlled by a Raspberry Pi Pico 2.

Version 1 uses and LCD screen for the Display, LED indicators on the board for players and goals, an external DAC to drive a speaker, some buttons and potentiometers for inputs (volume and game select), as well as beam break sensors to detect goals. I decided on these components because the class requirements included most of these, but it all changed in V2.
Version 2 uses a MAX7219 to control 8 common cathode seven segment displays with only 1 SPI port. It uses the NeoPixel LEDs and the FastLED library to control the external LEDs. Lastly, it uses a DFPlayer Mini MP3 player and amp to generate the audio. It has a start and select button, switches for power for both the scoreboard and the lights, and a potentiometer for volume.
Version 2 also has a 3D printed case. There are daughterboards for each interactable component (switches, buttons, pot) with individual mounting holes and standoffs in the case. They are connected with Molex connectors for easy assembly and disassembly (god knows I needed that).
There is a hole for mounting the barrel jack connector, as well as holes for easy access to Pico and DFPlayer mini's mp3 slot. This adds to it being able to be worked on while being fully built.

## Issues
This project isn't perfect. For one, the 3D model could be better. The speaker hole didn't really fit my speaker, and so I had to cut and shave away extra filament. The button holes didn't quite fit and had to be widened as well. On the code side, most everything works as desired. If I had to redo it again, I'd connect the switch for the lights directly to a GPIO pin so it can detect rising/high state, so I can automatically know to turn on the lights. Instead, you have to switch them on and click the select button. Overall though, it works as intended. It is mounted and fully usable, easily powered and operated.

