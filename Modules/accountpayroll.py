# Module Imports
import mariadb
import sys
import config

def updateWalletsforExiledPlayers():
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
    

    dbCur.close()
    dbCon.close()
