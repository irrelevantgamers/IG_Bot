import valve.rcon
import time
import sys
import mariadb
import config
from getconid import getconid
from datetime import datetime, timedelta
# setup logging
import logging
from logging.handlers import RotatingFileHandler
import os


def TeleportRequestWatcher():
    # create logger
    logger = logging.getLogger("teleporter")
    logger.setLevel(level=logging.DEBUG)

    # set formatter
    logFileFormatter = logging.Formatter(
        fmt=f"%(levelname)s %(created)s (%(relativeCreated)d) \t %(pathname)s F%(funcName)s L%(lineno)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # set the handler
    fileHandler = RotatingFileHandler(
        filename='..\\logs\\teleporter.log',
        maxBytes=10000,
        backupCount=5
    )
    fileHandler.setFormatter(logFileFormatter)
    fileHandler.setLevel(level=logging.INFO)
    logger.addHandler(fileHandler)
    logger.info('Teleport Request Watcher Started')
    while True:
        # check if we need to exit
        if os.path.exists('..\\restart'):
            os._exit(0)
        try:
            dbCon = mariadb.connect(
                user=config.DB_user,
                password=config.DB_pass,
                host=config.DB_host,
                port=config.DB_port,
                database=config.DB_name

            )
            logger.info('Connected to MariaDB')
        except mariadb.Error as e:
            print(f"Error connecting to MariaDB Platform: {e}")
            logger.info('Error connecting to MariaDB Platform: %s', e)
            sys.exit(1)
        dbCur = dbCon.cursor()
        # look for teleport requests
        dbCur.execute("Select id, servername FROM servers WHERE Enabled =True")
        servers = dbCur.fetchall()
        if servers != None:
            for server in servers:
                now = datetime.now()
                eligibleProcessTime = now - timedelta(seconds=10)
                dbCur.execute(
                    "SELECT player, platformid, dstLocation, attempts FROM {servername}_teleport_requests WHERE completed =False AND lastAttempt <= ?".format(
                        servername=server[1]), (eligibleProcessTime,))
                result = dbCur.fetchall()
                if result != None:
                    for request in result:
                        player = request[0]
                        platformid = request[1]
                        dstLocation = request[2]
                        tpattempts = request[3]
                        logger.info('Found teleport request for %s', player)
                        dbCur.execute("SELECT rcon_host, rcon_port, rcon_pass FROM servers WHERE serverName =?",
                                      (server[1],))
                        serverInfo = dbCur.fetchone()
                        if serverInfo != None:
                            rcon_host = serverInfo[0]
                            rcon_port = serverInfo[1]
                            rcon_pass = serverInfo[2]
                            # check if player is online
                            dbCur.execute("SELECT platformid FROM {servername}_currentusers WHERE platformid =?".format(
                                servername=server[1]), (platformid,))
                            result = dbCur.fetchone()
                            if result != None:
                                conid = getconid(rcon_host, int(rcon_port), rcon_pass, platformid)
                                if conid != None:
                                    success = 0
                                    attempts = 0
                                    while success == 0 and attempts <= 5:
                                        try:
                                            with valve.rcon.RCON((rcon_host, int(rcon_port)), rcon_pass) as rcon:
                                                response = rcon.execute(f"con {conid} teleportplayer {dstLocation}")
                                                rcon.close()
                                            success = 1
                                            tpattempts = tpattempts + 1
                                            dbCur.execute(
                                                "UPDATE {servername}_teleport_requests SET completed =?, attempts =? WHERE platformid =?".format(
                                                    servername=server[1]), (True, tpattempts, platformid))
                                            dbCon.commit()
                                            print("Teleported {player} to {dstLocation}".format(player=player,
                                                                                                dstLocation=dstLocation))
                                            logger.info('Teleported %s to %s', player, dstLocation)
                                        except Exception as e:
                                            success = 0
                                            logger.info('Error teleporting %s to %s: %s', player, dstLocation, e)
                                            attempts = attempts + 1
                                            time.sleep(1)
                                            attempts = attempts + 1
                                            time.sleep(1)
                                        tpattempts = tpattempts + 1
                            else:
                                print("{player} is not online".format(player=player))
                                logger.info('%s is not online', player)
                                tpattempts = tpattempts + 1
                                dbCur.execute(
                                    "UPDATE {servername}_teleport_requests SET attempts =? WHERE platformid =?".format(
                                        servername=server[1]), (tpattempts, platformid))
                                dbCon.commit()
                        if tpattempts >= 6:
                            dbCur.execute(
                                "UPDATE {servername}_teleport_requests SET completed =True WHERE platformid =?".format(
                                    servername=server[1]), (platformid,))
                            dbCon.commit()
                            logger.info('%s has exceeded maximum attempts', player)

        dbCon.close()
        logger.info('Closed MariaDB Connection')
        time.sleep(1)


def CancelAllTeleportRequests(server):
    logger.info('Cancelling all teleport requests for %s', server)
    try:
        dbCon = mariadb.connect(
            user=config.DB_user,
            password=config.DB_pass,
            host=config.DB_host,
            port=config.DB_port,
            database=config.DB_name

        )
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)
    dbCur = dbCon.cursor()
    dbCur.execute("UPDATE {servername}_teleport_requests SET completed =True".format(servername=server))
    dbCon.commit()
    dbCon.close()
