import subprocess
import time
import os
from pathlib import Path
# import the main library
from Python-ALUP.src.Device import Device
# import command definitions
from Python-ALUP.src.Frame import Command
from Python-ALUP.src.Frame import Frame

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

# path to the cava fifo file
# todo: replace with os tmp folder
fifo_path = "/tmp/cava/fifo"
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
    # Connect to ALUP
    arduino.SerialConnect(COM_PORT, BAUD_RATE)
    # create temporary fifo
    fifo_path = CreateFifo()
    # Create custom config 
    config_path = CreateCavaConfig(arduino.configuration.ledCount, fifo_path)

    # Start Cava with created config
    cava_process = subprocess.Popen(["cava","-p", config_path])

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

    
    
def CreateFifo(fifo_path):   
    # create temp folder if non-existent
    Path(os.path.dirname(os.path.abspath(fifo_path))).mkdir(parents=False, exist_ok=True)
    
    # create fifo file if not exists
    if not os.path.exists(fifo_path):
        os.mkfifo(fifo_path)
        
    return fifo_path


def CreateCavaConfig(num_leds):
    # read in default config
    # change bars to num_leds
    # make sure bit_format is 8 bit
    # paste into new custom config to temp folder
    # return path of custom config 


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
