import os
import re
import sys
import shutil
import colorsys
import subprocess
import argparse
from pathlib import Path
import configparser


sys.path.insert(0,'Python-ALUP')
import importlib  
# import the main ALUP library
Device = getattr(importlib.import_module("Python-ALUP.src.Device"), "Device")
#from Python-ALUP.src.Device import Device
# import command definitions
Command = getattr(importlib.import_module("Python-ALUP.src.Frame"), "Command")
#from Python-ALUP.src.Frame import Command
#from Python-ALUP.src.Frame import Frame
Frame = getattr(importlib.import_module("Python-ALUP.src.Frame"), "Frame")


# note: make sure, alsa is configured accordingly and loopback devices are active

###############################
# Plan:
# 1. Connect to ALUP, get config data
# 1.5 create temporary fifo file 
# 2. Create custom cava config with bars = num_leds
# 3. Launch cava instance with custom config and output to fifo file
# 4. read cava binary data from fifo
# 5. partition data to led brightness and send data to alup
###############################


# future goals:
# custom configuration (cmdline argument) todo: test and fix
# different effects 
# import custom effects from external effects python file

# path to the cava tmp folder
#TMP_DIRECTORY = tempfile.gettempdir() + "/cava" 
TMP_DIRECTORY = Path("./tmp")
# COM Port of the arduino
# on windows: COMxx
# on linux: /dev/ttyUSBx
COM_PORT = "/dev/ttyUSB0"
BAUD_RATE = 115200

parser = argparse.ArgumentParser(prog='ALUP Audio Visualizer',
                                 description='Audio Visualization for addressable LEDs using CAVA and ALUP')

# todo: implement args:
parser.add_argument('-c', '--config', action='store', nargs=1, type=Path, help="Specify a custom CAVA configuration to use for visualization.\nIf not set, a copy of the configuration at %s will be generated to the tmp folder and automatically adjusted" % ((Path(__file__).parent.resolve() / "cava_config").resolve()))
parser.add_argument('-t', '--tmp', action='store', nargs=1, type=Path, help="Specify a tmp directory to store temporary files in. Default is %s" % (TMP_DIRECTORY.resolve()))
parser.add_argument('-C', '--com_port', action='store', nargs=1, help="Specify the COM port where the Arduino Serial is connected.\nIf not set, %s will be used" % (COM_PORT))
parser.add_argument('-b', '--baud', action='store', nargs=1, type=int, help="Specify the baud rate of the Arduino Serial connection.\nIf not set, %d will be used" % (BAUD_RATE))
# future feature
#parser.add_argument('-e', '--effect', action='store', nargs=1, type=Path, help="Specify a custom effects python file.\nIf not set, %s will be used" % (BAUD_RATE))


# these values need to be the same as in the cava config
# todo: automatically read from config file ? (see example)
#cava_config_path = "/home/pi/.config/cava/visualizer_config"
bit_format = 8  # set sample size (8bit or 16bit) according to CAVA config
bars = 0        # this should be automatically set to the number of leds reported by alup

# create ALUP Device
arduino = Device()

def main():
    global TMP_DIRECTORY
    global COM_PORT
    global BAUD_RATE

    # todo: maybe write defaults into parser arguments instead?
    # this would obsolete those checks
    # parse cmdline arguments
    args = parser.parse_args()
    # update tmp directory path if cmdline arg is given
    if (not args.tmp is None):
        TMP_DIRECTORY = args.tmp
        print("Using custom tmp directory: " + str(TMP_DIRECTORY.resolve()))
    if (not args.com_port is None):
        COM_PORT = args.com_port
        print("Using custom COM Port: " + str(COM_PORT))
    if (not args.baud is None):
        BAUD_RATE = args.baud
        print("Using custom Baud Rate: " + str(BAUD_RATE))

    print("Connecting to Serial ALUP at %s, %d" % (COM_PORT, BAUD_RATE))
    # Connect to ALUP
    arduino.SerialConnect(COM_PORT, BAUD_RATE)
    # ALUP connection status is currently untracked in python-alup (bruh)

    # create tmp folder if non-existent
    Path(TMP_DIRECTORY).mkdir(parents=False, exist_ok=True)
    print("Made sure tmp folder at " + str(TMP_DIRECTORY.resolve()) + " exists")
    # clear tmp folder 
    #ClearDirectory(TMP_DIRECTORY) # temporarily disabled to do rm -rf concerns (high risks)
    # create temporary fifo
    fifo_path = CreateFifo(TMP_DIRECTORY)
    print("Created fifo at " + str(fifo_path.resolve()))

   
    # read in config cmdline argument if present
    config_path = Path(__file__).parent.resolve() / "cava_config"
    modified_config_path =  TMP_DIRECTORY.resolve() / "cava_tmp_config"

    if(not args.config is None):
        config_path = args.config[0]
        print("Using custom config: "+ str(config_path))

    # customize the CAVA configuration
    config = configparser.ConfigParser()
    config.read(config_path)
    ConfigureCAVA(config, arduino, fifo_path)
    with open(modified_config_path, 'w') as modified_config_file:
        config.write(modified_config_file)

    print("Saved modified config to " + str(modified_config_path.resolve()))


    bars = arduino.configuration.ledCount

    print("Running CAVA with config " + str(config_path))
    # Start Cava with created config
    cava_process = subprocess.Popen(["cava","-p", str(config_path.resolve())])

    print("Running visualizer...")
    # read from fifo file

    # todo: this does currently not work as expected
    # it should:
    # - read <bars> bytes from the fifo and then send them to ALUP
    # loop
    with open(fifo_path, mode="rb") as input_file:
        try:
            while(True):
                frame = Frame()
                # copy each bar from the fifo to the alup Device
                for i  in range(bars): 
                    # read next sample from fifo
                    bytes_sample = input_file.read(int(bit_format/8))
                    sample = int.from_bytes(bytes_sample, "little", signed=False)

                    #print("Received sample " + str(sample))

                    # ---------- plan for effects: ---------------
                    # add variable effect function generating array of 24bit color values for leds
                    color = Effect(i, arduino.configuration.ledCount, sample)
                    # add visualizer function to change brightness of each 8bit led color depeding on visualizer
                    color = AdjustBrightness(color, sample)
                    # set color to led  (colors are stored together in 24bit int as 0xrrggbb)     
                    arduino.frame.colors.append(color)
                # send led frame
                #print("sending next frame...")
                # todo: this is hanging with more than 10 leds 
                arduino.Send()
        except KeyboardInterrupt as e:
            #cleanup
            print("Ctl-C pressed")
            print("Cleaning up...")
            # remove fifo 
            print("Deleting FIFO at " + str(fifo_path.resolve()))
            os.remove(fifo_path)
            print("Disconnecting ALUP...")
            arduino.SetCommand(Command.CLEAR)
            arduino.Send()
            arduino.Disconnect()
    print("Done.")


# geneate a rainbow color
# @param i: the hue for the geneated color, in range [0.0, 1.0]
# @return: the 24bit hsv color
def RainbowColor(i):
    # get hsv color as rgb array
    color_array = colorsys.hsv_to_rgb(i, 1.0, 1.0)
    # scale array to range [0,255] and combine to hex color
    color = int(color_array[0] * 255)
    color = color << 8
    color += int(color_array[1] * 255)
    color = color << 8
    color += int(color_array[2] * 255)
    return color

# effect applied to the leds with all values which might be useful to generate an effect
# @param currentLed: the index of the led this color will correspond to
# @param ledCount: the total number of Leds
# @param sample: the current visualizer sample 
#                Note: no need to apply the visualizer effects here, this is done in 'AdjustBrightness(...)'
# returns a 24bit color value in the format 0xrrggbb
def Effect(currentLed, ledCount, sample):
    return RainbowColor(currentLed/ledCount)


# returns the given 24bit color with the given 8 bit brightness
def AdjustBrightness(color, brightness):
    # extract the different base colors from the 24bit color
    # using bitshifts and a bitmask
    r = (color >> 16) & 0xFF
    g = (color >> 8) & 0xFF
    b = color & 0xFF
    # scale colors according to brightness
    r = int(r * brightness/255.0)
    g = int(g * brightness/255.0)
    b = int(b * brightness/255.0)
    # reassemble as 24bit color
    color = r
    color = color << 8
    color += g
    color = color << 8
    color += b
    return color

    

# remove all contents in directory recursively
def ClearDirectory(folder):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))
    
def CreateFifo(folder):    
    fifo_path = folder / "fifo"
    # create fifo file if not exists
    if not os.path.exists(fifo_path):
        os.mkfifo(fifo_path)

    return fifo_path


# modify the given CAVA configuration to work with the visualizer
# @param config: the configparser object containing the CAVA config
# @param device: the ALUP device
# @param fifo_path: the path to the fifo file
# @return the modified config
def ConfigureCAVA(config, device, fifo_path):
    print('Setting output method to raw')
    config['output']['method'] = 'raw'
    print('Setting number of bars to %d' % (device.configuration.ledCount))
    config['general']['bars'] = str(device.configuration.ledCount)
    print('Setting raw output target to %s' % (str(fifo_path.resolve())))
    config['output']['raw_target'] = str(fifo_path.resolve())
    return config



if __name__ == "__main__":
    main()
