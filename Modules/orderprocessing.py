def processOrderLoop():
    import time
    from datetime import datetime, timedelta
    from usersync import runSync
    import sys
    import mariadb
    import valve.rcon
    import config
    from getconid import getconid
    import os
    # setup logging
    import logging
    from logging.handlers import RotatingFileHandler

    # create logger
    logger = logging.getLogger("orderprocessing")
    logger.setLevel(level=logging.DEBUG)

    # set formatter
    logFileFormatter = logging.Formatter(
        fmt=f"%(levelname)s %(created)s (%(relativeCreated)d) \t %(pathname)s F%(funcName)s L%(lineno)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # set the handler
    fileHandler = logging.handlers.RotatingFileHandler(
        filename='..\\logs\\orderprocessing.log',
        maxBytes=4_096_000,
        backupCount=5
    )
    fileHandler.setFormatter(logFileFormatter)
    fileHandler.setLevel(level=logging.INFO)
    logger.addHandler(fileHandler)

    def activateBuff(buffId, server, purchaser):
        logger.info('Activating buff {} for {}'.format(buffId, purchaser))
        success = 0
        while success == 0:
            try:
                mariaCon = mariadb.connect(
                    user=config.DB_user,
                    password=config.DB_pass,
                    host=config.DB_host,
                    port=config.DB_port,
                    database=config.DB_name

                )
                logger.info('Connected to MariaDB')
                mariaCur = mariaCon.cursor()
                discordID = purchaser
                mariaCur.execute(
                    "SELECT id, isactive, activateCommand, deactivateCommand, lastActivated, endTime FROM server_buffs WHERE id = ?",
                    (buffId,))
                buffList = mariaCur.fetchone()
                logger.info('Retrieved buff info')
                Active = buffList[1]
                ActivateCommand = buffList[2]
                DeactivateCommand = buffList[3]
                lastActivated = buffList[4]
                endTime = buffList[5]

                currentTime = datetime.now()

                if endTime is not None:
                    if endTime > currentTime:
                        print(f"Active Buff: endTime: {endTime}")
                        newEndTime = endTime + timedelta(minutes=30)
                        print(f"New End Time: {newEndTime}")
                    else:
                        newEndTime = currentTime + timedelta(minutes=30)
                        print(f"New End Time: {newEndTime}")
                if endTime is None:
                    newEndTime = currentTime + timedelta(minutes=30)
                    print(f"New End Time: {newEndTime}")

                mariaCur.execute(
                    "UPDATE server_buffs SET endTime = ?, lastActivated = ?, isactive =True, lastActivatedBy = ? WHERE id = ?",
                    (newEndTime, currentTime, discordID, buffId))
                mariaCon.commit()
                logger.info('Updated buff info')
                # get server rcon
                logger.info('Getting server rcon')
                mariaCur.execute("SELECT rcon_host, rcon_port, rcon_pass FROM servers WHERE serverName = ?", (server,))
                rcon = mariaCur.fetchone()
                rcon_host = rcon[0]
                rcon_port = rcon[1]
                rcon_pass = rcon[2]

                # activate the buff
                logger.info('Activating buff')
                rconSuccess = 0
                attempts = 0
                while rconSuccess == 0 and attempts < 5:
                    try:
                        with valve.rcon.RCON((rcon_host, int(rcon_port)), rcon_pass) as rcon:
                            response = rcon.execute(f"con 0 {ActivateCommand}")
                            rcon.close()
                        print(response.text)
                        rconSuccess = 1
                        return rconSuccess
                    except valve.rcon.RCONAuthenticationError:
                        print("Authentication Error")
                        status = "Could not authenticate RCON"
                        rconSuccess = 0
                        pass
                        time.sleep(1)
                    except ConnectionResetError:
                        print("Could not connect to server. Retry later")
                        rconSuccess = 0
                        pass
                success = 1
            except Exception as e:
                print(f"couldn't connect to mariaDB.. Try again: {e}")
                logger.info(f"couldn't connect to mariaDB.. Try again: {e}")
                success = 0
                time.sleep(10)
                pass

    print("Starting Order Processor")
    logger.info('Starting Order Processor')
    while True:
        # check if we need to exit
        if os.path.exists('..\\restart'):
            os._exit(0)
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
        logger.info('Connected to MariaDB')
        shopCur = shopCon.cursor()
        now = datetime.now()
        eligibleProcessTime = now - timedelta(minutes=5)

        # Get incomplete orders by newest
        logger.info('Getting incomplete orders')
        shopCur.execute(
            "SELECT order_number, itemid, itemcount, purchaser_platformid, purchaser_steamid, order_date FROM order_processing WHERE completed = False AND in_process = False AND refunded = False AND last_attempt <= ? ORDER BY order_date ASC",
            (eligibleProcessTime,))
        NewestOrder = shopCur.fetchone()
        try:
            if NewestOrder != None:
                # process order

                # mark order as in process for this order number
                orderNumber = NewestOrder[0]
                logger.info('Marking order {} as in process'.format(orderNumber))
                shopCur.execute("UPDATE order_processing SET in_process =True WHERE order_number =?", (orderNumber,))
                shopCon.commit()

                # Get all items associated with order number
                shopCur.execute(
                    "SELECT id, order_number, itemid, itemType, itemcount, purchaser_platformid, purchaser_steamid, order_date, serverName FROM order_processing WHERE order_number =?",
                    (orderNumber,))
                orderedItems = shopCur.fetchall()
                logger.info('Retrieved order items')
                if orderedItems != None:
                    userIsOffline = 0
                    for item in orderedItems:

                        order_id = item[0]
                        order_number = item[1]
                        itemid = item[2]
                        itemType = item[3]
                        itemcount = item[4]
                        platformid = item[5]
                        serverName = item[8]
                        print(f"Processing {order_number}: Current order_processing_id {order_id}: Item ID {itemid}")
                        logger.info(
                            'Processing {}: Current order_processing_id {}: Item ID {}'.format(order_number, order_id,
                                                                                               itemid))
                        if itemType == "serverBuff":
                            print("Item is a server buff")
                            logger.info('Item is a server buff')

                            # get buyer discord id
                            shopCur.execute("SELECT discordid FROM accounts WHERE conanPlatformID =?", (platformid,))
                            info = shopCur.fetchone()
                            purchaser = info[0]
                            rconSuccess = activateBuff(itemid, serverName, purchaser)
                            # mark order as completed

                        elif itemType == "vault":
                            logger.info('Item is a vault item')
                            # get last server
                            shopCur.execute("SELECT lastServer, discordid FROM accounts WHERE conanPlatformID =?",
                                            (platformid,))
                            server = shopCur.fetchone()[0]
                            purchaser = shopCur.fetchone()[1]
                            # get available vault or existing vault
                            shopCur.execute(
                                "SELECT id, rentedUntil FROM {servername}_vault_rentals WHERE rentedUntil < ? AND renterdiscordid = ?".format(
                                    servername=server), (now, purchaser))
                            vault = shopCur.fetchone()
                            if vault != None:
                                # extend time
                                vaultid = vault[0]
                                rentedUntil = vault[1]
                                newRentedUntil = rentedUntil + timedelta(days=7)
                                shopCur.execute(
                                    "UPDATE {servername}_vault_rentals SET rentedUntil = ? WHERE id = ?".format(
                                        servername=server), (newRentedUntil, vaultid))
                                shopCon.commit()
                                logger.info('Extended vault time')
                                # mark order as completed
                                rconSuccess = 1
                        elif itemType == "single" or itemType == "kit" or itemType == "knowledge":
                            if userIsOffline == 0:
                                logger.info('Item is a single or kit')
                                # get server
                                userFound = 0
                                rconSuccess = 0
                                user_server = ''
                                user_conid = None
                                # look for user on servers
                                print("looking for user on servers")
                                logger.info('looking for user on servers')
                                shopCur.execute("SELECT ID, serverName FROM servers WHERE enabled =True")
                                enabledServers = shopCur.fetchall()

                                if enabledServers != None:
                                    for enabledServer in enabledServers:
                                        serverid = enabledServer[0]
                                        serverName = enabledServer[1]
                                        print(f"Looking at {serverName}")
                                        shopCur.execute(
                                            f"SELECT conid FROM {serverName}_currentUsers WHERE platformid = ? LIMIT 1",
                                            (platformid,))
                                        conid = shopCur.fetchone()

                                        if conid != None:
                                            userFound = 1
                                            logger.info('User found on {}'.format(serverName))
                                            user_conid = conid[0]
                                            print(f"User found, conid {user_conid}")
                                            user_server = serverName
                                            shopCur.execute(
                                                "SELECT rcon_host, rcon_port, rcon_pass FROM servers WHERE ID =?",
                                                (serverid,))
                                            rconInfo = shopCur.fetchone()
                                            if rconInfo != None:
                                                rcon_host = rconInfo[0]
                                                rcon_port = rconInfo[1]
                                                rcon_pass = rconInfo[2]

                                if (userFound == 1) and (user_conid != None):
                                    # try delivery
                                    print("Trying delivery")
                                    logger.info('Trying delivery')
                                    # refresh conid
                                    conid = getconid(rcon_host, int(rcon_port), rcon_pass, platformid)
                                    attempts = 0
                                    while rconSuccess == 0 and attempts <= 5:
                                        try:
                                            with valve.rcon.RCON((rcon_host, int(rcon_port)), rcon_pass) as rcon:
                                                if (itemType == "knowledge"):
                                                    response = rcon.execute(f"con {conid} LearnFeat {itemid}")
                                                else:
                                                    response = rcon.execute(f"con {conid} spawnitem {itemid} {itemcount}")
                                                rcon.close()
                                            print(response.text)
                                            rconSuccess = 1
                                            logger.info('Delivery successful')
                                        except valve.rcon.RCONAuthenticationError:
                                            print("Authentication Error")
                                            status = "Could not authenticate RCON"
                                            rconSuccess = 0
                                            attempts = attempts + 1
                                            pass
                                        except ConnectionResetError:
                                            print("Could not connect to server. Retry later")
                                            status = "Could not connect to server, possibly out of karma"
                                            rconSuccess = 0
                                            attempts = attempts + 5
                                            outOfKarma = 1
                                            logger.info('Could not connect to server, possibly out of karma')
                                            pass
                                else:
                                    userIsOffline = 1
                                    print(f"User {platformid} is offline")
                                    logger.info('User is offline')

                        else:
                            # user is offline retry later
                            rconSuccess = 0

                        if rconSuccess == 1:
                            # update order processing to show this is complete
                            print("Marking order complete")
                            completeTime = datetime.now()
                            shopCur.execute(
                                "UPDATE order_processing SET completed =True, in_process =False, completed_date =?, last_attempt =? WHERE id=?",
                                (completeTime, completeTime, order_id))
                            shopCon.commit()
                            logger.info('Order marked complete')
                        elif rconSuccess == 0:
                            # set in_process back to 0
                            # update last attempted date for order
                            print("Updating last attempt time")
                            attemptTime = datetime.now()
                            shopCur.execute("UPDATE order_processing SET last_attempt =?, in_process =False WHERE id=?",
                                            (attemptTime, order_id))
                            shopCon.commit()
                            logger.info('Order last attempt time updated')
                    # set user is offline back to 0
                    userIsOffline = 0
                    # check if order is complete
                    shopCur.execute("SELECT completed FROM order_processing WHERE order_number =?", (order_number,))
                    orderComplete = shopCur.fetchone()[0]
                    if orderComplete == True:
                        # update shop_log
                        shopCur.execute("UPDATE shop_log SET curstatus ='Complete' WHERE id =?", (order_number,))
                        shopCon.commit()
                        logger.info('Order complete')

        except Exception as e:
            print(f"exception: {e}")
            logger.info('Exception: {}'.format(e))
            shopCur.execute(
                "UPDATE order_processing SET last_attempt =?, in_process = False WHERE order_number=? AND completed = False AND refunded = False",
                (attemptTime, order_number))
            shopCon.commit()

            pass
        shopCur.close()
        shopCon.close()
        time.sleep(2)  # sleep for 5 seconds between orders
