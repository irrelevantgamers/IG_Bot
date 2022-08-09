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

    # Get server id from config file and get server info from mariadb
    sys.path.insert(0, '..\\Modules')
    # read in the config variables from importconfig.py
    import config

    intents = discord.Intents.default()
    intents.members = True
    client = discord.Client(intents=intents)

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

    def clean_text(rgx_list, text):
        new_text = text
        for rgx_match in rgx_list:
            new_text = re.sub(rgx_match, '', new_text)
        return new_text

    async def player_count_refresh():

        while True:
            connect_mariadb()
            try:
                # connect to exiled for info
                mariaCur.execute("SELECT conid FROM {servername}_currentusers".format(servername=config.Server_Name))
                prizes = mariaCur.fetchall()
                player_count = len(prizes)
                print("Updating player count for discord status")
                await client.change_presence(
                    activity=discord.Activity(type=discord.ActivityType.watching, name="{} online".format(player_count)))
            except Exception as e:
                print(f"Error updating player count for discord status: {e}")
                pass
            
            close_mariaDB()
            await asyncio.sleep(60)  # task runs every 60 seconds

    async def registrationWatcher():
        while True:
            connect_mariadb()
            # find complete registrations
            mariaCur.execute("SELECT * FROM registration_codes WHERE status = 1")
            completed = mariaCur.fetchall()
            messageSent = 0
            if completed != None:
                for user in completed:
                    if messageSent == 0:
                        discordID = user[0]
                        discordObjID = user[1]
                        print(f"Discord ID is {discordID}")
                        print(f"Discord Object ID is {discordObjID}")

                        members = client.get_all_members()
                        for member in members:
                            if (discordID == str(member)) and (messageSent == 0):
                                print(f"inside {member}")
                                await member.send("Registration Complete")
                                mariaCur.execute("DELETE FROM registrationcodes WHERE discordID = ?", (discordID,))
                                mariaCon.commit()
                                messageSent = 1
            close_mariaDB()
            await asyncio.sleep(5)  # task runs every 5 seconds

    async def kill_log_watcher():
        while True:
            connect_mariadb()
            try:
                
                # find complete registrations
                mariaCur.execute(
                    "SELECT * FROM {servername}_kill_log WHERE discord_notified = 0 ORDER BY Killlog_Last_event_Time ASC LIMIT 1".format(
                        servername=config.Server_Name))
                kills = mariaCur.fetchall()
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
                            channel = client.get_channel(config.Discord_Killlog_Channel)
                            list = list + (
                                f"**PROTECTED AREA KILL DETECTED AT {protected_area} STRIKE HAS BEEN ISSUED**\n")
                        if kill_type == "Normal":
                            channel = client.get_channel(int(config.Discord_Killlog_Channel))
                            list = list + (
                                '⚔️**{}** of clan **{}** killed **{}** of clan **{}**⚔️\n'.format(player, player_clan,
                                                                                                  victim, victim_clan))
                        if kill_type == "Event":
                            channel = client.get_channel(config.Discord_Event_Channel)
                        if kill_type == "Arena":
                            channel = client.get_channel(config.Discord_Event_Channel)

                        if wanted_kill == True:
                            list = list + (
                                '🔥**{}** earned {} {} for killing while wanted🔥\n'.format(player, wanted_paid_amount,
                                                                                            config.Shop_CurrencyName))

                        await channel.send(list)
                        mariaCur.execute("UPDATE {servername}_kill_log SET discord_notified = 1 WHERE id = ?".format(
                            servername=config.Server_Name), (id,))
                        mariaCon.commit()

            except Exception as e:
                print(f"Kill_Log_Watcher_error: {e}")
                sys.exit(1)
            close_mariaDB()
            await asyncio.sleep(1)  # task runs every 1 seconds

    @client.event
    async def on_ready():
        print('We have logged in as {0.user}'.format(client))
        await client.change_presence(activity=discord.Game(name="Conan Exiles"))
        client.loop.create_task(player_count_refresh())
        client.loop.create_task(registrationWatcher())
        client.loop.create_task(kill_log_watcher())

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return

        if message.content.startswith('!intro'):
            await message.channel.send(
                'Hi I\'m Pythios, a Discord bot currently being developed by SubtleLunatic. I can\'t do a lot yet but i\'m still young.')

    client.run(config.Discord_API_KEY)
