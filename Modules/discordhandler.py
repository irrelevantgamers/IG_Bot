from pickle import FALSE
from re import M


def discord_bot():
    from asyncio.windows_events import NULL
    from subprocess import Popen
    from unicodedata import name
    import discord
    from discord.ext import commands
    from discord.utils import get
    import asyncio
    import sqlite3
    from sqlite3 import Error
    import valve.rcon
    import sys
    import mariadb
    import re
    import random
    import string

    # Get server id from config file and get server info from mariadb
    sys.path.insert(0, '..\\Modules')
    # read in the config variables from importconfig.py
    import config

    intents = discord.Intents.default()
    intents.members = True
    client = discord.Client(intents=intents)

    def clean_text(rgx_list, text):
        new_text = text
        for rgx_match in rgx_list:
            new_text = re.sub(rgx_match, '', new_text)
        return new_text

    async def player_count_refresh():

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
            dbCur.execute("Select servername FROM servers WHERE Enabled =True")
            servers = dbCur.fetchall()
            player_count = 0
            if servers != None:
                for server in servers:
                    servername = server[0]
                    try:
                        # connect to exiled for info
                        dbCur.execute("SELECT conid FROM {server}_currentusers".format(server=servername))
                        players = dbCur.fetchall()
                        player_count = player_count + len(players)
                        
                    except Exception as e:
                        print(f"Error updating player count for discord status: {e}")
                        pass
            print("Updating player count for discord status")
            await client.change_presence(
                activity=discord.Activity(type=discord.ActivityType.watching, name="{} online".format(player_count)))
            dbCon.close()
            await asyncio.sleep(60)  # task runs every 60 seconds

    async def registrationWatcher():
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
            # find complete registrations
            dbCur.execute("SELECT * FROM registration_codes WHERE status = 1")
            completed = dbCur.fetchall()
            messageSent = 0
            if completed != None:
                for user in completed:
                    if messageSent == 0:
                        discordID = user[0]
                        discordObjID = user[1]
                        #print(f"Discord ID is {discordID}")
                        #print(f"Discord Object ID is {discordObjID}")

                        members = client.get_all_members()
                        for member in members:
                            if (discordID == str(member)) and (messageSent == 0):
                                print(f"inside {member}")
                                await member.send("Registration Complete")
                                dbCur.execute("DELETE FROM registrationcodes WHERE discordID = ?", (discordID,))
                                dbCon.commit()
                                messageSent = 1
            dbCur.close()
            dbCon.close()
            await asyncio.sleep(5)  # task runs every 5 seconds

    async def pending_Message_Watcher():
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
            dbCur.execute("Select servername FROM servers WHERE Enabled =True")
            servers = dbCur.fetchall()
            if servers != None:
                for server in servers:
                    serverName = server[0]
                    try:
                        dbCur.execute("SELECT * FROM {servername}_pendingdiscordmsg WHERE sent =FALSE ORDER BY loadDate ASC".format(servername=serverName))
                        messages = dbCur.fetchall()
                        if messages != None:
                            for message in messages:
                                destChannel = message[1]
                                messageText = message[2]
                                messageType = message[3]
                                if messageType == 'General':
                                    channel = client.get_channel(int(destChannel))
                                    await channel.send("{msg}".format(msg=messageText))
                                    dbCur.execute("UPDATE {servername}_pendingdiscordmsg SET sent = TRUE WHERE ID = ?".format(servername=serverName), (message[0],))
                                    dbCon.commit()
                                if messageType == 'DM':
                                    members = client.get_all_members()
                                    DMSent = 0
                                    for member in members:
                                        if (destChannel == str(member)) and (DMSent == 0):
                                            await member.send("{msg}".format(msg=messageText))
                                            dbCur.execute("UPDATE {servername}_pendingdiscordmsg SET sent = TRUE WHERE ID = ?".format(servername=serverName), (message[0],))
                                            dbCon.commit()
                                            DMSent = 1
                            dbCur.execute("DELETE FROM {servername}_pendingdiscordmsg WHERE sent = TRUE".format(servername=serverName))
                            dbCon.commit()
                    except Exception as e:
                        print(f"Error sending pending discord messages: {e}")
                        pass
            dbCur.close()
            dbCon.close()
            await asyncio.sleep(1)  # task runs every 5 seconds
   
    async def kill_log_watcher():
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
            dbCur = dbCon.cursor()
            dbCur.execute("Select servername, Killlog_Channel, Event_Channel FROM servers WHERE Enabled =True")
            servers = dbCur.fetchall()
            if servers != None:
                for server in servers:
                    serverName = server[0]
                    killlog_channel = int(server[1])
                    event_channel = int(server[2])
                    try:
                        
                        # find complete registrations
                        dbCur.execute(
                            "SELECT * FROM {servername}_kill_log WHERE discord_notified = 0 ORDER BY Killlog_Last_event_Time ASC LIMIT 1".format(
                                servername=serverName))
                        kills = dbCur.fetchall()
                        if kills is not None and len(kills) != 0:
                            for kill in kills:
                                list = ''
                                id = kill[0]
                                player = kill[1]
                                player_id = kill[2]
                                player_level = kill[3]
                                player_clan = kill[4]
                                victim = kill[5]
                                victim_id = kill[6]
                                victim_level = kill[7]
                                victim_clan = kill[8]
                                kill_type = kill[11]
                                protected_area = kill[12]
                                wanted_kill = kill[13]
                                wanted_paid_amount = kill[14]
                                bounty_kill = kill[14]
                                bounty_amount = kill[15]

                                if kill_type == "ProtectedArea":
                                    channel = client.get_channel(killlog_channel)
                                    list = list + (
                                        f"**PROTECTED AREA KILL DETECTED AT {protected_area} STRIKE HAS BEEN ISSUED**\n")
                                if kill_type == "Normal":
                                    channel = client.get_channel(killlog_channel)
                                    list = list + (
                                        '⚔️**{}** of clan **{}** killed **{}** of clan **{}**⚔️\n'.format(player, player_clan,
                                                                                                        victim, victim_clan))
                                if kill_type == "Event":
                                    channel = client.get_channel(event_channel)
                                if kill_type == "Arena":
                                    channel = client.get_channel(event_channel)

                                if wanted_kill == True:
                                    list = list + (
                                        '🔥**{}** earned {} {} for killing while wanted🔥\n'.format(player, wanted_paid_amount,
                                                                                                    config.Shop_CurrencyName))

                                await channel.send(list)
                                dbCur.execute("UPDATE {servername}_kill_log SET discord_notified = 1 WHERE id = ?".format(
                                    servername=serverName), (id,))
                                dbCon.commit()

                    except Exception as e:
                        print(f"Kill_Log_Watcher_error: {e}")
                        sys.exit(1)
            dbCur.close()
            dbCon.close()
            await asyncio.sleep(1)  # task runs every 1 seconds

    @client.event
    async def on_ready():
        print('We have logged in as {0.user}'.format(client))
        await client.change_presence(activity=discord.Game(name="Conan Exiles"))
        client.loop.create_task(player_count_refresh())
        client.loop.create_task(registrationWatcher())
        client.loop.create_task(kill_log_watcher())
        client.loop.create_task(pending_Message_Watcher())

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return

        if message.content.startswith('!intro'):
            await message.channel.send(
                'Hi I\'m Pythios, a Discord bot currently being developed by SubtleLunatic. I can\'t do a lot yet but i\'m still young.')

        if message.content == '!register':
            discordID = message.author.name + '#' + message.author.discriminator
            discordObjID = message.author.id
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

            # Create registration code
            N = 6
            code = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(N))
            #print(code)

            # Get MariaCursor
            dbCur = dbCon.cursor()

            # insert code with associated discord ID
            try:
                dbCur.execute("INSERT INTO registration_codes (discordID, discordObjID, registrationCode, status) VALUES (?, ?, ?, FALSE)",
                                (discordID, discordObjID, code))
                dbCon.commit()
            except Exception as e:
                if "Duplicate" in str(e):
                    print("found duplicate updating registration code")
                    dbCur.execute("UPDATE registration_codes SET registrationcode = ? WHERE discordID = ?",
                                    (code, discordID))
                    dbCon.commit()
                else:
                    print(f"failed to insert {e}")
                pass
            dbCon.close()
            await message.author.send(f"Please enter '!register {code}' into conan in-game chat without the quotes. Recommend entering in /local or /clan")

        if message.content == '!coin':
            discordID = message.author.name + '#' + message.author.discriminator
            discordObjID = message.author.id
            print(discordID)
            print(discordObjID)
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


            # Get MariaCursor
            dbCur = dbCon.cursor()

            # get wallet balance
            dbCur.execute("SELECT walletBalance FROM accounts WHERE discordid = ?",(discordID, ))
            coin = dbCur.fetchone()

            if coin == None:
                msg = "Couldn't find an account associated with your discord ID. Please !register first."
                print("Couldn't find discord ID in accounts... not registered?")
            else:
                coin = coin[0] 
                msg = (f"You have {coin} {config.Shop_CurrencyName}")
            dbCon.close()
            await message.channel.send(msg)

    client.run(config.Discord_API_KEY)
