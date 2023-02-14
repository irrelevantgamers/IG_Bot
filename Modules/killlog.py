from time import sleep
import mariadb
import sqlite3
import config
import os
import sys
from datetime import datetime, timedelta

# Get server id from config file and get server info from mariadb
sys.path.insert(0, '..\\Modules')


def connect_mariadb():
    global mariaCon
    global mariaCur
    try:
        mariaCon = mariadb.connect(
            user=config.DB_user,
            password=config.DB_pass,
            host=config.DB_host,
            port=config.DB_port,
            database=config.DB_name

        )
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)
    mariaCur = mariaCon.cursor()


def close_mariaDB():
    mariaCur.close()
    mariaCon.close()


def kill_stream():
    print("Exiled Kill Stream Started")
    while True:
        # check if we need to exit
        if os.path.exists('..\\restart'):
            os._exit(0)
        # read in last event time
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
        dbCur.execute(
            "SELECT databaseLocation, Killlog_Last_Event_Time, serverName FROM servers WHERE serverName = ?",
            (config.Server_Name,))
        server_info = dbCur.fetchone()
        if len(server_info) != 0 and server_info[0] is not None:

            gamedb_file = server_info[0]
            serverid = server_info[2]
            last_event_time = server_info[1]

            if last_event_time is None:
                print("No last event time found. Setting to 0")
                last_event_time = datetime.now() - timedelta(days=1)
            Killlog_Last_Event_Time = last_event_time

            exiled_gamedb_con = sqlite3.connect(gamedb_file)
            exiled_gamedb_cur = exiled_gamedb_con.cursor()
            exiled_gamedb_cur.execute(
                """
                SELECT worldTime, ukill.causerName, ukill.causerID, causerGuildName, ukill.ownerName, ukill.ownerId, ownerGuildName, ukill.x AS X, ukill.y AS Y 
                FROM (
                    SELECT distinct x, y, z, causerName, causerId, causerGuildName, ownerName, ownerId 
                    from game_events where eventType = 103 AND causerName != '' AND ownerName != ''
                    ) as ukill  
                join (
                    SELECT worldTime, x, y, z, causerName, causerId, ownerName, ownerId, ownerGuildName 
                        FROM game_events WHERE eventType = 103 AND causerName != '' AND ownerName != ''
                    ) 
                USING (x, y, z) 
                WHERE datetime(worldTime,'unixepoch') >= ? group by x ,y ,z 
                ORDER BY worldTime ASC
                """,
                (Killlog_Last_Event_Time,))
            kills = exiled_gamedb_cur.fetchall()
            killList = ''
            if len(kills) > 0:
                for row in kills:
                    eventTime = datetime.fromtimestamp(int(row[0]))
                    if row[1] is not None:
                        if eventTime > Killlog_Last_Event_Time:
                            Killlog_Last_Event_Time = eventTime
                            player = row[1]
                            playerID = row[2]
                            playerClan = row[3]
                            victim = row[4]
                            victimID = row[5]
                            victimClan = row[6]
                            KillLocationX = int(row[7])
                            KillLocationY = int(row[8])
                            killtype = "Normal"
                            ProtectedArea = None
                            if playerClan == '':
                                playerClan = 'N\\A'

                            if victimClan == '':
                                victimClan = 'N\\A'

                            if playerClan == victimClan and playerClan != 'N\\A':
                                sameClan = True
                            else:
                                sameClan = False

                            # check kill_log to see if same clan in last 24 hours
                            dbCur.execute(
                                "SELECT ID FROM {server}_kill_log WHERE player_clan = victim_clan AND player = ? AND loadDate > ?".format(
                                    server=serverid), (player, datetime.now() - timedelta(hours=24)))
                            same_Clan_Check = dbCur.fetchone()
                            if same_Clan_Check is not None:
                                sameClan = True
                            playerLevel = exiled_gamedb_cur.execute("Select level FROM characters WHERE char_name =?",
                                                                    (player,))
                            playerLevel = playerLevel.fetchone()
                            if playerLevel is not None:
                                playerLevel = playerLevel[0]
                            else:
                                playerLevel = 0
                            victimLevel = exiled_gamedb_cur.execute("Select level FROM characters WHERE char_name =?",
                                                                    (victim,))
                            victimLevel = victimLevel.fetchone()
                            if victimLevel is not None:
                                victimLevel = victimLevel[0]
                            else:
                                victimLevel = 0
                            # get account id and platformid from the playerid
                            # Killers PlatformID
                            try:
                                exiled_gamedb_cur.execute(
                                    "SELECT a.user FROM characters c LEFT JOIN account a on c.playerid = a.id WHERE c.id =?",
                                    (playerID,))
                                PlayerPlatformID = exiled_gamedb_cur.fetchone()
                                if PlayerPlatformID is None:
                                    PlayerPlatformID = 'N\\A'
                                # victims PlatformID
                                exiled_gamedb_cur.execute(
                                    "SELECT a.user FROM characters c LEFT JOIN account a on c.playerid = a.id WHERE c.id =?",
                                    (victimID,))
                                VictimPlatformID = exiled_gamedb_cur.fetchone()
                                if VictimPlatformID is None:
                                    VictimPlatformID = 'N\\A'
                            except Exception:
                                print("Failed to process platform ids")
                                pass

                            ##get protected areas
                            try:
                                dbCur.execute(
                                    "SELECT paname, minX, minY, maxX, maxY FROM {servername}_protected_areas".format(
                                        servername=serverid))
                                protectedareas = dbCur.fetchall()
                                if len(protectedareas) != 0 and protectedareas[0] != None:
                                    for area in protectedareas:
                                        areaName = area[0]
                                        minX = area[1]
                                        minY = area[2]
                                        maxX = area[3]
                                        maxY = area[4]

                                        if ((int(KillLocationX) <= int(maxX)) and (
                                                int(KillLocationX) >= int(minX)) and (
                                                int(KillLocationY) <= int(maxY)) and (int(KillLocationY) >= int(minY))):
                                            try:
                                                dbCur.execute(
                                                    "INSERT INTO {servername}_offenders (player, platformID, current_strikes, last_strike, strike_outs) VALUES (?,?,1,?,0)".format(
                                                        servername=serverid),
                                                    (player, PlayerPlatformID[0], Killlog_Last_Event_Time))
                                                dbCon.commit()
                                            except Exception as e:
                                                if "Duplicate" in str(e):
                                                    dbCur.execute(
                                                        "SELECT current_strikes, strike_outs FROM {servername}_offenders WHERE PlatformID =?".format(
                                                            servername=serverid), (PlayerPlatformID[0],))
                                                    info = dbCur.fetchone()
                                                    strikes = info[0]
                                                    offenses = info[1]
                                                    newStrikes = int(strikes) + 1
                                                    dbCur.execute(
                                                        "UPDATE {servername}_offenders SET current_strikes =?, last_strike =? WHERE PlatformID =?".format(
                                                            servername=serverid),
                                                        (newStrikes, Killlog_Last_Event_Time, PlayerPlatformID[0]))
                                                    dbCon.commit()
                                                    pass
                                                else:
                                                    print(e)
                                                    pass
                                            killList = killList + (
                                                f"**PROTECTED AREA KILL DETECTED AT {areaName} STRIKE HAS BEEN ISSUED**\n")
                                            killtype = "ProtectedArea"
                                            ProtectedArea = areaName
                            except Exception as e:
                                print(f"Error getting protected areas: {e}")
                                pass

                            # check for kill streaks
                            wantedKill = False
                            bountyKill = False
                            wanted_paid_amount = 0
                            bounty_paid_amount = 0
                            if not sameClan:
                                # print("checking kill streaks")
                                matchFound = 0
                                dbCur.execute(
                                    "SELECT id, platformid, player, killstreak, highestkillstreak, wantedLevel, bounty FROM {servername}_wanted_players".format(
                                        servername=serverid))
                                wanted = dbCur.fetchall()
                                rowcount = len(wanted)
                                if rowcount != 0:
                                    # print("existing Wanted players found")
                                    for result in wanted:
                                        playerid = result[0]
                                        conanplatformid = result[1]
                                        conanplayer = result[2]
                                        killstreak = result[3]
                                        highestkillstreak = result[4]
                                        wantedLevel = result[5]
                                        bounty = result[6]
                                        if PlayerPlatformID is not None and VictimPlatformID is not None:
                                            if conanplatformid == PlayerPlatformID[0]:
                                                newkillstreak = int(killstreak) + 1
                                                dbCur.execute(
                                                    "UPDATE {servername}_wanted_players SET killstreak =? WHERE id =?".format(
                                                        servername=serverid), (newkillstreak, playerid))

                                                if newkillstreak < 5:
                                                    newwantedlevel = 0
                                                elif newkillstreak == 5:
                                                    newwantedlevel = 1
                                                elif newkillstreak <= 7:
                                                    newwantedlevel = 2
                                                elif newkillstreak <= 9:
                                                    newwantedlevel = 3
                                                elif newkillstreak <= 11:
                                                    newwantedlevel = 4
                                                elif newkillstreak <= 13:
                                                    newwantedlevel = 5
                                                elif newkillstreak > 13:
                                                    newwantedlevel = 5
                                                else:
                                                    print("something went wrong with kill streak calculation")
                                                newbounty = newwantedlevel * 1000
                                                if newkillstreak > highestkillstreak:
                                                    dbCur.execute(
                                                        "UPDATE {servername}_wanted_players SET highestkillstreak = ? WHERE id =?".format(
                                                            servername=serverid), (newkillstreak, playerid))
                                                dbCur.execute(
                                                    "UPDATE {servername}_wanted_players SET wantedLevel =?, bounty =?, X =?, Y =? WHERE id =?".format(
                                                        servername=serverid),
                                                    (newwantedlevel, newbounty, KillLocationX, KillLocationY, playerid))

                                                # add coin for the kill
                                                if wantedLevel > 0:
                                                    dbCur.execute(
                                                        "SELECT walletbalance, earnratemultiplier FROM accounts WHERE conanplatformid =?",
                                                        (PlayerPlatformID[0],))
                                                    balance = dbCur.fetchone()
                                                    if balance is not None:
                                                        wantedKill = True
                                                        earnratemultiplier = balance[1]
                                                        newbalance = int(balance[0]) + newbounty
                                                        dbCur.execute(
                                                            "UPDATE accounts SET walletbalance =? WHERE conanplatformid =?",
                                                            (newbalance, PlayerPlatformID[0]))
                                                        dbCon.commit()
                                                        balance = balance[0]
                                                        wanted_paid_amount = (200 * earnratemultiplier)
                                                        newBalance = balance + wanted_paid_amount
                                                        dbCur.execute(
                                                            "UPDATE accounts SET walletBalance =? WHERE conanplatformid =?",
                                                            (newBalance, PlayerPlatformID[0]))
                                                        dbCon.commit()
                                                matchFound = 1
                                        if VictimPlatformID is not None and PlayerPlatformID is not None:
                                            if conanplatformid == VictimPlatformID[0]:
                                                # pay killer
                                                dbCur.execute(
                                                    "SELECT walletBalance, earnratemultiplier FROM accounts WHERE conanplatformid = ?",
                                                    (PlayerPlatformID[0],))
                                                walletDetails = dbCur.fetchone()
                                                if walletDetails is not None:
                                                    bountyKill = True
                                                    walletBalance = walletDetails[0]
                                                    earnratemultiplier = walletDetails[1]
                                                    bounty_paid_amount = (bounty * earnratemultiplier)
                                                    newBalance = walletBalance + bounty_paid_amount

                                                    dbCur.execute(
                                                        "UPDATE accounts SET walletBalance=? WHERE conanplatformid = ?",
                                                        (newBalance, PlayerPlatformID[0]))
                                                    dbCon.commit()
                                                    # clear wanted
                                                    dbCur.execute(
                                                        "UPDATE {servername}_wanted_players SET wantedLevel = '0' WHERE id =?".format(
                                                            servername=serverid), (playerid,))
                                                    dbCur.execute(
                                                        "UPDATE {servername}_wanted_players SET bounty = '0' WHERE id =?".format(
                                                            servername=serverid), (playerid,))
                                                    dbCur.execute(
                                                        "UPDATE {servername}_wanted_players SET killstreak = '0' WHERE id =?".format(
                                                            servername=serverid), (playerid,))
                                                    dbCon.commit()
                                                    matchFound = 1
                                    if matchFound == 0:
                                        # print("no existing wanted players found")
                                        dbCur.execute(
                                            "INSERT INTO {servername}_wanted_players (platformid, player, killstreak, highestkillstreak, wantedlevel, bounty, X, Y) VALUES (?,?,'1','1','0','0',?,?)".format(
                                                servername=serverid),
                                            (PlayerPlatformID[0], player, KillLocationX, KillLocationY))
                                        dbCon.commit()
                                else:
                                    # print("no existing wanted players found")
                                    dbCur.execute(
                                        "INSERT INTO {servername}_wanted_players (platformid, player, killstreak, highestkillstreak, wantedlevel, bounty, X, Y) VALUES (?,?,'1','1','0','0',?,?)".format(
                                            servername=serverid),
                                        (PlayerPlatformID[0], player, KillLocationX, KillLocationY))
                                    dbCon.commit()
                            # insert into recent pvp
                            now = datetime.now()
                            pvpmarkername = f"{player} vs {victim}"
                            dbCur.execute(
                                "INSERT INTO {servername}_recent_pvp (pvpname, x, y, loaddate) VALUES (?,?,?,?)".format(
                                    servername=serverid), (pvpmarkername, KillLocationX, KillLocationY, now))
                            dbCon.commit()

                            # record last event time to db
                            dbCur.execute(
                                "INSERT INTO {servername}_kill_log (player, player_id, player_level, player_clan, victim, victim_id, victim_level, victim_clan, kill_location_x, kill_location_y, kill_type, protected_area, wanted_kill, wanted_paid_amount, bounty_kill, bounty_paid_amount, Killlog_Last_Event_Time) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)".format(
                                    servername=serverid), (
                                    player, playerID, playerLevel, playerClan, victim, victimID, victimLevel,
                                    victimClan,
                                    KillLocationX, KillLocationY, killtype, ProtectedArea, wantedKill,
                                    wanted_paid_amount,
                                    bountyKill, bounty_paid_amount, Killlog_Last_Event_Time))
                            # update server's last event time
                            dbCur.execute("UPDATE servers SET Killlog_Last_Event_Time = ? WHERE serverName = ?",
                                          (Killlog_Last_Event_Time, serverid))
                            dbCon.commit()

            # close gamedb

            exiled_gamedb_con.close()

            killList = ''
        dbCur.close()
        dbCon.close()

        sleep(1)  # task runs every 1 seconds
