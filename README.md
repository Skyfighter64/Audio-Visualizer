# Audio-Visualizer
An audio visualizer for my Raspberry Pi which combines Addressable LEDs and the [CAVA Audio Visualizer](https://github.com/karlstav/cava) by using an Arduino with [ALUP](https://github.com/Skyfighter64/ALUP) and a custom ALSA Configuration.


# Demo
Sorry for the bad quality :>\
https://www.youtube.com/watch?v=6K1Sigc1xIU

# Requirements
- Spotify Premium access
- Raspberry Pi to play Audio (any other linux system will probably work)
- [CAVA Audio Visualizer](https://github.com/karlstav/cava)
- Audio Loopback devices (usually via `sudo modprobe snd-aloop`)
- Arduino connected via USB and [Arduino-ALUP](https://github.com/Skyfighter64/Arduino-ALUP) configured and running

## Spotify Premium and alternative audio sources
In order to use spotify connect, a Spotify Premium account is required.
If you want to stream from other audio sources, it is also possible (like bluetooth devices or Raspberry Pi system sounds). See below for more.

# Install
Use this to clone the repo and also clone the [Python-ALUP](https://github.com/Skyfighter64/Python-ALUP) submodule:\
`git clone --recurse-submodules https://github.com/Skyfighter64/Audio-Visualizer.git`\
or
- `git clone https://github.com/Skyfighter64/Audio-Visualizer.git`
- `cd Audio-Visualizer`
- `git submodule update --init`

# Setup
This section explains how to set up the different components needed so audio coming from different sources
can be visualized while playing to speakers.
## CAVA
We need to edit the cava default configuration at `~/.config/cava/config` for the visualizer displayed in the commandline when calling `cava` without any arguments. (This is theoretically optional, but used later for testing the ALSA config. Only skip if you know what you're doing)
- open `~/.config/cava/config`
- in section `[input]` disable all input methods except `method = alsa`
- set the source beneath to `source = loopout`

It should look something like this:
```
...
[input]
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
A default config file with all possible parameters can be found here: https://github.com/karlstav/cava/blob/master/example_files/config

## ALSA
- Backup your current `/etc/asound.conf` config file
- Copy the provided `asound.conf` to `/etc/asound.conf`

To configure your sound card:
- Open `/etc/asound.conf` in a text editor and navigate to:
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


---------------------------------------------------
# Play Music from sources
There are different ways to play music. In general, any audio source can be used as long as its audio output is set to the `pbnrec` ALSA audio device. If you want all audio to be visualized, you may also just declare `pbnrec` as the default audio device in your `asound.conf` as follows:

```
pcm.!default 
{   
    type plug;
    #slave.pcm _usbSound; # usb soundcard as default output
    slave.pcm pbnrec;	# pbnrec as default output
}
```

Here are some of my favorite ways to play audio:

## RPI Audio Receiver:
This is the easiest way to get Raspotify (Spotify Connect), Bluetooth Audio and AirPlay 2 on your Raspberrry Pi (needs latest Raspberry Pi OS)

https://github.com/nicokaiser/rpi-audio-receiver

Use the installer script to set up the different methods, then follow the guides below for every installed method to change the audio device to the right output.

### Configure Raspotify
We need to set the output of raspotify to the `pbnrec` device created previously in asound.conf:
- Run ` sudo systemctl edit raspotify.service` to open the configuration in a text editor
Change its contents to:
```
### Editing /etc/systemd/system/raspotify.service.d/override.conf
### Anything between here and the comment below will become the new contents of the file

[Service]
ExecStart=
ExecStart=/usr/bin/librespot --backend alsa --device pbnrec

### Lines below this comment will be discarded
   ```
- Restart raspotify: `sudo systemctl restart raspotify`

The spotify connect audio should now play via the speakers and be visible in CAVA
(It might also work to set it in the config at `/etc/raspotify/conf`)

#### Testing Raspotify
- You should now be able to connect to `Raspotify` inside your spotify app on your phone or computer.
- If you play any song while connected, you should now hear it over your speakers and see the visualizer doing its thing when running `cava` in your terminal.


### Configure Bluez-aplay
This bluetooth audio player plays anything sent from connected bluetooth devices.
To configure the output, edit the systemd file for the `bluealsa-aplay` service:
- use `sudo systemctl edit bluealsa-aplay.service`, and paste in the following lines:
```
### Editing /etc/systemd/system/bluealsa-aplay.service.d/override.conf
### Anything between here and the comment below will become the new contents of the file

# $ sudo systemctl edit bluealsa-aplay
[Service]
ExecStart=
ExecStart=/usr/bin/bluealsa-aplay --pcm=pbnrec

### Lines below this comment will be discarded
```
- restart bluez-aplay: `sudo systemctl restart bluealsa-aplay.service`
- check if it is running successfully: `sudo systemctl status bluealsa-aplay.service`

__Note:__
CAVA may not work if pipewire and wireplumber are running as wireplumber automatically takes the bluetooth audio stream and routes it to the speaker.
To fix this, you need to disable wireplumber or configure the routing to pbnrec in wireplumber.

To disable Wireplumber: 
- `systemctl --user disable wireplumber.service`
- `systemctl --user mask wireplumber.service`
- `systemctl --user stop wireplumber.service`
 __WARNING:__ This will break any other Software which uses pipewire/Wireplumber for audio. If you still need it, you can try disabling bluetooth in the wireplumber configuration.
To undo:
- `systemctl --user unmask wireplumber.service`
- `systemctl --user enable wireplumber.service`
- `systemctl --user start wireplumber.service`

### Line In / Mic In
Todo

### Other audio sources
As said, is possible to use other sources of audio (eg. Bluetooth / Browser / System Sounds / other music player / Microphone (?)), which need to be configured separately.

If you are using another source than Raspotify for playing audio, make sure to set the input method to use alsa and the output device to `pbnrec` ("playback and record").

If this is not an option, you can also try setting the `pbnrec` as default sink in `/etc/asound.conf` as described earlier. This will output all sounds which have no special output configured to the visualizer and your configured sound card.


## Arduino / ALUP
todo


# Configuration
The audio visualizer overrides the following parameters of the specified CAVA configuration in order to work properly:
```
[general]
bars = <alup led count>
[output]
 method = raw
 raw_target = <path to fifo>
```
todo: custom cava configs, multi instances, ...
