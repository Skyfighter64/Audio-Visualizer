import subprocess
import time
import os
from pathlib import Path

# note: make sure, alsa is configured accordingly and loopback devices are active

# Todo:
# get input from cava nonblocking
# parse input
# convert to led effect
# send over alup

# future goals:
# multiple devices
# different effects 
# udp/wifi support

# also see: https://github.com/karlstav/cava/issues/123#issuecomment-307891020

# path to the cava fifo file
fifo_path = "/tmp/cava/fifo"
# these values need to be the same as in the cava config
# todo: automatically read from config file ? (see example)
cava_config_path = "/home/pi/.config/cava/visualizer_config"
bit_format = 8 # set sample size (8bit or 16bit) according to CAVA config
bars = 10

def main():
    
    
    # start cava
    cava_process = subprocess.Popen(["cava","-p", cava_config_path])
    
    # create temp folder if non-existent
    Path("/tmp/cava/").mkdir(parents=False, exist_ok=True)
    # create fifo file if not exists
    if not os.path.exists(fifo_path):
        os.mkfifo(fifo_path)
        
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
        



if __name__ == "__main__":
    main()
