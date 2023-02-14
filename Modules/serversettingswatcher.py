import config
import valve.rcon
import time
import mariadb
from datetime import datetime
import sys
import os


def WatchForServerSettings():
    while True:
        # check if we need to exit
        if os.path.exists('..\\restart'):
            os._exit(0)
        # This function watches for server buffs
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
            "SELECT id, buffname, isactive, lastActivated, endTime, lastActivatedBy, deactivateCommand "
            "FROM server_buffs WHERE serverName =?",
            (config.Server_Name,))
        buffList = dbCur.fetchall()

        for buff in buffList:
            buffID = buff[0]
            active = buff[2]
            endTime = buff[4]
            deactivateCommand = buff[6]

            # check if buff expired
            if endTime is not None:
                now = datetime.now()
                if now > endTime and active == 1:
                    # old buff found

                    dbCur.execute("SELECT rcon_host, rcon_port, rcon_pass FROM servers WHERE serverName =?",
                                  (config.Server_Name,))
                    rconInfo = dbCur.fetchone()
                    if rconInfo is not None:
                        rcon_host = rconInfo[0]
                        rcon_port = rconInfo[1]
                        rcon_pass = rconInfo[2]
                    # turn off buff
                    rconSuccess = 0
                    attempts = 0
                    while rconSuccess == 0 or attempts <= 5:
                        try:
                            with valve.rcon.RCON((rcon_host, int(rcon_port)), rcon_pass) as rcon:
                                response = rcon.execute(f"con 0 {deactivateCommand}")
                                print(response)
                                rcon.close()
                            rconSuccess = 1
                            dbCur.execute("UPDATE server_buffs SET isactive =False WHERE id =?", (buffID,))
                            dbCon.commit()
                        except valve.rcon.RCONAuthenticationError:
                            print("Authentication Error")
                            rconSuccess = 0
                            attempts = attempts + 1
                            pass
                        except ConnectionResetError:
                            print("Could not connect to server. Retry later")
                            rconSuccess = 0
                            attempts = attempts + 1
                            pass
        dbCon.close()
        time.sleep(60)
