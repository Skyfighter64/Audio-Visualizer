import subprocess
import time
import os
import shutil
from pathlib import Path
import tempfile
import sys
sys.path.insert(0,'Python-ALUP')
# import the main library
import importlib  
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
# multiple devices / multiple instances
# different effects 
# udp/wifi support

# also see: https://github.com/karlstav/cava/issues/123#issuecomment-307891020

# path to the cava tmp folder
TMP_DIRECTORY = tempfile.gettempdir() + "/cava"
# COM Port of the arduino
COM_PORT = "COM9"
BAUD_RATE = 115200
# these values need to be the same as in the cava config
# todo: automatically read from config file ? (see example)
cava_config_path = "/home/pi/.config/cava/visualizer_config"
bit_format = 8 # set sample size (8bit or 16bit) according to CAVA config
bars = 10       # this should be automatically set to the number of leds reported by alup

# create ALUP Device
arduino = Device()

def main():
    print("Connecting to Serial ALUP at %s, %d", (COM_PORT, BAUD_RATE))
    # Connect to ALUP
    arduino.SerialConnect(COM_PORT, BAUD_RATE)
    # ALUP connection status is currently untracked in python-alup (bruh)

    # create tmp folder if non-existent
    Path(folder).mkdir(parents=False, exist_ok=True)
    print("Made sure tmp folder at " + folder + " exists")
    # clear tmp folder 
    #ClearDirectory(TMP_DIRECTORY) # temporarily disabled to do rm -rf concerns (high risks)
    # create temporary fifo
    fifo_path = CreateFifo(TMP_DIRECTORY)
    print("Created fifo at " + fifo_path)

    # Create custom config 
    config_path = CreateCavaConfig(arduino.configuration.ledCount, TMP_DIRECTORY, fifo_path)
    print("Saved custom config to " + config_path)


    print("Running CAVA with config " + config_path)
    # Start Cava with created config
    cava_process = subprocess.Popen(["cava","-p", config_path])

    print("Running visualizer...")
    # read from fifo file
    with open(fifo_path, mode="rb") as input_file:
        while(True):
            frame = Frame()
            # copy each bar from the fifo to the alup Device
            for i  in range(bars): 
                # read next 8 bit from fifo
                sample = input_file.read(int(bit_format/8))
                # set color to led
                # todo: does this work or does this need to be specifically hex?                
                arduino.frame.colors.append(sample)
            # send led frame
            arduino.Send()

    print("Done.")


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
    fifo_path = folder + "/fifo"
    # create fifo file if not exists
    if not os.path.exists(fifo_path):
        os.mkfifo(fifo_path)

    return fifo_path


# replace the first occurence of the matching regex with the contents of replacement_line
# in the given array of strings or appends it to the end if no match is found
# returns the number of replaced lines
def ReplaceLine(lines, regex, replacement_line):
    pattern = re.compile(regex, re.MULTILINE)
    occurences = 0
    for line in lines:
        if pattern.match(line):
            line = replacement_line
            occurences += 1
    
    print("Replaced " + str(occurences) + " line(s) with \"" + replacement_line + "\"")

    if(occurences is 0):
        lines.append(replacement_line)
        print("No match found for regex \"" + str(regex) + "\". Appended line \"" + replacement_line + "\" at the end of file")


def CreateCavaConfig(num_leds, tmp_dir, fifo_path):
    # get the preconfigured config from the same folder as the script
    default_config_path = Path(__file__).parent.resolve() + "/cava_config"
    tmp_config_path =  Path(__file__).parent.resolve() + "/cava_tmp_config"

    # read default config
    with open(default_config_path, "r") as file:
        config_lines = file.readlines()

    # change bars to num_leds
    ReplaceLine(config_lines, regex = r"^ ?;? ?bars ?= ?[0-9]+ ?$", replacement_line = "bars = " + str(num_leds))
    # set fifo target file to fifo path
    ReplaceLine(config_lines, regex = r"^ ?;? ?raw_target ?= ?.* ?$", replacement_line = "raw_target =" + str(fifo_path))
    
    # paste into new custom config file
    with open(tmp_config_path, "w+") as output_file:
        output_file.writelines(lines)

    # return path of custom config 
    return tmp_config_path


"""      
# clear terminal 
    os.system('clear')

    # read from fifo file
    with open(fifo_path, mode="rb") as input_file:
        while(True):
            #os.system('clear')
            print("\033[3J\033[H", end="")
            print("Next Frame:")
            for i  in range(bars): 
                sample = input_file.read(int(bit_format/8))
                drawBar(int.from_bytes(sample, byteorder="big", signed=False))
                #print(sample)

def drawBar(value):
    #print(value)
    print("=" + ("=" * (value//20)) + (" " * ((255-value)//20)))
 """       



if __name__ == "__main__":
    main()
