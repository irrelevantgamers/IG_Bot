import asyncio
from time import sleep
import mariadb
import sqlite3
import configparser
import sys
from datetime import datetime, timedelta
#Get server id from config file and get server info from mariadb
sys.path.insert(0, '..\\Modules')
#read in the config variables from importconfig.py
from importconfig import *

def connect_mariadb():
    global mariaCon
    global mariaCur
    try:
        mariaCon = mariadb.connect(
            user=DB_user,
            password=DB_pass,
            host=DB_host,
            port=DB_port,
            database=DB_name

        )
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)
    mariaCur = mariaCon.cursor()

def close_mariaDB():
    mariaCur.close()
    mariaCon.close()


def kill_stream():
    
    print ("Exiled Kill Stream Started")
    while True:
        #read in last event time
        connect_mariadb()
        mariaCur.execute("SELECT DatabaseLocation, Killlog_Last_Event_Time, serverName FROM servers WHERE id = ?", (Server_ID,))
        server_info = mariaCur.fetchone()
        if len(server_info) != 0 and server_info[0] != None:

            gamedb_file = server_info[0]
            serverid = server_info[2]
            Killlog_Last_Event_Time = datetime.timestamp(server_info[1])

            exiled_gamedb_con = sqlite3.connect(gamedb_file)
            exiled_gamedb_cur = exiled_gamedb_con.cursor()
            kills = exiled_gamedb_cur.execute("select worldTime, ukill.causerName, ukill.causerID, causerGuildName, ukill.ownerName, ukill.ownerId, ownerGuildName, ukill.x as X, ukill.y as Y FROM (select distinct x, y, z, causerName, causerId, causerGuildName, ownerName, ownerId from game_events where eventType = 103 AND causerName != '' AND ownerName != '') as ukill  join (SELECT worldTime, x, y, z, causerName, causerId, ownerName, ownerId, ownerGuildName FROM game_events WHERE eventType = 103 AND causerName != '' AND ownerName != '') using (x, y, z) where datetime(worldTime,'unixepoch') >= datetime('now', '-1 Day') group by x ,y ,z order by worldTime DESC LIMIT 20")
            
            list = ''
            
            for row in kills.fetchall():
                if row[0] > Killlog_Last_Event_Time:
                    eventTime = row[0]
                    Killlog_Last_Event_Time = eventTime
                    player = row[1]
                    playerID = row[2]
                    playerClan = row[3]
                    victim = row[4]
                    victimID = row[5]
                    victimClan = row[6]
                    KillLocationX = row[7]
                    KillLocationY = row[8]

                    if playerClan == '':
                        playerClan = 'N\\A'
                
                    if victimClan == '':
                        victimClan = 'N\\A'

                    if playerClan == victimClan and playerClan != 'N\\A':
                        sameClan = True
                    else:
                        sameClan = False

                    playerLevel = exiled_gamedb_cur.execute("Select level FROM characters WHERE char_name =?", (player, ))
                    playerLevel = playerLevel.fetchone()
                    playerLevel = playerLevel[0]
                    victimLevel = exiled_gamedb_cur.execute("Select level FROM characters WHERE char_name =?", (victim, ))
                    victimLevel = victimLevel.fetchone()
                    victimLevel = victimLevel[0]
                    print(f"Victim Level: {victimLevel}")
                    print(f"Player Level: {playerLevel}")

                    #get account id and platformid from the playerid
                    #Killers PlatformID
                    try:
                        exiled_gamedb_cur.execute(f"SELECT a.user FROM characters c LEFT JOIN account a on c.playerid = a.id WHERE c.id =?", (playerID, ))
                        PlayerPlatformID = exiled_gamedb_cur.fetchone()
                        print(PlayerPlatformID)
                        #victims PlatformID
                        exiled_gamedb_cur.execute(f"SELECT a.user FROM characters c LEFT JOIN account a on c.playerid = a.id WHERE c.id =?", (victimID, ))
                        VictimPlatformID = exiled_gamedb_cur.fetchone()
                        print(VictimPlatformID)
                    except Exception:
                        print("Failed to process platform ids")
                        pass

                    #get protected areas
                    try:
                        mariaCur.execute("SELECT name, minX, minY, maxX, maxY FROM ?_protected_areas", (serverid, ))
                        protectedareas = mariaCur.fetchall()

                        for area in protectedareas:
                            areaName = area[0]
                            minX = area[1]
                            minY = area[2]
                            maxX = area[3]
                            maxY = area[4]

                            if ((int(KillLocationX) <= int(maxX)) and (int(KillLocationX) >= int(minX)) and (int(KillLocationY) <= int(maxY)) and (int(KillLocationY) >= int(minY))):
                                try:
                                    mariaCur.execute("INSERT INTO ?_offenders (conanPlayerName, conanPlatformID, strikes, offenses) VALUES (?,?,1,1)", (serverid, player, PlayerPlatformID[0]))
                                    mariaCon.commit()
                                except Exception as e:
                                    if "Duplicate" in str(e):
                                        mariaCur.execute("SELECT strikes, offenses FROM ?_offenders WHERE conanPlatformID =?", (serverid, PlayerPlatformID[0], ))
                                        info = mariaCur.fetchone()
                                        strikes = info[0]
                                        offenses = info[1]
                                        newStrikes = int(strikes) + 1
                                        newOffenses = int(offenses) + 1
                                        mariaCur.execute("UPDATE ?_offenders SET strikes =?, offenses =? WHERE conanPlatformID =?", (serverid, newStrikes, newOffenses, PlayerPlatformID[0]))
                                        mariaCon.commit()
                                        pass
                                    else:
                                        print(e)
                                        pass
                                list = list + (f"**PROTECTED AREA KILL DETECTED AT {areaName} STRIKE HAS BEEN ISSUED**\n")

                        #check for kill streaks
                        wantedKill = False
                        if sameClan:
                            print("skipping kill streak count, same clan")
                        else:
                            print("checking kill streaks")
                            matchFound = 0
                            mariaCur.execute("SELECT id, conanplatformid, conanplayer, killstreak, highestkillstreak, wantedLevel, bounty FROM ?_wanted_players",(serverid,))
                            wanted = mariaCur.fetchall()
                            rowcount = len(wanted)
                            if rowcount != 0:
                                print("existing Wanted players found")
                                for result in wanted:
                                    playerid = result[0]
                                    conanplatformid = result[1]
                                    conanplayer = result[2]
                                    killstreak = result[3]
                                    highestkillstreak = result[4]
                                    wantedLevel = result[5]
                                    bounty = result[6]
                                    if conanplatformid == PlayerPlatformID[0]:
                                        newkillstreak = int(killstreak) + 1
                                        mariaCur.execute("UPDATE ?_wanted_players SET killstreak =? WHERE id =?",(serverid, newkillstreak, playerid))
                                        
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
                                            mariaCur.execute("UPDATE ?_wanted_players SET highestkillstreak = ? WHERE id =?",(serverid, newkillstreak, playerid))
                                        mariaCur.execute("UPDATE ?_wanted_players SET wantedLevel =? WHERE id =?",(serverid, newwantedlevel, playerid))
                                        mariaCur.execute("UPDATE ?_wanted_players SET bounty =? WHERE id =?",(serverid, newbounty, playerid))
                                        #add coin for the kill
                                        if wantedLevel > 0:
                                            wantedKill = True
                                            mariaCur.execute("SELECT walletbalance FROM accounts WHERE conanplatformid =?",(PlayerPlatformID[0], ))
                                            balance = mariaCur.fetchone()
                                            balance = balance[0]
                                            newBalance = balance + 200
                                            mariaCur.execute("UPDATE accounts SET walletBalance =? WHERE conanplatformid =?",(newBalance, PlayerPlatformID[0]))
                                            mariaCon.commit()
                                        matchFound = 1
                                    if conanplatformid == VictimPlatformID[0]:
                                        #pay killer
                                        #add user to mariadb account if it doesn't exist
                                        mariaCur.execute("SELECT walletBalance, multiplier FROM accounts WHERE conanplatformid = ?", (PlayerPlatformID[0], ))
                                        walletDetails = mariaCur.fetchone()
                                        walletBalance = walletDetails[0]
                                        newBalance = walletBalance + bounty
                                        mariaCur.execute("UPDATE accounts SET walletBalance=? WHERE conanplatformid = ?", (newBalance, PlayerPlatformID[0]))
                                        mariaCon.commit()
                                        #clear wanted
                                        mariaCur.execute("UPDATE ?_wanted_players SET wantedLevel = '0' WHERE id =?",(serverid, playerid))
                                        mariaCur.execute("UPDATE ?_wanted_players SET bounty = '0' WHERE id =?",(serverid, playerid))
                                        mariaCur.execute("UPDATE ?_wanted_players SET killstreak = '0' WHERE id =?",(serverid, playerid))
                                        mariaCon.commit()
                                        matchFound = 1
                                if matchFound == 0:
                                    print("no existing wanted players found")
                                    mariaCur.execute("INSERT INTO ?_wanted_players (conanplatformid, conanplayer, killstreak, highestkillstreak, wantedlevel, bounty) VALUES (?,?,'1','1','0','0')",(serverid, PlayerPlatformID[0],player))
                                    mariaCon.commit()
                            else:
                                print("no existing wanted players found")
                                mariaCur.execute("INSERT INTO ?_wanted_players (conanplatformid, conanplayer, killstreak, highestkillstreak, wantedlevel, bounty) VALUES (?,?,'1','1','0','0')",(serverid, PlayerPlatformID[0],player))
                                mariaCon.commit()
                        #insert into recent pvp
                        now = datetime.now()
                        pvpmarkername = f"{player} vs {victim}"
                        mariaCur.execute("INSERT INTO ?_recent_pvp (name, x, y, datetime) VALUES (?,?,?,?)",(serverid, pvpmarkername, int(KillLocationX), int(KillLocationY), now))
                        mariaCon.commit()
                    except Exception as e:
                        print(f"couldn't connect to mariaDB {e}")
                        pass

                    #record last event time to db
                    Killlog_Last_Event_Time = datetime.timestamp(eventTime)
                    mariaCur.execute("INSERT INTO servers (player, player_id, player_level, player_clan, victim, victim_id, victim_level, victim_clan, kill_location_x, kill_location_y) Killlog_Last_Event_Time = ? WHERE id =?",(serverid, Killlog_Last_Event_Time, ))
                    mariaCon.commit()
                    
            #close gamedb

            exiled_gamedb_con.close()
            
            list = ''
        
        close_mariaDB()
            
        sleep(1) #task runs every 1 seconds


kill_stream()