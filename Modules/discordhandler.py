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
    from datetime import datetime, timedelta

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
            dbCur.execute("SELECT * FROM registration_codes WHERE curstatus = 1")
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
    
    async def updateShopList():
        while True:
            print("Updating Shop")
            channel = client.get_channel(int(config.Discord_Items_for_Sale_Channel))
            await channel.purge()
            
            
            try:
                shopCon = mariadb.connect(
                user=config.DB_user,
                password=config.DB_pass,
                host=config.DB_host,
                port=config.DB_port,
                database=config.DB_name

            )
            except mariadb.Error as e:
                print(f"Error connecting to MariaDB Platform: {e}")
                sys.exit(1)
            try:
                shopCur = shopCon.cursor()
                shopCur.execute("SELECT DISTINCT(category) FROM shop_items WHERE enabled = True AND category != 'NULL' ORDER BY category ASC")
                categories = shopCur.fetchall()
                for category in categories:
                    cat = category[0]
                    embedvar = discord.Embed(title=cat)
                    embedvar.set_footer(text="To buy an item go to purchasing and use !buy followed by the item ID. (Optional you can include how many times you want to buy with x# \nExample to buy 1: !buy 1\nExample to buy 1 twice: !buy 1x2 ")
                    shopCur.execute(f"SELECT id, itemname, price, itemcount, itemdescription, category, maxCountPerPurchase FROM shop_items WHERE enabled = True AND category = '{cat}' ORDER BY id ASC")
                    shop_items = shopCur.fetchall()


                    for row in shop_items:
                        itemid = row[0]
                        itemname = row[1]
                        price = row[2]
                        itemcount = row[3]
                        description = row[4]
                        category = row[5]
                        maxCountPerPurchase = row[6]
                        
                        embedvar.add_field(name="ID: {} \tName: {} x {}".format(itemid, itemcount, itemname), value="Price: {}\nMax per purchase: {}\nDescription: {}".format(price, maxCountPerPurchase, config.Shop_CurrencyName, description),inline=False)
                    await channel.send(embed=embedvar)

            except Exception as e:
                    print(f"Update Shop Error: {e}")
                    pass
            shopCur.close()
            shopCon.close()
        
            await asyncio.sleep(600) #updates every 10 minutes
    async def placeOrder(senderID,userIN,channelID):
        sourcechannel = client.get_channel(channelID)
        loadDate = datetime.now()
        try:
            try:
                shopCon = mariadb.connect(
                user=config.DB_user,
                password=config.DB_pass,
                host=config.DB_host,
                port=config.DB_port,
                database=config.DB_name

            )
            except mariadb.Error as e:
                print(f"Error connecting to MariaDB Platform: {e}")
                sys.exit(1)
            shopCur = shopCon.cursor()
            #Get the price of the item
            userINsplit = userIN.split("x")
            if len(userINsplit) == 2:
                itemNo = userINsplit[0]
                itemQty = userINsplit[1]
            else:
                itemNo = userINsplit[0]
                itemQty = 1
            shopCur.execute(f"SELECT itemname, price, itemid, itemcount, itemType, kitID, cooldown, maxCountPerPurchase, buffId FROM shop_items WHERE id =? AND enabled =1", (itemNo, ))
            itemDetails = shopCur.fetchone()
            if itemDetails == None:
                print("Item not found")
                msg = "Item not found"
            elif int(itemDetails[7]) < int(itemQty):
                msg = "You can only purchase {} of this item at a time".format(itemDetails[7])
            else:
                itemname = itemDetails[0]
                itemcount = int(itemDetails[3]) * int(itemQty)
                itemid = int(itemDetails[2])
                itemprice = int(itemDetails[1]) * int(itemQty)
                itemType = itemDetails[4]
                itemKitID = itemDetails[5]
                cooldown = int(itemDetails[6]) * int(itemQty)
                buffId = itemDetails[8]
                #Assign an order number
                shopCur.execute("SELECT ID FROM shop_log ORDER BY ID DESC")
                orderNums = shopCur.fetchone()
                if orderNums != None:
                    order_number = int(orderNums[0]) + 1
                else:
                    order_number = 1
                order_date = datetime.now()
                last_attempt = datetime.min
                #get the wallet value of the user
                shopCur.execute(f"SELECT walletBalance,conanplatformid, steamplatformid FROM accounts WHERE discordid =?", (senderID, ))
                senderDetails = shopCur.fetchone()
                if senderDetails == None:
                    msg = (f"Couldn't find any {config.Shop_CurrencyName} for {senderID}. Try !register first.")
                else:
                    senderCurrency = senderDetails[0]
                    platformid = senderDetails[1]
                    steamid = senderDetails[2]
                    if int(senderCurrency) >= int(itemprice):
                        print(f"{senderID} Has enough {config.Shop_CurrencyName} to purchase {itemname} for {itemprice}")
                        #check if cooldown for this item is up for the user
                        shopCur.execute("SELECT logtimestamp FROM shop_log WHERE item =? AND player=? ORDER BY ID Desc", (itemname, senderID))
                        lastPurchase = shopCur.fetchone()
                        if lastPurchase != None:
                            timestamp = lastPurchase[0]
                            now = datetime.now()
                            coolDownExpires = timestamp + timedelta(minutes=cooldown)
                            if now > coolDownExpires:
                                print("Cool down is up. Purchase allowed")
                                coolDownOK = True
                            else:
                                coolDownOK = False
                                print(f"Cannot purchase again yet, Cooldown expires {coolDownExpires}")
                                timediff = coolDownExpires - timestamp
                                status = f"Cannot purchase again yet, Cooldown expires in {timediff}"
                                msg = status
                        else: 
                            coolDownOK = True

                        if coolDownOK:
                            order_placed = False
                            if itemType == 'single':
                                print("item type is single, placing order")
                                shopCur.execute("INSERT INTO order_processing (order_number, order_value, itemid, itemType, itemcount, purchaser_platformid, purchaser_steamid, in_process, completed, refunded, order_date, last_attempt) values (?,?,?,?,?,?,?,?,?,?,?,?)",(order_number, itemprice, itemid, itemType, itemcount, platformid, steamid, False, False, False, order_date, last_attempt))
                                shopCon.commit()
                                order_placed = True
                            elif itemType == 'kit':
                                print("item type is kit, processing order")
                                #get items in the kit
                                shopCur.execute("SELECT itemID, itemcount, kitname FROM shop_kits WHERE kitID =?",(itemKitID, ))
                                items = shopCur.fetchall()
                                if items == None:
                                    print("No items associated with kit, order canceled")
                                    msg = "No items associated with kit, order canceled"
                                else:
                                    order_placed = True
                                    for item in items: 
                                        itemid = item[0]
                                        itemcount = int(item[1]) * int(itemQty)
                                        shopCur.execute("INSERT INTO order_processing (order_number, order_value, itemid, itemType, itemcount, purchaser_platformid, purchaser_steamid, in_process, completed, refunded, order_date, last_attempt) values (?,?,?,?,?,?,?,?,?,?,?,?)",(order_number, itemprice, itemid, itemType, itemcount, platformid, steamid, False, False, False, order_date, last_attempt))
                                        shopCon.commit()
                            elif itemType == 'serverBuff':
                                    
                                shopCur.execute("SELECT ID, serverName FROM server_buffs WHERE id =?",(buffId, ))
                                buffs = shopCur.fetchone()
                                if buffs == None:
                                    msg = "Buff not found, order canceled"
                                else:
                                    insertquery = """INSERT INTO order_processing 
                                    (
                                        order_number, 
                                        order_value, 
                                        itemid, 
                                        itemType, 
                                        serverName, 
                                        itemcount, 
                                        purchaser_platformid, 
                                        purchaser_steamid, 
                                        in_process, 
                                        completed, 
                                        refunded, 
                                        order_date, 
                                        last_attempt
                                        ) values (?,?,?,?,?,?,?,?,?,?,?,?,?)"""
                                    shopCur.execute(insertquery,(
                                        order_number, 
                                        itemprice, 
                                        buffId, 
                                        itemType, 
                                        buffs[1], 
                                        itemcount, 
                                        platformid, 
                                        steamid, 
                                        False, 
                                        False, 
                                        False, 
                                        order_date, 
                                        last_attempt))
                                    
                                    shopCon.commit()
                                    order_placed = True
                                    print("order placed")
                            elif itemType == 'vault':
                                #get vault list for users last seen server
                                shopCur.execute("SELECT lastServer FROM Accounts WHERE discordid =?",(senderID, ))
                                lastServer = shopCur.fetchone()
                                if lastServer == None:
                                    print("No last server found, order canceled")
                                    msg = "No last server found, order canceled. Please try again once your are online."
                                else:
                                    lastServer = lastServer[0]
                                    now = datetime.now()
                                    shopCur.execute("SELECT ID FROM {server}_vault_rentals WHERE rentedUntil < ?".format(server=lastServer),(now, ))
                                    availableVaults = shopCur.fetchall()
                                    if availableVaults == None or len(availableVaults) == 0:
                                        print("No available vaults found, order canceled")
                                        msg = "No available vaults found, order canceled. Please try again once your are online."
                                    else:
                                        shopCur.execute("INSERT INTO order_processing (order_number, order_value, itemid, itemType, server, count, purchaser_platformid, purchaser_steamid, in_process, completed, refunded, order_date, last_attempt) values (?,?,?,?,?,?,?,?,?,?,?,?,?)",(order_number, itemprice, itemid, itemType, lastServer, itemcount, platformid, steamid, False, False, False, order_date, last_attempt))
                                        shopCon.commit()
                                        order_placed = True
                            else:
                                print("couldn't identify item type. Canceling order")
                                msg = "Couldn't identify item type. Canceling order"


                            if order_placed == True:
                                #log purchase
                                status = "Order Placed"
                                shopCur.execute("INSERT INTO shop_log (item, itemcount, price, player, curstatus, logtimestamp) VALUES (?,?,?,?,?,?)", (itemname, itemcount, itemprice, senderID, status, loadDate))
                                shopCon.commit()
                                #remove currency
                                newBalance = int(senderCurrency) - int(itemprice)
                                shopCur.execute(f"UPDATE accounts SET walletBalance = ? WHERE discordid =?",(int(newBalance), senderID))
                                shopCon.commit()
                                msg = f"Order# {order_number} has been placed. Your new {config.Shop_CurrencyName} balance is {newBalance}. You can refund pending orders with !refund {order_number}"

                    else:
                        msg = "Insufficient Balance"
            message = await sourcechannel.send(msg)
            message_id = message.id
            discordChannelID = sourcechannel.id
            #insert message ID for order_num
            if msg != "Item not found":
                shopCur.execute("UPDATE order_processing SET discordMessageID =?, discordChannelID =? WHERE order_number =?", (message_id, discordChannelID, order_number))
                shopCon.commit()
            shopCur.close()
            shopCon.close()
                
            
        except Exception as e:
                print(f"Error on DB: {e}")
                msg = ("Couldn't connect to DB. Try again later")
                pass
        

    async def refundOrder(userIN,channelID):
        sourceChannel = client.get_channel(channelID)
        order_number = userIN
        print(f"Attempting to refund order {order_number}")
        #find if order is eligible (is the order not in process and not complete, has the order been refunded already, is the requester the original orderer)
        try:
                shopCon = mariadb.connect(
                user=config.DB_user,
                password=config.DB_pass,
                host=config.DB_host,
                port=config.DB_port,
                database=config.DB_name

            )
        except mariadb.Error as e:
            print(f"Error connecting to MariaDB Platform: {e}")
            sys.exit(1)

        shopCur = shopCon.cursor()
        shopCur.execute("SELECT id, order_number, order_value, itemid, in_process, completed, refunded, order_date, last_attempt, completed_date, discordMessageID, discordChannelID, purchaser_platformid FROM order_processing WHERE order_number =?",(userIN, ))
        orderDetails = shopCur.fetchall()
        if orderDetails != None:
            refundedFound = 0
            inProcessFound = 0
            completedFound = 0
            order_value = 0
            order_number = 0
            for item in orderDetails:
                order_value = item[2]    
                inProcess = item[4]
                completed = item[5]
                refunded = item[6]
                order_number = item[1]
                purchaser_platformid = item[12]
                if inProcess == True:
                    inProcessFound = 1
                if completed == True:
                    completedFound = 1
                if refunded == True:
                    refundedFound = 1

            if refundedFound == 1 or inProcessFound == 1 or completedFound == 1:
                msg = "Order is not eligible for refund."
            else:
                #get wallet balance of user and add order value back to wallet
                shopCur.execute("SELECT walletBalance from accounts WHERE conanPlatformId =?",(purchaser_platformid, ))
                balance = shopCur.fetchone()
                if balance != None:
                    balance = balance[0]
                    newBalance = int(balance) + int(order_value)
                    shopCur.execute("UPDATE accounts SET walletBalance =? WHERE conanPlatformId =?",(newBalance, purchaser_platformid))
                    shopCon.commit()
                    #set order status to refunded
                    shopCur.execute("UPDATE order_processing SET refunded =True WHERE order_number =?", (order_number,))
                    shopCon.commit()
                    msg = f"Refund has been processed. New wallet balance is {newBalance}"
                else:
                    msg = f"Account not found for {purchaser_platformid}. Please !register first"
        else:
            msg = "Order not found"
        shopCur.close()
        shopCon.close()
        await sourceChannel.send(msg)

    async def orderStatusWatcher():
        while True:
            try:
                try:
                    shopCon = mariadb.connect(
                    user=config.DB_user,
                    password=config.DB_pass,
                    host=config.DB_host,
                    port=config.DB_port,
                    database=config.DB_name

                        )
                except mariadb.Error as e:
                    print(f"Error connecting to MariaDB Platform: {e}")
                    sys.exit(1)

                shopCur = shopCon.cursor()
                shopCur.execute("SELECT id, order_number, itemid, in_process, completed, refunded, order_date, last_attempt, completed_date, discordMessageID, discordChannelID FROM order_processing WHERE orderCompleteNoticeSent IS False AND discordMessageID IS NOT NULL")
                changedOrders = shopCur.fetchall()
                if changedOrders != None:
                    for order in changedOrders:
                        order_id = order[0]
                        order_number = order[1]
                        itemid = order[2]
                        in_process = order[3]
                        completed = order[4]
                        refunded = order[5]
                        order_date = order[6]
                        last_attempt = order[7]
                        completed_date = order[8]
                        discordMessageID = order[9]
                        discordChannelID = order[10]

                        #check if another item from orderis complete and mark status partially complete
                        completedFound = 0
                        incompleteFound = 0
                        shopCur.execute("SELECT id, completed FROM order_processing WHERE order_number =?",(order_number, ))
                        items = shopCur.fetchall()
                        if items != None:
                            if len(items) >= 2:
                                #this is a kit, check if there are both complete and incomplete items for order
                                for item in items:
                                    if item[1] == True:
                                        completedFound = 1
                                    elif item[1] == False:
                                        incompleteFound = 1

                        #update discord message ID as a test
                        if completedFound == 1 and incompleteFound == 1:
                            status = "Partial Delivery Complete"
                            embedvar = discord.Embed(title='Order Status', color = discord.Color.orange())
                            embedvar.add_field(name="Order #:{} \nStatus: {}".format(order_number, status), value="Order Date: {}".format(order_date, ))
                        
                        elif completed == True and refunded == False:
                            status = "Complete"
                            embedvar = discord.Embed(title='Order Status', color = discord.Color.green())
                            embedvar.add_field(name="Order #:{} \nStatus: {}".format(order_number, status), value="Order Date: {}\nCompleted Date: {}".format(order_date, completed_date))
                            shopCur.execute("UPDATE order_processing SET orderCompleteNoticeSent =True WHERE ID =?",(order_id, ))
                            shopCon.commit()
                        elif refunded == True:
                            status = "Refunded"
                            embedvar = discord.Embed(title='Order Status', color = discord.Color.red())
                            embedvar.add_field(name="Order #:{} \nStatus: {}".format(order_number, status), value="Order Date: {}\nLast delivery attempt date: {}".format(order_date, last_attempt))
                            shopCur.execute("UPDATE order_processing SET orderCompleteNoticeSent =True WHERE ID =?",(order_id, ))
                            shopCon.commit()
                        elif in_process == True:
                            status = "Processing"
                            embedvar = discord.Embed(title='Order Status', color = discord.Color.blue())
                            embedvar.add_field(name="Order #:{} \nStatus: {}".format(order_number, status), value="Order Date: {}\nLast delivery attempt date: {}".format(order_date, last_attempt))
                        else:
                            status = "Placed pending processing."
                            embedvar = discord.Embed(title='Order Status', color = discord.Color.gold())
                            embedvar.add_field(name="Order #:{} \nStatus: {}".format(order_number, status), value="Order Date: {}\nLast delivery attempt date: {}".format(order_date, last_attempt))
                            
                        channel = client.get_channel(int(discordChannelID))
                        message = await channel.fetch_message(int(discordMessageID))
                    
                        
                        
                        
                        await message.edit(embed=embedvar)
            except Exception as e:
                if "object has no attribute 'fetch_message'" in str(e):
                    print(f"Order message went to a channel I dont know, can't update status")
                    shopCur.execute("UPDATE order_processing SET orderCompleteNoticeSent =True WHERE order_number =?",(order_number, ))
                    shopCon.commit()
                else:
                    print(f"error in order status watcher {e}")
                pass
            shopCur.close()
            shopCon.close()
            await asyncio.sleep(1)

    async def refundAll(channelID):
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
        dbCur.execute("SELECT DISTINCT order_number, in_process, completed, refunded FROM order_processing WHERE completed = False AND in_process = False AND refunded = False")
        orders = dbCur.fetchall()
        if orders != None:
            for order in orders:
                userIN = order[0]
                print (userIN)
                print (type(userIN))
                await refundOrder(userIN,channelID)
        dbCon.close()

    async def getUserInfo(author, channelID):
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
        dbCur.execute("SELECT discordID, conanPlayer, conanUserId, isAdmin, walletBalance, lastPaid, earnRateMultiplier, lastUpdated FROM accounts WHERE discordID =?",(author, ))
        user = dbCur.fetchone()
        if user != None:
            discordID = user[0]
            conanPlayer = user[1]
            conanUserId = user[2]
            isAdmin = user[3]
            walletBalance = user[4]
            lastPaid = user[5]
            earnRateMultiplier = user[6]
            lastUpdate = user[7]

            embedvar = discord.Embed(title='User Info', color = discord.Color.blue())
            embedvar.add_field(name="Discord ID:", value=discordID, inline=False)
            embedvar.add_field(name="Conan Player:", value=conanPlayer, inline=False)
            embedvar.add_field(name="Conan User ID:", value=conanUserId, inline=False)
            embedvar.add_field(name="Admin:", value=isAdmin, inline=False)
            embedvar.add_field(name="Wallet Balance:", value=walletBalance, inline=False)
            embedvar.add_field(name="Last Paid:", value=lastPaid, inline=False)
            embedvar.add_field(name="Earn Rate Multiplier:", value=earnRateMultiplier, inline=False)
            embedvar.add_field(name="Last Seen:", value=lastUpdate, inline=False)
            channel = client.get_channel(int(channelID))
            await channel.send(embed=embedvar)

    async def permissionWatcher():
        while True:
            #get privledged roles
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
            dbCur.execute("SELECT roleValue, roleMultiplier, isAdmin FROM privileged_roles order by ID ASC")
            privelegedRoles = dbCur.fetchall()
            if privelegedRoles == None or len(privelegedRoles) == 0:
                msg = ("No privledged roles found")
            else:
                #get members
                members = client.get_all_members()
                if members != None:
                    matchedMembers = []
                    for member in members:
                        discordid = member.name + "#" + member.discriminator
                        if matchedMembers.count(discordid) == 0:
                            dbCur.execute("UPDATE accounts SET earnRateMultiplier =?, isAdmin =? WHERE discordid =?", (1, False, member.name + "#" + member.discriminator))
                            dbCon.commit()
                            if member.roles:
                                matched = 0
                                for role in member.roles:
                                    for privRole in privelegedRoles:
                                        if matched == 0:
                                            if role.name == privRole[0]:
                                                multiplier = privRole[1]
                                                isAdmin = privRole[2]
                                                matched = 1
                                                matchedMembers.append(discordid)
                                                try:
                                                    dbCur.execute("UPDATE accounts SET earnRateMultiplier =?, isAdmin =? WHERE discordid =?", (multiplier, isAdmin, discordid))
                                                    dbCon.commit()
                                                except mariadb.Error as e:
                                                    print(f"Error updating user privlege: {e}")
                                                    sys.exit(1) 

            await asyncio.sleep(60) #check every minute

    async def buffWatcher():
        while True:
            #This function punishes offenders
            
            
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
            dbCur.execute("Select id, servername, serverbuffs_Channel FROM servers WHERE Enabled =True")
            servers = dbCur.fetchall()
            if servers != None:
                for server in servers:
                    serverID = server[0]
                    serverName = server[1]
                    buff_channel = server[2]

                    channel = client.get_channel(int(buff_channel))
                    await channel.purge()

                    embedvar = discord.Embed(title="Server Buffs",color=discord.Color.green())
                    dbCur.execute("SELECT id, buffname, isactive, lastActivated, endTime, lastActivatedBy, deactivateCommand FROM server_buffs WHERE serverName =?",(serverName, ))
                    buffList = dbCur.fetchall()

                    for buff in buffList:
                        buffID = buff[0]
                        buffname = buff[1]
                        active = buff[2]
                        lastActivated = buff[3]
                        endTime = buff[4]
                        lastActivatedBy = buff[5]
                        deactivateCommand = buff[6]
                    
                        #check if buff expired
                        if endTime != None:
                            now = datetime.now()
                            if now > endTime and active == 1:
                                print(f"Deactivating {buffname} on {server}")
                                #old buff found
                                

                                dbCur.execute("SELECT rcon_host, rcon_port, rcon_pass FROM servers WHERE ID =?", (serverID, ))
                                rconInfo = dbCur.fetchone()
                                if rconInfo != None:
                                    rcon_host = rconInfo[0]
                                    rcon_port = rconInfo[1]
                                    rcon_pass = rconInfo[2]
                                #turn off buff
                                rconSuccess = 0
                                while rconSuccess == 0:
                                    try:
                                        with valve.rcon.RCON((rcon_host, int(rcon_port)), rcon_pass) as rcon:
                                            response = rcon.execute(f"con 0 {deactivateCommand}")
                                            rcon.close()
                                        rconSuccess = 1
                                        dbCur.execute("UPDATE server_buffs SET isactive =False WHERE id =?".format(server=serverName),(buffID,))
                                        dbCon.commit()
                                    except valve.rcon.RCONAuthenticationError:
                                        print("Authentication Error")
                                        status = "Could not authenticate RCON"
                                        rconSuccess = 0
                                        pass
                                    except ConnectionResetError:
                                        print("Could not connect to server. Retry later")
                                        rconSuccess = 0
                                        pass  

                        if active == 1:
                            status = "Active"
                        else:
                            status = "Not Active"
                        embedvar.add_field(name="Server: {}\tBuff: {}".format(serverName, buffname), value="Status: **{}**\nLast Activated {} by **{}**\nEndTime: {}".format(status, lastActivated, lastActivatedBy, endTime),inline=False)
                    dbCur.close()          
                    dbCon.close()
                    footer = f"Current server time is: {datetime.now()}."
                    embedvar.set_footer(text=footer)
                    await channel.send(embed=embedvar)

            await asyncio.sleep(60)

    async def updateWantedList():
        while True:
            print("Updating wanted list for discord")
            #This function punishes offenders
            
            
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
            dbCur.execute("Select id, servername, wanted_Channel, map_url FROM servers WHERE Enabled =True")
            servers = dbCur.fetchall()
            if servers != None:
                for server in servers:
                    channel = client.get_channel(int(server[2]))
                    await channel.purge()
                    serverurl = server[3]
                    embedvar = discord.Embed(title='Wanted Players',color = discord.Color.blue(),url="{servermapurl}".format(servermapurl=serverurl))
                    dbCur.execute("SELECT player, killstreak, highestKillStreak, wantedLevel, bounty FROM {server}_wanted_players WHERE wantedLevel > 0".format(server=server[1]))
                    wantedList = dbCur.fetchall()
                    if wantedList != None:
                        for wanted in wantedList:
                            conanplayer = wanted[0]
                            killstreak = wanted[1]
                            highestKillStreak = wanted[2]
                            wantedLevel = wanted[3]
                            bounty = wanted[4]
                            if wantedLevel > 0:
                                status = "Wanted"
                            else:
                                status = "Not Wanted"
                            embedvar.add_field(name="Player:{} \tStatus: {}".format(conanplayer,status), value="Bounty:{}\nCurrent Kill Streak:{}\nHighest Kill Streak:{}".format(bounty, killstreak, highestKillStreak), inline=False)
                    else:
                        embedvar.add_field(name="No currently wanted players", value="check back soon!")
                    footer = "Current Wanted Players can be tracked at {servermapurl}".format(servermapurl=serverurl)
                    embedvar.set_footer(text=footer)
                    await channel.send(embed=embedvar)

                    #kill streaks
                    dbCur.execute("SELECT player, killstreak, highestKillStreak, wantedLevel, bounty FROM {server}_wanted_players ORDER BY highestKillStreak DESC LIMIT 10".format(server=server[1]))
                    result = dbCur.fetchall()
                    embedvar = discord.Embed(title='Kill Streaks',color = discord.Color.gold(),url="{servermapurl}".format(servermapurl=serverurl))
                    for result in result:
                        name = result[0]
                        killstreak = result[1]
                        highestKillStreak = result[2]
                        wantedLevel = result[3]
                        bounty = result[4]
                        if wantedLevel > 0:
                            status = "WANTED"
                        else:
                            status = "Not Wanted"

                        embedvar.add_field(name="Player:{} \tStatus: {}".format(name,status), value="Bounty:{}\nCurrent Kill Streak:{}\nHighest Kill Streak:{}".format(bounty, killstreak, highestKillStreak), inline=False)
                
                    embedvar.set_footer(text=footer)
                    await channel.send(embed=embedvar)
                    dbCur.close()
                    dbCon.close()

            await asyncio.sleep(300)

    async def checkIsAdmin(user):
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
        dbCur.execute("SELECT isAdmin FROM accounts WHERE discordid =?", (user, ))
        isAdmin = dbCur.fetchone()
        if isAdmin != None:
            if isAdmin[0] == True:
                return True
            else:
                return False
        dbCur.close()
        dbCon.close()




    def clean_text(rgx_list, text):
        new_text = text
        for rgx_match in rgx_list:
            new_text = re.sub(rgx_match, '', new_text)
        return new_text        


    @client.event
    async def on_ready():
        print('We have logged in as {0.user}'.format(client))
        await client.change_presence(activity=discord.Game(name="Conan Exiles"))
        client.loop.create_task(player_count_refresh())
        #client.loop.create_task(registrationWatcher())
        client.loop.create_task(kill_log_watcher())
        client.loop.create_task(pending_Message_Watcher())
        client.loop.create_task(orderStatusWatcher())
        client.loop.create_task(permissionWatcher())
        client.loop.create_task(updateShopList())
        client.loop.create_task(buffWatcher())
        client.loop.create_task(updateWantedList())

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
                dbCur.execute("INSERT INTO registration_codes (discordID, discordObjID, registrationCode, curstatus) VALUES (?, ?, ?, FALSE)",
                                (discordID, discordObjID, code))
                dbCon.commit()
            except Exception as e:
                if "Duplicate" in str(e):
                    #print("found duplicate updating registration code")
                    dbCur.execute("UPDATE registration_codes SET registrationcode = ? WHERE discordID = ?",
                                    (code, discordID))
                    dbCon.commit()
                else:
                    print(f"failed to insert {e}")
                pass
            dbCon.close()
            await message.author.send(f"Please enter '!register {code}' into conan in-game chat without the quotes. Recommend entering in /local or /clan")

        if message.content == '!coin' or message.content == '!coins' or message.content == '!currency' or message.content == '!balance':
            discordID = message.author.name + '#' + message.author.discriminator
            discordObjID = message.author.id
            #print(discordID)
            #print(discordObjID)
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
                #print("Couldn't find discord ID in accounts... not registered?")
            else:
                coin = coin[0] 
                msg = (f"You have {coin} {config.Shop_CurrencyName}")
            dbCon.close()
            await message.channel.send(msg)

        if message.content.startswith('!buy'):
            userIN = message.content[5:]
            senderID = message.author.name + "#" + message.author.discriminator
            channelID = message.channel.id
            author = message.author
            #await purchaseItem(senderID,userIN,channelID,author)
            await placeOrder(senderID,userIN,channelID)
        
        if message.content.startswith('!refund'):
            userIN = message.content[8:]
            senderID = message.author.name + "#" + message.author.discriminator
            channelID = message.channel.id
            await refundOrder(userIN,channelID)

        if message.content.startswith('!gift'):
            senderDiscordID = message.author.name + "#" + message.author.discriminator
            pattern = re.compile(r'(?: <\S*[0-9]*>)?', re.IGNORECASE)
            match = pattern.findall(message.content)
            gift = clean_text(match, message.content)
            gift = gift[6:]
            mentioned = message.mentions
            mentionedCount = len(mentioned)
            senderCurrencyNeeded = int(gift) * mentionedCount
            #get senders balance, make sure it's enough, then send gift
            if int(gift) <= 0:
                msg = "Cannot send null value gift."
            else:
                try:
                    try:
                        shopCon = mariadb.connect(
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
                    shopCur = shopCon.cursor()
                    shopCur.execute(f"SELECT walletBalance FROM accounts WHERE discordid =?", (senderDiscordID, ))
                    senderCurrency = shopCur.fetchone()
                    if senderCurrency == None:
                        #YOU AINT GOT A WALLET
                        msg = ("Wallet not found. Try !register first")
                    else:
                        senderCurrency = senderCurrency[0]
                        if int(senderCurrency) >= int(senderCurrencyNeeded):
                            #you have enough
                            for mentions in mentioned:
                                discordid = mentions.name + "#" + mentions.discriminator
                                #print(f"{senderDiscordID} is gifting {gift} to {discordid}")
                                
                                #Get starting balance
                                shopCur.execute(f"SELECT walletBalance FROM accounts WHERE discordid =?", (discordid, ))
                                recipWallet = shopCur.fetchone()
                                if recipWallet == None:
                                    msg = (f"{discordid} is not associated with a wallet. They will need to !register first")
                                else:
                                    #try to update
                                    recipWallet = recipWallet[0]
                                    newBalance = int(recipWallet) + int(gift)
                                    shopCur.execute("UPDATE accounts SET walletBalance = ? WHERE discordid =?", (newBalance, discordid))
                                    shopCon.commit()

                                    #remove currency from sender
                                    senderCurrency = int(senderCurrency) - int(gift)
                                    shopCur.execute("UPDATE accounts SET walletBalance = ? WHERE discordid =?", (senderCurrency, senderDiscordID))
                                    shopCon.commit()
                                    msg = (f"{message.author.name} has sent a gift of {gift} {config.Shop_CurrencyName} to {discordid}")
                                
                        else:
                            #you broke
                            msg = ("Insufficient Balance")
                            
                        
                        shopCur.close()
                        shopCon.close()

                except Exception as e:
                    print(f"Error in Gifting: {e}")
                    msg = ("Error in Gifting, Try again later")
                    pass
                await message.channel.send(msg)
            
        if message.content.startswith('!whoami'):
            #stop order processing
            author = message.author
            channelID = message.channel.id
            await getUserInfo(author, channelID)

        if message.content.startswith('!admin'):
            #stop order processing
            channelID = message.channel.id
            author = message.author
            isAdmin = await checkIsAdmin(author)
            if isAdmin == True:
                await message.channel.send("You are the father")
            else:
                await message.channel.send("You are not an admin")
            
    client.run(config.Discord_API_KEY)
