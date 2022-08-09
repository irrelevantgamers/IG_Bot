# Module Imports
import mariadb
import sys
import config
from datetime import datetime, timedelta

def pay_users():
    # Connect to MariaDB Platform
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
    #get servers enabled
    dbCur.execute("Select ID, serverName FROM servers WHERE Enabled =TRUE")
    servers = dbCur.fetchall()
    if servers != None:
            for server in servers:
                server_name = server[1]
                #get current users and pay them if it's time
                dbCur.execute("SELECT PlatformID FROM {servername}_currentusers".format(servername=server_name))
                currentUsers = dbCur.fetchall()
                if currentUsers != None and currentUsers != '':
                    for user in currentUsers:
                        platformID = user[0]
                        dbCur.execute("select ID, walletbalance, lastPaid, conanPlatformid FROM accounts WHERE conanPlatformid = ?", (platformID,))
                        account = dbCur.fetchone()
                        if account != None:
                            now = datetime.now()
                            lastPaid = account[2]
                            walletbalance = account[1]
                            paycheck = int(config.Shop_PayCheck)
                            paycheckinterval = int(config.Shop_PayCheck_Interval)
                            if lastPaid < (now - timedelta(minutes=paycheckinterval)):
                                dbCur.execute("UPDATE accounts SET walletbalance = ?, lastPaid = ? WHERE ID = ?", (walletbalance + paycheck, now, account[0]))
                                dbCon.commit()
                                print(f"Paid {account[3]} {paycheck}")

    

    dbCur.close()
    dbCon.close()
