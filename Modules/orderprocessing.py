def processOrderLoop():
    import time
    from datetime import datetime, timedelta
    from usersync import runSync
    import sys
    import mariadb
    import valve.rcon
    import config

    print("Starting Order Processor")
    while True:
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
        now = datetime.now()
        eligibleProcessTime = now - timedelta(minutes=5)
        
        #Get incomplete orders by newest
        shopCur.execute("SELECT order_number, itemid, count, purchaser_platformid, purchaser_steamid, order_date FROM order_processing WHERE completed = False AND in_process = False AND refunded = False AND last_attempt <= ? ORDER BY order_date ASC", (eligibleProcessTime,))
        NewestOrder = shopCur.fetchone()
        try:
            if NewestOrder != None:
                #process order
                #mark order as in process for this order number
                orderNumber = NewestOrder[0]
                shopCur.execute("UPDATE order_processing SET in_process =True WHERE order_number =?",(orderNumber, ))
                shopCon.commit()

                #Get all items associated with order number
                shopCur.execute("SELECT id, order_number, itemid, count, purchaser_platformid, purchaser_steamid, order_date FROM order_processing WHERE order_number =?",(orderNumber, ))
                orderedItems = shopCur.fetchall()
                if orderedItems != None:
                    userIsOffline = 0
                    for item in orderedItems:
                        
                        order_id = item[0]
                        order_number = item[1]
                        itemid = item[2]
                        itemcount = item[3]
                        platformid =item[4]
                        print(f"Processing {order_number}: Current order_processing_id {order_id}: Item ID {itemid}")
                        if userIsOffline == 0:
                            #sync users
                            print ("syncing users")
                            runSync(True)
                            userFound = 0
                            rconSuccess = 0
                            user_server = ''
                            user_conid = None
                            #look for user on servers
                            print("looking for user on servers")
                            
                            shopCur.execute("SELECT ID, serverName FROM servers WHERE enabled =True")
                            enabledServers = shopCur.fetchall()
                    
                            if enabledServers != None:
                                for enabledServer in enabledServers:
                                    serverid = enabledServer[0]
                                    serverName = enabledServer[1]
                                    print(f"Looking at {serverName}")
                                    shopCur.execute(f"SELECT conid FROM {serverName}_currentUsers WHERE platformid = ? LIMIT 1",(platformid,))
                                    conid = shopCur.fetchone()
                                
                                    if conid != None:
                                        userFound = 1
                                        
                                        user_conid = conid[0]
                                        print(f"User found, conid {user_conid}")
                                        user_server = serverName
                                        shopCur.execute("SELECT rcon_host, rcon_port, rcon_pass FROM servers WHERE ID =?", (serverid, ))
                                        rconInfo = shopCur.fetchone()
                                        if rconInfo != None:
                                            rcon_host = rconInfo[0]
                                            rcon_port = rconInfo[1]
                                            rcon_pass = rconInfo[2]

                            if (userFound == 1) and (user_conid != None):
                                #try delivery
                                print("Trying delivery")
                                attempts = 0
                                while rconSuccess == 0 and attempts <= 5:
                                    try:
                                        with valve.rcon.RCON((rcon_host, int(rcon_port)), rcon_pass) as rcon:
                                            response = rcon.execute(f"con {user_conid} spawnitem {itemid} {itemcount}")
                                            rcon.close()
                                        print(response.text)
                                        rconSuccess = 1
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
                                        pass
                            else:
                                userIsOffline = 1
                                print(f"User {platformid} is offline")

                        else:
                            #user is offline retry later
                            rconSuccess = 0

                        if rconSuccess == 1:
                            #update order processing to show this is complete
                            print("Marking order complete")
                            completeTime = datetime.now()
                            shopCur.execute("UPDATE order_processing SET completed =True, in_process =False, completed_date =?, last_attempt =? WHERE id=?",(completeTime, completeTime, order_id))
                            shopCon.commit()
                        elif rconSuccess == 0:
                            #set in_process back to 0
                            #update last attempted date for order
                            print("Updating last attempt time")
                            attemptTime = datetime.now()
                            shopCur.execute("UPDATE order_processing SET last_attempt =?, in_process =False WHERE id=?",(attemptTime, order_id))
                            shopCon.commit()
                    #set user is offline back to 0
                    userIsOffline = 0

        except Exception as e:
            print(f"exception: {e}")
            shopCur.execute("UPDATE order_processing SET last_attempt =?, in_process = False WHERE order_number=? AND completed = False AND refunded = False",(attemptTime, order_number))
            shopCon.commit()
            pass
        shopCur.close()
        shopCon.close()
        time.sleep(2) #sleep for 5 seconds between orders