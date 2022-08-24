from asyncio import subprocess
from concurrent.futures import Executor, process
from pickle import TRUE
import time
import concurrent.futures
import sys
import subprocess
import multiprocessing
import valve.rcon
from concurrent.futures import Executor, process
import concurrent.futures
import lovely_logger as log # pip install lovely-logger
from datetime import datetime
import os

# add Modules folder to system path
sys.path.insert(0, '..\\Modules')
import config
from killlog import kill_stream
from discordhandler import discord_bot
from usersync import runSync
from game_log_watcher import game_log_watcher
from accountpayroll import pay_users
from orderprocessing import processOrderLoop
from mapmaker import create_conan_maps
from game_db_watcher import watch_game_db
from teleporter import TeleportRequestWatcher, CancelAllTeleportRequests
from serversettingswatcher import WatchForServerSettings

#setup logging
import logging
from logging.handlers import RotatingFileHandler


if __name__ == "__main__":
    # create logger
    logger = logging.getLogger("IGBOT")
    logger.setLevel(level=logging.DEBUG)

    # set formatter
    logFileFormatter = logging.Formatter(
        fmt=f"%(levelname)s %(created)s (%(relativeCreated)d) \t %(pathname)s F%(funcName)s L%(lineno)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # set the handler
    fileHandler = RotatingFileHandler(
    filename='..\\logs\\IGBOT.log', 
    maxBytes=10000, 
    backupCount=2
    )
    fileHandler.setFormatter(logFileFormatter)
    fileHandler.setLevel(level=logging.INFO)
    logger.addHandler(fileHandler)
    logger.info('IGBOT Started')

    # Run setup for the bot
    print("Setting up bot DB info...")
    logger.info("Setting up bot DB info...")
    p = subprocess.call(["python", "..\\Setup\\setup.py"], stdout=sys.stdout)
    logger.info('Setup complete')
    #establish bot module status variables
    outOfKarma = False
    killlogRunning = False
    discordhandlerRunning = False
    userSyncRunning = False
    gameLogWatcherRunning = False
    accountPayrollRunning = False
    orderProcessingRunning = False
    mapMakerProcessRunning = False
    GameDBWatcherRunning = False
    TeleporterWatcherRunning = False
    serversettingswatcherrunning = False
    #start modules and loop to check for status   
    logger.info('Starting bot modules')
    executor = concurrent.futures.ProcessPoolExecutor(max_workers=10) 
    while True:
        if outOfKarma == False:
            try:
                if not killlogRunning:
                    killlog = executor.submit(kill_stream)
                    logger.info('Killlog started')
                    killlogRunning = True
                if killlog.done():
                    print(f'Status: Killlog is not running. Restarting...')
                    logger.info('Killlog is not running. Restarting...')
                    killlogRunning = False
                else:
                    print(f'Status: Killlog is still running')
                    logger.info('Killlog is still running')
                    killlogRunning = True
            except Exception as e:
                print(f'Kill Log Error: {e}')
                logger.error(f'Kill Log Error: {e}')
                killlogRunning = False
            
            try:
                if not discordhandlerRunning:
                    discordhandler = executor.submit(discord_bot)
                    logger.info('Discord handler started')
                    discordhandlerRunning = True
                if discordhandler.done():
                    print(f'Status: Discord Handler is not running. Restarting...')
                    logger.info('Discord Handler is not running. Restarting...')
                    discordhandlerRunning = False
                else:
                    print(f'Status: Discord Handler is still running')
                    logger.info('Discord Handler is still running')
                    discordhandlerRunning = True
            except Exception as e:
                print(f'Discord Handler Error: {e}')
                logger.error(f'Discord Handler Error: {e}')
                discordhandlerRunning = False

            try:
                if not userSyncRunning:
                    userSync = executor.submit(runSync, False)
                    logger.info('User Sync started')
                    userSyncRunning = True
                if userSync.done():
                    print(f'Status: User Sync is not running. Restarting...')
                    logger.info('User Sync is not running. Restarting...')
                    userSyncRunning = False
                else:
                    print(f'Status: User Sync is still running')
                    logger.info('User Sync is still running')
                    userSyncRunning = True
            except Exception as e:
                print(f'User Sync Error: {e}')
                logger.error(f'User Sync Error: {e}')
                userSyncRunning = False

            try:
                if not gameLogWatcherRunning:
                    gameLogWatcher = executor.submit(game_log_watcher)
                    logger.info('Game Log Watcher started')
                    gameLogWatcherRunning = True
                if gameLogWatcher.done():
                    print(f'Status: Game Log Watcher is not running. Restarting...')
                    logger.info('Game Log Watcher is not running. Restarting...')
                    gameLogWatcherRunning = False
                else:
                    print(f'Status: Game Log Watcher is still running')
                    logger.info('Game Log Watcher is still running')
                    gameLogWatcherRunning = True
            except Exception as e:
                print(f'Game Log Watcher error: {e}')
                logger.error(f'Game Log Watcher error: {e}')
                gameLogWatcherRunning = False

            try:
                if not accountPayrollRunning:
                    accountPayroll = executor.submit(pay_users)
                    logger.info('Account Payroll started')
                    accountPayrollRunning = True
                if accountPayroll.done():
                    print(f'Status: Account Payroll is not running. Restarting...')
                    logger.info('Account Payroll is not running. Restarting...')
                    accountPayrollRunning = False
                else:
                    print(f'Status: Account Payroll is still running')
                    logger.info('Account Payroll is still running')
                    accountPayrollRunning = True
            except Exception as e:
                print(f'Account Payroll error: {e}')
                logger.error(f'Account Payroll error: {e}')
                accountPayrollRunning = False

            try:
                if not orderProcessingRunning:
                    orderProcessing = executor.submit(processOrderLoop)
                    logger.info('Order Processing started')
                    orderProcessingRunning = True
                if orderProcessing.done():
                    print(f'Status: Order Processing is not running. Restarting...')
                    logger.info('Order Processing is not running. Restarting...')
                    orderProcessingRunning = False
                else:
                    print(f'Status: Order Processing is still running')
                    logger.info('Order Processing is still running')
                    orderProcessingRunning = True
            except Exception as e:
                print(f'Order Processing error: {e}')
                logger.error(f'Order Processing error: {e}')
                orderProcessingRunning = False

            try:
                if not mapMakerProcessRunning:
                    mapMakerProcess = executor.submit(create_conan_maps)
                    logger.info('Map Maker started')
                    mapMakerProcessRunning = True
                if mapMakerProcess.done():
                    print(f'Status: Map Maker Process is not running. Restarting...')
                    logger.info('Map Maker Process is not running. Restarting...')
                    mapMakerProcessRunning = False
                else:
                    print(f'Status: Map Maker Process is still running')
                    logger.info('Map Maker Process is still running')
                    mapMakerProcessRunning = True
            except Exception as e:
                print(f'Map Maker Process error: {e}')
                logger.error(f'Map Maker Process error: {e}')
                mapMakerProcessRunning = False

            try:
                if not GameDBWatcherRunning:
                    GameDBWatcher = executor.submit(watch_game_db)
                    logger.info('Game DB Watcher started')
                    GameDBWatcherRunning = True
                if GameDBWatcher.done():
                    print(f'Status: Game DB Watcher is not running. Restarting...')
                    logger.info('Game DB Watcher is not running. Restarting...')
                    GameDBWatcherRunning = False
                else:
                    print(f'Status: Game DB Watcher is still running')
                    logger.info('Game DB Watcher is still running')
                    GameDBWatcherRunning = True
            except Exception as e:
                print(f'Game DB Watcher error: {e}')
                logger.error(f'Game DB Watcher error: {e}')
                GameDBWatcherRunning = False

            try:
                if not TeleporterWatcherRunning:
                    TeleporterWatcher = executor.submit(TeleportRequestWatcher)
                    logger.info('Teleporter Watcher started')
                    TeleporterWatcherRunning = True
                if TeleporterWatcher.done():
                    print(f'Status: Teleporter Watcher is not running. Restarting...')
                    logger.info('Teleporter Watcher is not running. Restarting...')
                    TeleporterWatcherRunning = False
                else:
                    print(f'Status: Teleporter Watcher is still running')
                    logger.info('Teleporter Watcher is still running')
                    TeleporterWatcherRunning = True
            except Exception as e:
                print(f'Teleporter Watcher error: {e}')
                logger.error(f'Teleporter Watcher error: {e}')
                TeleporterWatcherRunning = False

            try:
                if not serversettingswatcherrunning:
                    serversettingswatcher = executor.submit(WatchForServerSettings)
                    logger.info('Server Settings Watcher started')
                    serversettingswatcherrunning = True
                if serversettingswatcher.done():
                    print(f'Status: Server Settings Watcher is not running. Restarting...')
                    logger.info('Server Settings Watcher is not running. Restarting...')
                    serversettingswatcherrunning = False
                else:
                    print(f'Status: Server Settings Watcher is still running')
                    logger.info('Server Settings Watcher is still running')
                    serversettingswatcherrunning = True
            except Exception as e:
                print(f'Server Settings Watcher error: {e}')
                logger.error(f'Server Settings Watcher error: {e}')
                serversettingswatcherrunning = False

            logger.info('Checking karma status')
            attempts = 0
            rconSuccess = False
            while rconSuccess == False and attempts <= 5:
                try:
                    with valve.rcon.RCON((config.Server_RCON_Host, int(config.Server_RCON_Port)), config.Server_RCON_Pass) as rcon:
                        response = rcon.execute("listplayers")
                        rcon.close()
                        response_text = response.body.decode('utf-8', 'ignore')
                    rconSuccess = True
                    logger.info('Karma is good')
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
                    logger.warning('Karma is bad')
                    executor.submit(CancelAllTeleportRequests(config.Server_Name))
                    pass

            time.sleep(30) # wait 30 seconds before checking status
        else:
            print("Out of Karma! Stopping all rcon dependant modules until karma is regained...")
            logger.warning('Out of Karma! Stopping all rcon dependant modules until karma is regained...')
            userSync.cancel()
            userSyncRunning = False
            logger.info('User Sync stopped')
            orderProcessing.cancel()
            orderProcessingRunning = False
            logger.info('Order Processing stopped')
            mapMakerProcess.cancel()
            mapMakerProcessRunning = False
            logger.info('Map Maker stopped')
            GameDBWatcher.cancel()
            GameDBWatcherRunning = False
            logger.info('Game DB Watcher stopped')
            TeleporterWatcher.cancel()
            TeleporterWatcherRunning = False
            logger.info('Teleporter Watcher stopped')
            serversettingswatcher.cancel()
            serversettingswatcherrunning = False
            logger.info('Server Settings Watcher stopped')
            logger.info('waiting for karma to be regained')
            time.sleep(300) # wait 5 minutes before releasing modules
            outOfKarma = False