from asyncio import subprocess
from concurrent.futures import Executor, process
import time
import concurrent.futures
import asyncio
import sys
import subprocess

# add Modules folder to system path
sys.path.insert(0, '..\\Modules')
# read in the config variables from importconfig.py
from killlog import *

if __name__ == "__main__":
    # Run setup for the bot
    subprocess.call(["python", "..\\Setup\\setup.py"])
    
    #establish bot module status variables
    killlogRunning = False

    #start modules and loop to check for status    
    while True:
        if not killlogRunning:
            with concurrent.futures.ProcessPoolExecutor() as executor:
                    killlog = executor.submit(kill_stream)
                    killlogRunning = True
        if killlog.running():
            print(f'Status: Killlog is still running')
        else:
            print(f'Status: Killlog is not running. Restarting...')
            killlogRunning = False

        time.sleep(10) # wait 10 seconds before checking status