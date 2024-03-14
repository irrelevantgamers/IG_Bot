import valve.rcon
import time
import mariadb
import sqlite3
import configparser
from datetime import datetime, timedelta, timezone
import sys
import a2s

# add Modules folder to system path
sys.path.insert(0, '..\\Modules')
# read in the config variables from importconfig.py
import config


def syncPlayers(serverid):
    try:
        syncCon = mariadb.connect(
            user=config.DB_user,
            password=config.DB_pass,
            host=config.DB_host,
            port=config.DB_port,
            database=config.DB_name

        )
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    syncCur = syncCon.cursor()
    print(f"Syncing current users for server id {serverid}")
    # get server config from db
    syncCur.execute(
        "SELECT ServerName, dedicated, rcon_host, rcon_port, rcon_pass, SteamQueryPort, DatabaseLocation FROM servers where Enabled =True and ID =?",
        (serverid,))
    serverInfo = syncCur.fetchone()
    if serverInfo != None:
        serverName = serverInfo[0]
        dedicated = serverInfo[1]
        rcon_host = serverInfo[2]
        rcon_port = serverInfo[3]
        rcon_pass = serverInfo[4]
        steamQueryPort = serverInfo[5]
        file_path_db = serverInfo[6]
    else:
        print("CurrentUserSync Error: Server info cannot be retrieved from DB")
        exit(1)
    loadDate = (datetime.now())
    success = 0
    # recreate currentUsers table
    clearCurrentUsers_query = f"""DELETE FROM {serverName}_currentusers;"""

    try:
        syncCur.execute(clearCurrentUsers_query)
        syncCon.commit()
    except Exception as e:
        print(f"Error creating currentUsers table from usersync script: {e}")
        sys.exit(1)

    # get playerlist from steam
    SERVER_ADDRESS = (rcon_host, int(steamQueryPort))

    # with valve.source.a2s.ServerQuerier(SERVER_ADDRESS) as server:
    #    info = server.info()
    #    players = server.players()
    #    server
    # userlist = []
    # print("{player_count}/{max_players} {server_name}".format(**info))
    # for player in sorted(players["players"],key=lambda p: p["score"], reverse=True):
    #   userlist.append("{name}".format(**player))
    userlist = a2s.players(SERVER_ADDRESS, timeout=5, encoding='utf-8')

    attempts = 0
    while success == 0 and attempts <= 5:
        try:
            with valve.rcon.RCON((rcon_host, int(rcon_port)), rcon_pass) as rcon:
                response = rcon.execute("listplayers")
                rcon.close()
                response_text = response.body.decode('utf-8', 'ignore')
                # print(response_text)
            playerlist = response_text.split('\n')
            success = 1
        except Exception:
            success = 0
            attempts = attempts + 1
            time.sleep(1)
    i = 0
    for index in range(len(playerlist) - 1):
        try:
            item = playerlist[index].replace(userlist[i].name, "")
            item = item.split(' | ')
            conid = str(item[0].strip())
            player = item[1].strip()
            userid = str(userlist[i].name)
            platformid = str(item[3].strip())
            steamPlatformId = str(item[4].strip())
            if conid != "Idx":
                i += 1
            if conid != 'Idx':
                if player != "":
                    # get player x and player y if dedicated server
                    if dedicated == True:
                        gameCon = sqlite3.connect(file_path_db)
                        gameCur = gameCon.cursor()
                        gameCur.execute(
                            "SELECT a.id, a.user, a.online, c.char_name, c.id, p.x, p.y FROM account as a INNER JOIN characters as c ON a.id = c.playerid INNER JOIN actor_position as p ON c.id = p.id WHERE a.online =1 AND a.user =?",
                            (platformid,))
                        result = gameCur.fetchone()
                        playerX = result[5]
                        playerY = result[6]
                        gameCur.close()
                        gameCon.close()
                    else:
                        playerX = 0
                        playerY = 0
                    syncCur.execute(
                        f"INSERT INTO {serverName}_currentUsers (conid, player, userid, platformid, steamPlatformId, X, Y, loadDate) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (conid, player, userid, platformid, steamPlatformId, int(playerX), int(playerY), loadDate))
                    syncCur.execute(
                        f"INSERT INTO {serverName}_historicalUsers (conid, player, userid, platformid, steamPlatformId, X, Y, loadDate) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (conid, player, userid, platformid, steamPlatformId, int(playerX), int(playerY), loadDate))

                    syncCon.commit()

            # create accounts for any new users
            syncCur.execute(f"SELECT player, userid, platformid, steamplatformid FROM {serverName}_currentUsers")
            result = syncCur.fetchall()
            for row in result:
                player = row[0]
                userid = row[1]
                platformid = row[2]
                steamid = row[3]
                syncCur.execute(f"SELECT * FROM accounts WHERE conanplatformid =?", (platformid,))
                result = syncCur.fetchone()
                if result == None:
                    syncCur.execute(
                        f"INSERT INTO accounts (conanplayer, conanuserid, conanplatformid, steamplatformid, walletbalance, lastupdated, firstseen) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (player, userid, platformid, steamPlatformId, config.Shop_StartingCash, loadDate, loadDate))
                    syncCon.commit()
                # update last seen server for user
                syncCur.execute(f"UPDATE accounts SET lastServer =? WHERE conanplatformid =?", (serverName, platformid))
                syncCon.commit()
        except Exception as e:
            if "index out of range" in str(e):
                pass
            else:
                print(f"UserSyncError: {e}")
                pass
    syncCon.commit()
    syncCur.close()
    syncCon.close()


def runSync(force):
    try:
        runSyncCon = mariadb.connect(
            user=config.DB_user,
            password=config.DB_pass,
            host=config.DB_host,
            port=config.DB_port,
            database=config.DB_name

        )
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    runSyncCur = runSyncCon.cursor()
    runSyncCur.execute("Select ID, lastUserSync FROM servers WHERE Enabled =TRUE and serverName =?",
                       (config.Server_Name,))
    servers = runSyncCur.fetchall()
    if servers != None:
        for server in servers:
            serverid = server[0]
            lastUserSync = server[1]
            now = datetime.now()
            fiveMinAgo = now - timedelta(minutes=5)
            if force == True:
                try:
                    syncPlayers(serverid)
                    runSyncCur.execute("UPDATE servers SET lastUserSync = ? WHERE ID = ?", (now, serverid))
                    runSyncCon.commit()
                except Exception as e:
                    print(f"Could not sync players for ServerID {serverid}.\nError: {e}")
                    pass
            else:
                if lastUserSync == None:
                    try:
                        syncPlayers(serverid)
                        runSyncCur.execute("UPDATE servers SET lastUserSync = ? WHERE ID = ?", (now, serverid))
                        runSyncCon.commit()
                    except Exception as e:
                        print(f"Could not sync players for ServerID {serverid}.\nError: {e}")
                        pass
                else:
                    if lastUserSync < fiveMinAgo:
                        try:
                            syncPlayers(serverid)
                            runSyncCur.execute("UPDATE servers SET lastUserSync = ? WHERE ID = ?", (now, serverid))
                            runSyncCon.commit()
                        except Exception as e:
                            print(f"Could not sync players for ServerID {serverid}.\nError: {e}")
                            pass

    runSyncCur.close()
    runSyncCon.close()

