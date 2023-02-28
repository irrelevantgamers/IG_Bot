import config
import sqlite3
import mariadb
import asyncio
import sys
import time
from datetime import datetime, timedelta
import valve.rcon
from usersync import runSync
from getconid import getconid
import os


def watch_game_db():
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
        except mariadb.Error as e:
            print(f"Error connecting to MariaDB Platform: {e}")
            sys.exit(1)
        dbCur = dbCon.cursor()
        file_path_db = config.Server_Game_DB_Location
        gamedbCon = sqlite3.connect(file_path_db)
        gamedbCur = gamedbCon.cursor()
        gamedbCur.execute(
            "select DISTINCT  g.guildid, g.name, (select count() from building_instances where object_id in (select object_id from buildings where owner_id = g.guildId)) as count FROM guilds as g LEFT JOIN buildings as b ON b.owner_id = g.guildId ORDER BY count DESC")
        dbRows = gamedbCur.fetchall()
        if dbRows != None and len(dbRows) > 0:
            dbCur.execute("DELETE FROM {servername}_building_piece_tracking".format(servername=config.Server_Name))
            for row in dbRows:
                dbCur.execute(
                    "INSERT INTO {servername}_building_piece_tracking (clan_id, clan_name, building_piece_count) VALUES (?, ?, ?)".format(
                        servername=config.Server_Name), (row[0], row[1], row[2]))
            dbCon.commit()

        gamedbCur.execute(
            "SELECT g.guildid, g.name, count(*) as InventoryCount FROM Detailed_structure_inventory as dsi JOIN buildings as b on dsi.owner_id = b.object_id JOIN guilds as g on b.owner_id = g.guildId GROUP BY g.guildId ORDER BY InventoryCount DESC")
        invdbrows = gamedbCur.fetchall()
        if invdbrows != None and len(invdbrows) > 0:
            dbCur.execute("DELETE FROM {servername}_inventory_tracking".format(servername=config.Server_Name))
            for row in invdbrows:
                dbCur.execute(
                    "INSERT INTO {servername}_inventory_tracking (clan_id, clan_name, inventory_count) VALUES (?, ?, ?)".format(
                        servername=config.Server_Name), (row[0], row[1], row[2]))
            dbCon.commit()

        # Check if prisoners need released
        print("Checking if prisoners need released")
        dbCur.execute(
            "SELECT cellName, prisoner, sentenceTime, sentenceLength, assignedPlayerPlatformID FROM {server}_jail_info".format(
                server=config.Server_Name))
        result = dbCur.fetchall()
        if result != None:
            for result in result:
                cellName = result[0]
                prisoner = result[1]
                sentenceTime = result[2]
                sentenceLength = result[3]
                assignedPlayerPlatformID = result[4]

                if prisoner == None:
                    continue
                else:
                    now = datetime.now()
                    currentTime = datetime.timestamp(now)
                    SentenceToSeconds = sentenceLength * 60
                    SenEndTimeStamp = datetime.timestamp(sentenceTime) + SentenceToSeconds

                    remaining = (SenEndTimeStamp - currentTime) / 60
                    # update jail posting in discord
                    if remaining <= 0:
                        TimeLeft = 0
                        print("release prisoner {assignedPlayerPlatformID} from cell {cellName}".format(
                            assignedPlayerPlatformID=assignedPlayerPlatformID, cellName=cellName))
                        # get server info
                        dbCur.execute(
                            "SELECT rcon_host, rcon_port, rcon_pass, Prison_Exit_Coordinates FROM servers where serverName =?",
                            (config.Server_Name,))
                        serverInfo = dbCur.fetchone()
                        if serverInfo != None:
                            rcon_host = serverInfo[0]
                            rcon_port = serverInfo[1]
                            rcon_pass = serverInfo[2]
                            Prison_Exit_Coordinates = serverInfo[3]
                            print(Prison_Exit_Coordinates)
                        # release prisoner
                        dbCur.execute(
                            "INSERT INTO {server}_teleport_requests (player, dstlocation, platformid) VALUES (?,?,?)".format(
                                server=config.Server_Name),
                            (prisoner, Prison_Exit_Coordinates, assignedPlayerPlatformID))
                        dbCur.execute(
                            "UPDATE {server}_jail_info SET prisoner = NULL, assignedPlayerPlatformID =NULL, sentenceTime = NULL, sentenceLength = NULL WHERE cellName = ?".format(
                                server=config.Server_Name), (cellName,))
                        dbCon.commit()

            # check if prisoners escaped
            print("Checking if prisoners escaped")
            dbCur.execute(
                "SELECT cellName, prisoner, sentenceTime, sentenceLength, assignedPlayerPlatformID, spawnLocation FROM {server}_jail_info".format(
                    server=config.Server_Name))
            result = dbCur.fetchall()
            if result != None:
                for result in result:
                    cellName = result[0]
                    prisoner = result[1]
                    sentenceTime = result[2]
                    sentenceLength = result[3]
                    assignedPlayerPlatformID = result[4]
                    spawnLocation = result[5]

                    if prisoner == None:
                        continue
                    else:
                        file_path_db = config.Server_Game_DB_Location
                        connection = sqlite3.connect(file_path_db)
                        cursor = connection.cursor()
                        cursor.execute(
                            f"SELECT c.id, c.playerid, c.char_name, a.user as PlatformID FROM characters c LEFT JOIN accounts a on c.playerid = a.id WHERE a.user =?",
                            (assignedPlayerPlatformID,))
                        result_id = cursor.fetchone()
                        characterID = result_id[0]

                        cursor.execute(f"select X, Y  FROM actor_position WHERE id =?", (characterID,))
                        location = cursor.fetchone()
                        cursor.close()
                        connection.close()
                        playerX = location[0]
                        playerY = location[1]
                        # if not in prison, teleport to prison
                        # get prison min and max
                        dbCur.execute(
                            "SELECT prison_min_x, prison_min_y, prison_max_x, prison_max_y FROM servers WHERE serverName =?",
                            (config.Server_Name,))
                        info = dbCur.fetchone()
                        if info != None:
                            prison_min_x = info[0]
                            prison_min_y = info[1]
                            prison_max_x = info[2]
                            prison_max_y = info[3]
                            # check if in prison
                            if playerX < prison_min_x or playerX > prison_max_x or playerY < prison_min_y or playerY > prison_max_y:
                                print(f"Player {prisoner} is not in prison")
                                # move them back
                                dbCur.execute("SELECT rcon_host, rcon_port, rcon_pass FROM servers WHERE serverName =?",
                                              (config.Server_Name,))
                                serverInfo = dbCur.fetchone()
                                if serverInfo != None:
                                    rcon_host = serverInfo[0]
                                    rcon_port = serverInfo[1]
                                    rcon_pass = serverInfo[2]
                                # release prisoner
                                dbCur.execute(
                                    "INSERT INTO {server}_teleport_requests (player, dstlocation, platformid) VALUES (?,?,?)".format(
                                        server=config.Server_Name), (prisoner, spawnLocation, assignedPlayerPlatformID))
                                dbCon.commit()

        gamedbCon.close()
        dbCon.close()
        time.sleep(60)
