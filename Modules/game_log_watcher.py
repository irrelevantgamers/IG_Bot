from time import sleep


def game_log_watcher():
    import re
    import time
    import requests
    import json
    import sqlite3
    import os
    import configparser
    import mariadb
    import sys
    from datetime import datetime, timedelta, timezone


    # Get server id from config file and get server info from mariadb
    sys.path.insert(0, '..\\Modules')
    # read in the config variables from importconfig.py
    import config

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


    # check log filesize (for detect new logfile)
    global file_size_log
    file_size_log = os.stat(config.Server_Game_Log_Location).st_size
    # read logfile
    def read_log(logfile):
        global file_size_log
        logfile.seek(0, 2)
        while True:
            line = logfile.readline()
            if len(line) < 2:
                if file_size_log > os.stat(config.Server_Game_Log_Location).st_size:
                    print(os.stat(config.Server_Game_Log_Location).st_size)
                    exit()
                file_size_log = os.stat(config.Server_Game_Log_Location).st_size
                time.sleep(0.1)
                continue
            else:
                yield line

    def discord_message(message):
        try:
            connect_mariadb()
            mariaCur.execute("INSERT INTO {servername}_pendingDiscordMsg (message, destChannelID, sent) VALUES (?,?,?)".format(servername=config.Server_Name), (message, config.Discord_ServerLog_Channel, False))
            mariaCon.commit()
            close_mariaDB()
        except Exception as e:
            print(f"an error occurred while sending the discord message: {e}")
            pass

    def save_log(loglist):
        try:
            # open db connection
            connection = sqlite3.connect('..\\Modules\\connectionlog.db')
            cursor = connection.cursor()

            if loglist[0] == "connection":
                cursor.execute(f"INSERT INTO connection (type, name, steamid, ip, time) VALUES ('{loglist[1]}', '{loglist[2]}', '{loglist[3]}', '{loglist[4]}', '{loglist[5]}')")
                connection.commit()

            # close db connection
            cursor.close()
            connection.close()

        except sqlite3.Error:
            print("an error occurred while opening/write the logdatabase")
            pass

    # convert time
    def convert_time(time):
        time = datetime.strptime(time, "%Y.%m.%d-%H.%M.%S:%f") + timedelta(hours=config.Time_Timezone)
        time = time.strftime("%Y-%m-%d %H:%M:%S")
        return time

    def register(inputcode):
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
        dbCur.execute("SELECT discordID, discordObjID, registrationcode FROM registration_codes WHERE curstatus = FALSE")
        results = dbCur.fetchall()
        for row in results:
            discordID = row[0]
            discordObjID = row[1]
            code = row[2]

            if code == inputcode:
                try:
                    # open db connection
                    connection = sqlite3.connect(config.Server_Game_DB_Location)
                    cursor = connection.cursor()

                    
                    #find character ID
                    #cursor.execute(f"SELECT id FROM characters WHERE char_name ='{log_character[0]}'")
                    cursor.execute(f"SELECT c.id, c.playerid, c.char_name, a.user as PlatformID FROM characters c LEFT JOIN account a on c.playerid = a.id WHERE c.char_name =?", (log_character[0], ))
                    result_id = cursor.fetchone()
                    #print(f"Character-ID: {result_id[0]}")
                    #print(f"Character-Player-ID: {result_id[1]}")
                    #print(f"Character-Name: {result_id[2]}")
                    #print(f"Platform-ID: {result_id[3]}")
                    
                    platformid = result_id[3]

                    cursor.close()
                    connection.close()
                    print(f"Setting discord ID to {discordID} for {platformid} - {result_id[2]}")
                    dbCur.execute("UPDATE accounts SET discordid = ? WHERE conanplatformid = ?", (discordID, platformid))
                    dbCon.commit()

                    #check if registration successful 
                    dbCur.execute("Select discordid FROM accounts WHERE conanplatformid = ?", (platformid, ))
                    checkResult = dbCur.fetchone()
                    if checkResult == None:
                        print("could not register user. Perhaps not in account list yet")
                    else:
                        #delete registration code and send notify message
                        dbCur.execute("INSERT INTO {server}_pendingDiscordMsg (message, messageType, destChannelID, sent) VALUES (?,?,?,?)".format(server=config.Server_Name), (f"{log_character[0]} registration confirmed!", 'DM', discordID, False))
                        dbCur.execute("DELETE FROM registration_codes WHERE discordID = ?", (discordID, ))
                        dbCon.commit()
                except Exception as e:
                    print(e)
                    pass
        dbCon.close()

    def TeleportHome(player):
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
        #find user
        dbCur.execute("SELECT platformid FROM {server}_currentusers WHERE player=?".format(server=config.Server_Name), (player, ))
        result = dbCur.fetchone()
        if result == None:
            print(f"{player} is not in the current users list cant send home")
            return
        else:
            platformid = result[0]

            dbCur.execute("SELECT homelocation FROM {server}_homelocations WHERE platformid =?".format(server=config.Server_Name), (platformid, ))
            results = dbCur.fetchone()
            if results == None:
                print(f"{player} is not in the homelocations list cant send home")
                return
            else:
                home = results[0]
                print(f"{player} home location is {home}")
                #check if active event, arena, or vault
                homeAllowed = False
                dbCur.execute("SELECT ID FROM {server}_event_details WHERE isActive =True AND HomeAllowed =True".format(server=config.Server_Name))
                result = dbCur.fetchone()
                if result != None:
                    homeAllowed = True
                dbCur.execute("SELECT ID FROM {server}_arenas WHERE isActive =True AND HomeAllowed =True".format(server=config.Server_Name))
                result = dbCur.fetchone()
                if result != None:
                    homeAllowed = True
                dbCur.execute("SELECT ID FROM {server}_vault_rentals WHERE inUse =True AND renterplatformid =?".format(server=config.Server_Name), (platformid, ))
                result = dbCur.fetchone()
                if result != None:
                    homeAllowed = True
                    dbCur.execute("UPDATE {server}_vault_rentals SET inUse =False WHERE renterplatformid =?".format(server=config.Server_Name), (platformid, ))
                    dbCon.commit()
                if homeAllowed == True:
                    dbCur.execute("INSERT INTO {server}_teleport_requests (player, dstlocation, platformid) VALUES (?,?,?)".format(server=config.Server_Name), (player, home, platformid))
                    dbCon.commit()
                    discord_message(f"{player} has been sent home")
                else:
                    print(f"{player} is not allowed to teleport home")
                    discord_message(f"{player} tried to teleport home but is not allowed to do so")
        dbCon.close()
    def RegisterHomeLocation(player):
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
        #get player's current location
        # open db connection
        connection = sqlite3.connect(config.Server_Game_DB_Location)
        cursor = connection.cursor()
        
         #find character ID
        cursor.execute(f"SELECT c.id, c.playerid, c.char_name, a.user as PlatformID FROM characters c LEFT JOIN account a on c.playerid = a.id WHERE c.char_name =? AND a.online ='1'", (log_character[0], ))
        result_id = cursor.fetchone()

        platformid = result_id[3]
        
        #find XYZ of character
        cursor.execute(f"select (X || ' ' || Y || ' ' || Z) as XYZ FROM actor_position WHERE id ={result_id[0]}")
        location = cursor.fetchone()[0]

        #find user in current users
        dbCur.execute("SELECT platformid FROM {server}_currentusers WHERE player=?".format(server=config.Server_Name), (player, ))
        result = dbCur.fetchone()
        if result == None:
            print(f"{player} is not in the current users list cant register home")
            return
        else:
            platformid = result[0]

            dbCur.execute("SELECT homelocation FROM {server}_homelocations WHERE platformid =?".format(server=config.Server_Name), (platformid, ))
            results = dbCur.fetchone()
            if results == None:
                print(f"{player} is not in the homelocations creating a new location")
                dbCur.execute("INSERT INTO {server}_homelocations (player, homelocation, platformid) VALUES (?,?,?)".format(server=config.Server_Name), (player, location, platformid))
                dbCon.commit()
                discord_message(f"{player} registered their home location as {location}")
            else:
                dbCur.execute("UPDATE {server}_homelocations SET homelocation =? WHERE platformid =?".format(server=config.Server_Name), (location, platformid))
                dbCon.commit()
                discord_message(f"{player} updated their home location to {location}")
        dbCon.close()

    def teleportToEvent(teleTarget, player):
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
        #get player's current location
        # open db connection
        connection = sqlite3.connect(config.Server_Game_DB_Location)
        cursor = connection.cursor()
        
         #find character ID
        cursor.execute(f"SELECT c.id, c.playerid, c.char_name, a.user as PlatformID FROM characters c LEFT JOIN account a on c.playerid = a.id WHERE c.char_name =? AND a.online ='1'", (log_character[0], ))
        result_id = cursor.fetchone()

        platformid = result_id[3]
        
        #find XYZ of character
        cursor.execute(f"select (X || ' ' || Y || ' ' || Z) as XYZ FROM actor_position WHERE id ={result_id[0]}")
        location = cursor.fetchone()[0]

        #find user in current users
        dbCur.execute("SELECT platformid FROM {server}_currentusers WHERE player=?".format(server=config.Server_Name), (player, ))
        result = dbCur.fetchone()
        if result == None:
            print(f"{player} is not in the current users list cant register home")
            return
        else:
            platformid = result[0]
            #get event general location
            dbCur.execute("SELECT {location} FROM {server}_event_details WHERE isActive =True".format(location=teleTarget,server=config.Server_Name))
            result = dbCur.fetchone()
            if result == None:
                print(f"No active event found")
            else:
                dbCur.execute("INSERT INTO {server}_teleport_requests (player, dstlocation, platformid) VALUES (?,?,?)".format(server=config.Server_Name), (player, result[0], platformid))
                dbCon.commit()
                discord_message(f"{player} has been sent to the event {teleTarget}")
        dbCon.close()


    while True:
        try:
            temp_player = ""

            # open logfile
            try:
                logfile = open(config.Server_Game_Log_Location, "r", encoding="utf-8", errors="ignore")
            except OSError as err:
                print(f"an error occurred while opening the logfile ({err})")
                #exit()
                pass

            # read logfile line
            for line in read_log(logfile):

                # detect Chatmessages
                if "ChatWindow" in line:
                    log_time = re.findall("\[(.*?)\]", line)
                    log_character = re.findall("(?<=Character )(.*)(?= said)", line)
                    log_text = re.findall("(?<=said: )(.*)", line)

                    # convert datetime
                    log_time = convert_time(log_time[0])

                    # send msg to discord
                    msg = f"{log_time} :speech_balloon: {log_character[0]}: {log_text[0]}"
                    discord_message(msg)

                    print(f"Chat: {log_character[0]} ({log_text[0]})")
                
                    # detect registration requests
                    if "!register " in log_text[0]:
                        inputcode = log_text[0]
                        inputcode = inputcode.strip("!register ")  
                        register(inputcode)  
                    if log_text[0] == "!beammeup":
                        print(log_text[0])
                        print(f"Teleport request received by: {log_character[0]} ({log_text[0]})")
                        teleTarget = "GeneralLocation"
                        teleportToEvent(teleTarget, log_character[0])
                
                    if log_text[0] ==  "!redteam":
                        print(f"Teleport request received by: {log_character[0]} ({log_text[0]})")
                        teleTarget = "RedTeamLocation"
                        teleportToEvent(teleTarget, log_character[0])

                    if log_text[0] == "!blueteam":
                        print(f"Teleport request received by: {log_character[0]} ({log_text[0]})")
                        teleTarget = "BlueTeamLocation"
                        teleportToEvent(teleTarget, log_character[0])

                    if log_text[0] == "!spectate":
                        print(f"Teleport request received by: {log_character[0]} ({log_text[0]})")
                        teleTarget = "SpectateLocation"
                        teleportToEvent(teleTarget, log_character[0])

                    # detect home request
                    if log_text[0] ==  "!home":
                        print(f"Teleport request received by: {log_character[0]} ({log_text[0]})")
                        TeleportHome(log_character[0])

                    # detect home location registration
                    if log_text[0] == "!registerhome":
                        print(f"Request to register/update home location received by: {log_character[0]} ({log_text[0]})")
                        RegisterHomeLocation(log_character[0])


                # detect Error
                if "Error: Unhandled Exception:" in line:
                    log_time = re.findall("\[(.*?)\]", line)
                    log_error = re.findall("(?<=Unhandled Exception: )(.*)", line)

                    # convert datetime
                    log_time = convert_time(log_time[0])

                    # send msg to discord
                    msg = (f"{log_time} :warning: {log_error[0]}")
                    discord_message(msg)

                    print(f"Error: {log_error[0]}")

                # detect Shutdown
                if "LogExit: Game engine shut down" in line:
                    log_time = re.findall("\[(.*?)\]", line)

                    # convert datetime
                    log_time = convert_time(log_time[0])

                    # send msg to discord
                    msg = (f"{log_time} :o2: Engine shutdown")
                    discord_message(msg)

                    print(f"Engine shutdown")

                # detect Serverloaded
                if "LogLoad: (Engine Initialization)" in line:
                    log_time = re.findall("\[(.*?)\]", line)

                    # convert datetime
                    log_time = convert_time(log_time[0])

                    # send msg to discord
                    msg = (f"{log_time} :white_check_mark: Engine loaded")
                    discord_message(msg)

                    print(f"Engine loaded")

                # detect New Player
                if "Join succeeded:" in line:
                    log_time = re.findall("\[(.*?)\]", line)
                    temp_player = re.findall("(?<=Join succeeded: )(.*)", line)

                if "Telling client to start Character Creation." in line:
                    log_time = re.findall("\[(.*?)\]", line)
                    log_character = temp_player

                    # convert datetime
                    log_time = convert_time(log_time[0])

                    # send msg to discord
                    msg = (f"{log_time} :new: {log_character[0]}")
                    discord_message(msg)

                    print(f"New: {log_character[0]}")

                # detect IP
                if "BattlEyeServer: Print Message: Player " in line:
                    log_ip = re.findall("(?<= \()(.*)(?=\:)", line)

                # detect Connect
                if "BattlEyeLogging: BattlEyeServer: Registering player" in line:
                    log_time = re.findall("\[(.*?)\]", line)
                    log_steamid = re.findall("(?<=BattlEyePlayerGuid )(.*)(?= and)", line)
                    log_character = re.findall("(?<=name \')(.*)(?=\')", line)

                    if not len(log_character) == 0:
                        # convert datetime
                        log_time = convert_time(log_time[0])

                        # send msg to discord
                        msg = (f"{log_time} :green_square: {log_character[0]} (SteamID: {log_steamid[0]} | IP: {log_ip[0]})")
                        discord_message(msg)

                        # save to sqlite database
                        save_log(["connection", "connect", log_character[0], log_steamid[0], log_ip[0], log_time])

                        print(f"Connect: {log_character[0]} ({log_steamid[0]} | {log_ip[0]})")

                # detect Disconnect
                if " disconnected" in line:
                    log_time = re.findall("\[(.*?)\]", line)
                    log_character = re.findall("(?<=Player #[0-9] )(.*)(?= disconnected)", line)

                    if len(log_character) == 0:
                        log_character = re.findall("(?<=Player #[0-9][0-9] )(.*)(?= disconnected)", line)
                    if len(log_character) == 0:
                        log_character = re.findall("(?<=Player #[0-9][0-9][0-9] )(.*)(?= disconnected)", line)
                    if not len(log_character) == 0:

                        # convert datetime
                        log_time = convert_time(log_time[0])

                        # send msg to discord
                        msg = (f"{log_time} :red_square: {log_character[0]}")
                        discord_message(msg)

                        # save to sqlite database
                        save_log(["connection", "disconnect", log_character[0], "", "", log_time])

                        print(f"Disconnect: {log_character[0]}")

                # detect Purge Started
                if "Purge Started" in line:
                    log_time = re.findall("\[(.*?)\]", line)
                    log_clanid = re.findall("(?<=for Clan )(.*)(?=,)", line)
                    log_x = re.findall("(?<=X=)(.*)(?=, Y)", line)
                    log_y = re.findall("(?<=, Y=)(.*)(?=, Z)", line)
                    log_wave = re.findall("(?<=Using Wave )(.*)", line)

                    # convert datetime
                    log_time = convert_time(log_time[0])

                    try:
                        # open db connection
                        connection = sqlite3.connect(config.Server_Game_DB_Location)
                        cursor = connection.cursor()

                        # search clan or player
                        cursor.execute(f"SELECT name FROM guilds WHERE guildId ={log_clanid[0]}")
                        result_clan = cursor.fetchone()
                        cursor.execute(f"SELECT char_name FROM characters WHERE id ={log_clanid[0]}")
                        result_player = cursor.fetchone()

                        if not result_clan == None:
                            log_name = result_clan[0]
                        if not result_player == None:
                            log_name = result_player[0]

                        # close db connection
                        cursor.close()
                        connection.close()

                    except sqlite3.Error:
                        print("an error occurred while opening the serverdatabase")
                        log_name = "Unknown"
                        pass

                    # send msg to discord
                    msg = (f"{log_time} :crossed_swords: {log_name}, {log_wave[0]} (X: {log_x[0]} | Y: {log_y[0]})")
                    discord_message(msg)

                    print(f"Purge Started: {log_name} - {log_wave[0]} (X: {log_x[0]} | Y: {log_y[0]})")

                # detect Purge Failed
                if "Purge Failed" in line:
                    log_time = re.findall("\[(.*?)\]", line)
                    log_clanid = re.findall("(?<=for Clan )(.*)(?=, At)", line)
                    log_reason = re.findall("(?<=, Reason )(.*)", line)

                    # convert datetime
                    log_time = convert_time(log_time[0])

                    try:
                        # open db connection
                        connection = sqlite3.connect(config.Server_Game_DB_Location)
                        sqlite3_cursor = connection.cursor()

                        # search clan or player
                        sqlite3_cursor.execute(f"SELECT name FROM guilds WHERE guildId ={log_clanid[0]}")
                        result_clan = sqlite3_cursor.fetchone()
                        sqlite3_cursor.execute(f"SELECT char_name FROM characters WHERE id ={log_clanid[0]}")
                        result_player = sqlite3_cursor.fetchone()

                        if not result_clan == None:
                            log_name = result_clan[0]
                        if not result_player == None:
                            log_name = result_player[0]

                        # close db connection
                        sqlite3_cursor.close()
                        connection.close()

                    except sqlite3.Error:
                        print("an error occurred while opening the serverdatabase")
                        log_name = "Unknown"
                        pass

                    # send msg to discord
                    msg = (f"{log_time} :crossed_swords: {log_name} ({log_reason[0]})")
                    discord_message(msg)

                    print(f"Purge Failed: {log_name} ({log_reason[0]})")
        except Exception as e:
            print(f"Game Log Watcher Error: {e}")
            pass
