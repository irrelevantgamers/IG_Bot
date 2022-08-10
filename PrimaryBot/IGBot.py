from asyncio import subprocess
from concurrent.futures import Executor, process
from pickle import TRUE
import time
import concurrent.futures
import sys
import subprocess
import multiprocessing
import valve.rcon


# add Modules folder to system path
sys.path.insert(0, '..\\Modules')
import config
from killlog import kill_stream
from discordhandler import discord_bot
from usersync import runSync
from game_log_watcher import game_log_watcher
from accountpayroll import pay_users

if __name__ == "__main__":
    # Run setup for the bot
    print("Setting up bot DB info...")
    p = subprocess.call(["python", "..\\Setup\\setup.py"], stdout=sys.stdout)
    
    #establish bot module status variables
    outOfKarma = False
    killlogRunning = False
    discordhandlerRunning = False
    userSyncRunning = False
    gameLogWatcherRunning = False
    accountPayrollRunning = False
    #start modules and loop to check for status    
    while True:
        if outOfKarma == False:
            try:
                if not killlogRunning:
                    killlog = multiprocessing.Process(target=kill_stream)
                    killlog.start()
                    killlogRunning = True
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
                    discordhandlerRunning = True
                if discordhandler.is_alive():
                    print(f'Status: Discord Handler is still running')
                    discordhandlerRunning = True
                else:
                    print(f'Status: Discord Handler is not running. Restarting...')
                    discordhandlerRunning = False
            except Exception as e:
                print(f'Discord Handler Error: {e}')
                discordhandlerRunning = False

            try:
                if not userSyncRunning:
                    userSync = multiprocessing.Process(target=runSync, args=(False,))
                    userSync.start()
                    userSyncRunning = True
                if userSync.is_alive():
                    print(f'Status: User Sync is still running')
                    userSyncRunning = True
                else:
                    print(f'Status: User Sync is not running. Restarting...')
                    userSyncRunning = False
            except Exception as e:
                print(f'User Sync Error: {e}')
                userSyncRunning = False

            try:
                if not gameLogWatcherRunning:
                    gameLogWatcher = multiprocessing.Process(target=game_log_watcher)
                    gameLogWatcher.start()
                    gameLogWatcherRunning = True
                if gameLogWatcher.is_alive():
                    print(f'Status: Game Log Watcher is still running')
                    gameLogWatcherRunning = True
                else:
                    print(f'Status: Game Log Watcher is not running. Restarting...')
                    gameLogWatcherRunning = False
            except Exception as e:
                print(f'Game Log Watcher error: {e}')
                gameLogWatcherRunning = False

            try:
                if not accountPayrollRunning:
                    accountPayroll = multiprocessing.Process(target=pay_users)
                    accountPayroll.start()
                    accountPayrollRunning = True
                if accountPayroll.is_alive():
                    print(f'Status: Account Payroll is still running')
                    accountPayrollRunning = True
                else:
                    print(f'Status: Account Payroll is not running. Restarting...')
                    accountPayrollRunning = False
            except Exception as e:
                print(f'Account Payroll error: {e}')
                accountPayrollRunning = False

            attempts = 0
            rconSuccess = False
            while rconSuccess == False and attempts <= 5:
                try:
                    with valve.rcon.RCON((config.Server_RCON_Host, int(config.Server_RCON_Port)), config.Server_RCON_Pass) as rcon:
                        response = rcon.execute("listplayers")
                        rcon.close()
                        response_text = response.body.decode('utf-8', 'ignore')
                    rconSuccess = True
                except valve.rcon.RCONAuthenticationError:
                    print("RCON watcher error: Authentication Error")
                    status = "Could not authenticate RCON"
                    rconSuccess = True
                    attempts = attempts + 1
                    pass
                except ConnectionResetError:
                    print("RCON watcher error: Could not connect to server. Retry later")
                    status = "Could not connect to server, possibly out of karma"
                    rconSuccess = 0
                    attempts = attempts + 5
                    outOfKarma = True
                    pass

            time.sleep(30) # wait 30 seconds before checking status
        else:
            print("Out of Karma! Stopping all rcon dependant modules until karma is regained...")
            userSync.terminate()
            userSyncRunning = False
            time.sleep(300) # wait 5 minutes before releasing modules
            outOfKarma = False