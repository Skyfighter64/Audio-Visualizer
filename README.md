# Audio-Visualizer
An audio visualizer for my Raspberry Pi which combines Addressable LEDs and the [CAVA Audio Visualizer](https://github.com/karlstav/cava) by using an Arduino with [ALUP](https://github.com/Skyfighter64/ALUP) and a custom ALSA Configuration.

# Requirements
- Spotify Premium access
- Raspberry Pi to play Audio (any other linux system will probably work)
- [CAVA Audio Visualizer](https://github.com/karlstav/cava)
- Audio Loopback devices (usually via `sudo modprobe snd-aloop`)
- Arduino connected via USB and [Arduino-ALUP](https://github.com/Skyfighter64/Arduino-ALUP) configured and running

## Spotify Premium and alternative audio sources
In order to use spotify connect, a Spotify Premium account is required.
If you want to stream from other audio sources, it is also possible (like bluetooth devices or Raspberry Pi system sounds). See section "Other audio sources".

However, this setup does currently only include a guide for Raspotify. If you want to use other audio sources, just make sure to set the audio output device of the other programs to `pbnrec` in their respective configuration and ignore the Raspotify section. Everything else should stay the same.


# Install
Use this to clone the repo and also clone the [Python-ALUP](https://github.com/Skyfighter64/Python-ALUP) submodule:\
`git clone --recurse-submodules https://github.com/Skyfighter64/Audio-Visualizer`\
or
- `git clone https://github.com/Skyfighter64/Audio-Visualizer`
- `cd Audio-Visualizer`
- `git submodule update --init`

# Setup
This section explains how to set up the different components needed.
## CAVA
We need to edit the cava default configuration at `~/.config/cava/config` for the visualizer displayed in the commandline when calling `cava` without any arguments. (This is theoretically optional, but used later for testing the ALSA config. Only skip if you know what you're doing)
- open `~/.config/cava/config`
- in section `[input]` disable all input methods except `method = alsa`
- set the source beneath to `source = loopout`

It should look something like this:
```
...

; method = pulse
; source = auto

; method = pipewire
; source = auto

# this is the important part:
method = alsa
source = loopout

; method = fifo
; source = /tmp/mpd.fifo

...

```
Everything else can be configured as you like.

## ALSA
- Backup your current `/etc/asound.conf` config file
- Copy the provided `asound.conf` to `/etc/asound.conf`

To configure your sound card:
- Open the file in a text editor navigate to:
```
...

ctl.usbSound
{
    type plug;
    slave.pcm plughw:Device;
}

# redirect to usb soundcard (without additional plug)
# this is needed for the pbnrec plug which conflicts if two plugs (pbnrec, usbSound) are used in the same stream
pcm._usbSound
{
    type empty;
    slave.pcm plughw:Device;
}

...
```
- Change `plughw:Device;` to the name of your desired audio output device. (All devices can be listed with `aplay -l`)  

## Audio Loopback
Start the audio loopback kernel module:\
`sudo modprobe snd-aloop`

You will now see loopback devices when running `aplay -l`.\
This needs to be done every time the system reboots.\

To load this module automatically on system boot:
- open `/etc/modules-load.d/modules.conf`
- add `snd-aloop` to the bottom of the file 


## Test your ALSA setup
You can now test if your audio setup is working correctly:
- run `cava` in your terminal (this uses the default config at `~/.config/cava/config` which was set up previously)
- :warning: The next step will play audio, adjust your device volumes to appropriate leves beforehand.
- in another terminal, run `aplay /usr/share/sounds/alsa/Front_Center.wav --device=pbnrec` to play a test audio file

You should now hear the audio on your speakers AND see `cava` react to the audio.\
If not, something is not set up correctly. Check your config files and make sure the loopback devices are running.
### Troubleshooting:
- Use `aplay /usr/share/sounds/alsa/Front_Center.wav --device=usbSound` to to test only your speakers. If you can't hear anything, see the ALSA setup above on how to set the correct sound card for output.
- If cava is not responding to the sounds:
    - try changing the cava sensitivity and number of bars by using the arrow keys 
    - make sure loopback devices are shown when running `aplay -l`. See Audio Loopback setup.
    - see the CAVA setup section again on how to set the audio input for CAVA


## Raspotify
We need to set the output of raspotify to the `pbnrec` device created previously in asound.conf:
- Change the `ExecStart` parameter in `/usr/lib/systemd/system/raspotify.service`
to: `ExecStart=/usr/bin/librespot --backend alsa --device pbnrec`
- save and restart raspotify (`sudo systemctl restart raspotify`)
(It might also work to set it in the config at `/etc/raspotify/conf`)

## Other audio sources
It is possible to use other sources of audio (eg. Bluetooth / Browser / System Sounds / other music player), which need to be configured separately.

If you are using another source than Raspotify for playing audio, make sure to set the input method to use alsa and the output device to `pbnrec` ("playback and record").

If this is not an option, you can also try setting the `pbnrec` as default sink in `/etc/asound.conf`. This will output all sounds which have no special output configured to the visualizer and your configured sound card.

### Testing Raspotify
- You should now be able to connect to `Raspotify` inside your spotify app on your phone or computer.
- If you play any song while connected, you should now hear it over your speakers and see the visualizer doing its thing when running `cava` in your terminal.


## Arduino / ALUP
todo


# Configuration
todo: custom cava configs, multi instances, ...