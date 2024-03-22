# Audio-Visualizer
An audio visualizer for my Raspberry Pi which combines Addressable LEDs and the [CAVA Audio Visualizer](https://github.com/karlstav/cava) by using an Arduino with [ALUP](https://github.com/Skyfighter64/ALUP) and a custom ALSA Configuration.

# Requirements
- Raspberry Pi to play Audio (any other linux system will probably work)
- [CAVA Audio Visualizer](https://github.com/karlstav/cava)
- Audio Loopback device enabled (usually via `sudo modprobe snd-aloop`)
- Arduino connected via USB and [Arduino-ALUP](https://github.com/Skyfighter64/Arduino-ALUP) configured and running

# Install
Use this to clone the repo and also clone the [Python-ALUP](https://github.com/Skyfighter64/Python-ALUP) submodule
`git clone --recurse-submodules https://github.com/Skyfighter64/Audio-Visualizer`
or
`git clone https://github.com/Skyfighter64/Audio-Visualizer`
`cd Audio-Visualizer`
`git submodule update --init`

# Configuration
todo
also todo: make setup guide to set up alsa config, soundcards, loopback devices and custom cava configs 
