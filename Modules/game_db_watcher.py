
import config
import sqlite3
import mariadb
import asyncio
import sys
import time
from datetime import datetime, timedelta
import valve.rcon
from usersync import runSync

def watch_game_db():
    while True:
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
        gamedbCur.execute("select DISTINCT  g.guildid, g.name, (select count() from building_instances where object_id in (select object_id from buildings where owner_id = g.guildId)) as count FROM guilds as g LEFT JOIN buildings as b ON b.owner_id = g.guildId ORDER BY count DESC")
        dbRows = gamedbCur.fetchall()
        if dbRows != None and len(dbRows) > 0:
            dbCur.execute("DELETE FROM {servername}_building_piece_tracking".format(servername=config.Server_Name))
            for row in dbRows:
                dbCur.execute("INSERT INTO {servername}_building_piece_tracking (clan_id, clan_name, building_piece_count) VALUES (?, ?, ?)".format(servername=config.Server_Name), (row[0], row[1], row[2]))
            dbCon.commit()

        gamedbCur.execute("SELECT g.guildid, g.name, count(*) as InventoryCount FROM Detailed_structure_inventory as dsi JOIN buildings as b on dsi.owner_id = b.object_id JOIN guilds as g on b.owner_id = g.guildId GROUP BY g.guildId ORDER BY InventoryCount DESC")
        invdbrows = gamedbCur.fetchall()
        if invdbrows != None and len(invdbrows) > 0:
            dbCur.execute("DELETE FROM {servername}_inventory_tracking".format(servername=config.Server_Name))
            for row in invdbrows:
                dbCur.execute("INSERT INTO {servername}_inventory_tracking (clan_id, clan_name, inventory_count) VALUES (?, ?, ?)".format(servername=config.Server_Name), (row[0], row[1], row[2]))
            dbCon.commit()
        

        #Check if prisoners need released
        dbCur.execute("SELECT cellName, prisoner, sentenceTime, sentenceLength, assignedPlayerPlatformID FROM {server}_jail_info ORDER BY ID ASC".format(server=config.Server_Name))
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
                    #update jail posting in discord
                    if remaining <= 0:
                        TimeLeft = 0
                        #get server info
                        dbCur.execute("SELECT rcon_host, rcon_port, rcon_pass, Prison_Exit_Coordinates FROM servers where serverName",(config.Server_Name, ))
                        serverInfo = dbCur.fetchone()
                        if serverInfo != None:
                            rcon_host = serverInfo[0]
                            rcon_port = serverInfo[1]
                            rcon_pass = serverInfo[2]
                            Prison_Exit_Coordinates = serverInfo[3]

                        #release prisoner
                        runSync(True)
                        #get conid
                        dbCur.execute("SELECT conid FROM {serverName}_currentUsers WHERE platformid = ? LIMIT 1".format(serverName=config.Server_Name),(assignedPlayerPlatformID,))
                        conid = dbCur.fetchone()
                        if conid != None:
                            attempts = 0
                            while success == 0 and attempts <= 5:
                                try:
                                    with valve.rcon.RCON((rcon_host, int(rcon_port)), rcon_pass) as rcon:
                                        response = rcon.execute(f"con {conid[0]} teleportplayer {Prison_Exit_Coordinates}")
                                        rcon.close()
                                        response_text = response.body.decode('utf-8', 'ignore') 
                                    success = 1
                                except Exception:
                                    success = 0
                                    attempts = attempts + 1
                                    time.sleep(1)
                            if success == 1:
                                dbCur.execute("UPDATE {server}_jail_info SET prisoner = NULL WHERE cellName = ?".format(server=config.Server_Name), (cellName,))

        gamedbCon.close()
        dbCon.close()
        time.sleep(60)

    