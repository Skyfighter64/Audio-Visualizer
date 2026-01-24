import os
import re
import sys
import math
import shutil
import colorsys
import subprocess
import argparse
from pathlib import Path
import configparser
import logging


#sys.path.insert(0,'Python-ALUP')
#import importlib  
# import the main ALUP library
#Device = getattr(importlib.import_module("Python-ALUP.src.Device"), "Device")
#from Python-ALUP.src.Device import Device
# import command definitions
#Command = getattr(importlib.import_module("Python-ALUP.src.Frame"), "Command")
#from Python-ALUP.src.Frame import Command
#from Python-ALUP.src.Frame import Frame
#Frame = getattr(importlib.import_module("Python-ALUP.src.Frame"), "Frame")

from pyalup.Device import Device
from pyalup.Frame import Frame, Command
from pyalup.TcpConnection import TcpConnection
from pyalup.SerialConnection import SerialConnection
from pyalup.Group import Group

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

parser = argparse.ArgumentParser(prog='ALUP Audio Visualizer',
                                 description='Audio Visualization for addressable LEDs using CAVA and ALUP')

parser.add_argument('-c', '--config', action='store', nargs=1, type=Path, help="Specify a custom CAVA configuration to use for visualization.\nIf not set, a copy of the configuration at %s will be generated to the tmp folder and automatically adjusted" % ((Path(__file__).parent.resolve() / "cava_config").resolve()))
parser.add_argument('-t', '--tmp', action='store', nargs=1, type=Path, help="Specify a tmp directory to store temporary files in. Default is %s" % (TMP_DIRECTORY.resolve()))

parser.add_argument('--serial', nargs=1, action='append', default=[], help="Specify a serial connected ALUP device replacing the default device: [PORT]{:[BAUD]} eg: COM7:115200. Default Baud:115200. This argument can be specified multiple times")
parser.add_argument('--tcp', nargs=1, action='append', default=[], help="Specify a TCP connected ALUP device replacing the default device. Format: [ip]{:[PORT]} eg: 127.0.0.1:5012. Default Port: 5012. This argument can be specified multiple times")
parser.add_argument('-v', '--verbose', action='store_true', help="Enable verbose logging") 
parser.add_argument('--loglevel', default='INFO', help='Specify the minimum level for log messages (Either String or Int value). Possible log levels: NOTSET (0), DEBUG (10), INFO (20), WARNING (30), ERROR (40), CRITICAL (50). Default: INFO')

#parser.add_argument('-e', '--effect', action='store', nargs=1, type=Path, help="Specify a custom effects python file.\nIf not set, %s will be used" % (BAUD_RATE))


# these values need to be the same as in the cava config
# todo: automatically read from config file ? (see example)
#cava_config_path = "/home/pi/.config/cava/visualizer_config"
bit_format = 8  # set sample size (8bit or 16bit) according to CAVA config
bars = 100        # number of visualizer bars for the CAVA backend to generate; default: 100 

def main():
    global TMP_DIRECTORY
    global bars

    #
    #       Commandline Arg parsing and execution
    #

    # Initialize Logger
    logging.basicConfig(format="[%(asctime)s %(levelname)s]: %(message)s", datefmt="%H:%M:%S")
    # this would obsolete those checks
    # parse cmdline arguments
    args = parser.parse_args()
    # update tmp directory path if cmdline arg is given
    if (args.tmp is not None):
        TMP_DIRECTORY = args.tmp
        print("Using custom tmp directory: " + str(TMP_DIRECTORY.resolve()))
    if(args.verbose):
        SetLogLevel(logging.root, logging.DEBUG)
    # set the log level from arg, overriding verbose if given
    SetLogLevel(logging.root, args.loglevel)


    #
    #       ALUP Devices Setup and Connection
    #


    # read in one or more devices from command line arguments
    #TODO: use ALUP Groups???
    group = Group()
    for serial_device in args.serial:
        port, baud = SerialConnectionParametersFromString(serial_device[0])
        device = Device()
        device.SerialConnect(port, baud)
        group.Add(device)
        logging.info(f"Connected to Serial Device {port}:{baud}")
    for tcp_device in args.tcp:
            ip, port = TcpConnectionParametersFromString(tcp_device[0])
            device = Device()
            device.TcpConnect(ip, port)
            group.Add(device)
            logging.info(f"Connected to TCP Device {ip}:{port}")

    # complain if no devices were found at all
    if(len(group.devices) == 0):
        logging.error("No Devices specified. Specify devices in commandline arguments! See --help for more\nExiting.")
        exit()



    #
    #      CAVA Backend Initialization
    #


    # create tmp folder if non-existent
    Path(TMP_DIRECTORY).mkdir(parents=False, exist_ok=True)
    print("Made sure tmp folder at " + str(TMP_DIRECTORY.resolve()) + " exists")
    # clear tmp folder 
    #ClearDirectory(TMP_DIRECTORY) # disabled to do rm -rf concerns (high risks)
    # create temporary fifo
    fifo_path = CreateFifo(TMP_DIRECTORY)
    print("Created fifo at " + str(fifo_path.resolve()))

   
    # create temporary copy of config
    config_path = Path(__file__).parent.resolve() / "cava_config"
    modified_config_path =  TMP_DIRECTORY.resolve() / "cava_tmp_config"

    if(not args.config is None):
        config_path = args.config[0]
        print("Using custom config: "+ str(config_path))

    # customize the CAVA configuration
    config = configparser.ConfigParser()
    config.read(config_path)
    ConfigureCAVA(config, bars, fifo_path)
    # write into copy of config file
    with open(modified_config_path, 'w') as modified_config_file:
        config.write(modified_config_file)
    print("Saved modified config to " + str(modified_config_path.resolve()))


    # Start Cava with created config
    print("Running CAVA with config " + str(modified_config_path))
    cava_process = subprocess.Popen(["cava","-p", str(modified_config_path.resolve())])

    print("Running visualizer...")
    # read from fifo file

    # ----------------------------
    #       Run Visualizer
    # ----------------------------

    with open(fifo_path, mode="rb") as input_file:
        try:
            while(True):
                colors = []
                # copy each bar from the fifo to the alup Device
                for i  in range(bars): 
                    # read next sample from fifo (CAVA Backend)
                    #TODO: if needed, this can be done more efficiently
                    bytes_sample = input_file.read(int(bit_format/8))
                    sample = int.from_bytes(bytes_sample, "little", signed=False)
                

                    # generate base colors
                    color = Effect(i, bars)
                    # apply audio effects
                    color = AdjustBrightness(color, sample)
                    
                    colors.append(color)

                # send the colors to each device
                for device in group.devices:
                    # NOTE: for now only up to 100 LEDs, cutting off if a device has less
                    # TODO: stretch / interpolate for devices with more leds
                    device.SetColors(colors[:device.configuration.ledCount])
                
                # Send to every device asynchronously
                group.Send()
        
        except KeyboardInterrupt as e:
            #cleanup
            print("Ctl-C pressed")
            print("Cleaning up...")
            # remove fifo 
            print("Deleting FIFO at " + str(fifo_path.resolve()))
            os.remove(fifo_path)
            print("Disconnecting ALUP...")
            group.Clear()
            group.Disconnect()
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
# returns a 24bit color value in the format 0xrrggbb
def Effect(currentLed, ledCount):
    return RainbowColor(currentLed/ledCount)


# returns the given 24bit color with the given 8 bit brightness
def AdjustBrightness(color, brightness):
    # extract the different base colors from the 24bit color
    # using bitshifts and a bitmask
    r = (color >> 16) & 0xFF
    g = (color >> 8) & 0xFF
    b = color & 0xFF

    #brightness = Delinearize(brightness)

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

# square the given brightness for usage with 
# real leds; this is a direct consequence of the way
# humans perceive light
# @param brightness: the brightness integer value as [0-255]
# @return: the delinarized and resized brightness interger [0-255]
def Delinearize(brightness):
    #return pow(brightness, 2) / 255
    return math.sqrt(brightness* 255)
    

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
# @param bars: number of visualizer bars to generate
# @param fifo_path: the path to the fifo file
# @return the modified config
def ConfigureCAVA(config, bars, fifo_path):
    print('Setting output method to raw')
    config['output']['method'] = 'raw'
    print('Setting number of bars to %d' % (bars))
    config['general']['bars'] = str(bars)
    print('Setting raw output target to %s' % (str(fifo_path.resolve())))
    config['output']['raw_target'] = str(fifo_path.resolve())
    return config

# create an alup Serial connection from a string of connection parameters
# Format: [PORT]{:[Baud]}
# Default Baud: 115200
def SerialConnectionFromString(parameters : str):
    splitted = parameters.split(':')
    port = splitted[0]
    baud = int(splitted[1]) if len(splitted) > 1 else 115200
    return SerialConnection(port, baud)

# Parse the serial connection parameters from a string
# Format: [PORT]{:[Baud]}
# Default Baud: 115200
# @returns port, baud
def SerialConnectionParametersFromString(parameters : str):
    splitted = parameters.split(':')
    port = splitted[0]
    baud = int(splitted[1]) if len(splitted) > 1 else 115200
    return port, baud

# create an alup tcp connection from a string of connection parameters
# Format: [ip]{:[port]}
# Default port: 5012
def TcpConnectionFromString(parameters : str):
    splitted = parameters.split(':')
    ip = splitted[0]
    port = int(splitted[1]) if len(splitted) > 1 else 5012
    return TcpConnection(ip, port)


# parse the alup tcp connection parameters from a string 
# Format: [ip]{:[port]}
# Default port: 5012
# @returns: ip, port
def TcpConnectionParametersFromString(parameters : str):
    splitted = parameters.split(':')
    ip = splitted[0]
    port = int(splitted[1]) if len(splitted) > 1 else 5012
    return ip, port

def SetLogLevel(logger : logging.Logger, level):
    """Set the log level.
    Usage: loglevel [level]
    @param level: the log level to set (int or string).
    Possible log levels:
        NOTSET (0)
        PHYSICAL (5)
        DEBUG (10)
        PROTOCOL (15)
        INFO (20)
        WARNING (30)
        ERROR (40)
        CRITICAL (50)
    """
    # set the new log level
    try:
        logger.setLevel(TryStrToInt(level))
    except ValueError:
        print("Unknown Log Level: " + str(level))

def TryStrToInt(text : str):
    """
    Try to convert a given text to an interger.
    If not possible, return the original text

    """
    try:
        return int(text)
    except ValueError:
        return text


if __name__ == "__main__":
    main()
