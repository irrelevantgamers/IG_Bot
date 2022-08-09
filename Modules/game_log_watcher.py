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
        dbCur.execute("SELECT discordID, registrationcode FROM registration_codes WHERE status = FALSE")
        results = dbCur.fetchall()
        for row in results:
            discordID = row[0]
            code = row[1]

            if code == inputcode:
                try:
                    # open db connection
                    connection = sqlite3.connect(config.Server_Game_DB_Location)
                    cursor = connection.cursor()

                    
                    #find character ID
                    #cursor.execute(f"SELECT id FROM characters WHERE char_name ='{log_character[0]}'")
                    cursor.execute(f"SELECT c.id, c.playerid, c.char_name, a.user as PlatformID FROM characters c LEFT JOIN account a on c.playerid = a.id WHERE c.char_name =?", (log_character[0], ))
                    result_id = cursor.fetchone()
                    print(f"Character-ID: {result_id[0]}")
                    print(f"Character-Player-ID: {result_id[1]}")
                    print(f"Character-Name: {result_id[2]}")
                    print(f"Platform-ID: {result_id[3]}")
                    
                    platformid = result_id[3]

                    cursor.close()
                    connection.close()
                    print(f"Setting discord ID to {discordID} for {platformid}")
                    dbCur.execute("UPDATE accounts SET discordid = ? WHERE conanplatformid = ?", (discordID, platformid))
                    dbCon.commit()

                    #check if registration successful 
                    dbCur.execute("Select discordid FROM accounts WHERE conanplatformid = ?", (platformid, ))
                    checkResult = dbCur.fetchone()
                    if checkResult == None:
                        print("could not register user. Perhaps not in account list yet")
                    else:
                        #update registration status
                        dbCur.execute("UPDATE registrationcodes SET status = 1 WHERE registrationCode = ?", (inputcode, ))
                        dbCon.commit()
                except Exception as e:
                    print(e)
                    pass
                dbCon.close()

    if __name__ == "game_log_watcher":
        temp_player = ""

        # open logfile
        try:
            logfile = open(config.Server_Game_Log_Location, "r", encoding="utf-8", errors="ignore")
        except OSError as err:
            print(f"an error occurred while opening the logfile ({err})")
            exit()

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
