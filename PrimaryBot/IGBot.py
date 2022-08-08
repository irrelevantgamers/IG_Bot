from asyncio import subprocess
from concurrent.futures import Executor, process
import time
import concurrent.futures
import sys
import subprocess
import multiprocessing

# add Modules folder to system path
sys.path.insert(0, '..\\Modules')
from killlog import kill_stream
from discordhandler import discord_bot
if __name__ == "__main__":
    # Run setup for the bot
    print("Setting up bot DB info...")
    p = subprocess.call(["python", "..\\Setup\\setup.py"], stdout=sys.stdout)
    
    #establish bot module status variables
    killlogRunning = False
    discordhandlerRunning = False
    
    #start modules and loop to check for status    
    while True:
        try:
            if not killlogRunning:
                killlog = multiprocessing.Process(target=kill_stream)
                killlog.start()
                #with concurrent.futures.ProcessPoolExecutor() as executor:
                #        killlog = executor.submit(kill_stream())
                #        killlogRunning = True
            if killlog.is_alive():
                print(f'Status: Killlog is still running')
                killlogRunning = True
            else:
                print(f'Status: Killlog is not running. Restarting...')
                killlogRunning = False
        except Exception as e:
            print(f'Kill Log Error: {e}')
            killlogRunning = False
        
        try:
            if not discordhandlerRunning:
                discordhandler = multiprocessing.Process(target=discord_bot)
                discordhandler.start()
                #with concurrent.futures.ProcessPoolExecutor() as executor:
                #        discordhandler = executor.submit(discordhandler())
                #        discordhandlerRunning = True
            if discordhandler.is_alive():
                print(f'Status: Discord Handler is still running')
                discordhandlerRunning = True
            else:
                print(f'Status: Discord Handler is not running. Restarting...')
                discordhandlerRunning = False
        except Exception as e:
            print(f'Discord Handler Error: {e}')
            discordhandlerRunning = False

        time.sleep(10) # wait 10 seconds before checking status