
import config
import sqlite3
import mariadb
import asyncio
import sys
import time
def watch_game_db():
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
        file_path_db = config.Server_Game_DB_Location
        gamedbCon = sqlite3.connect(file_path_db)
        gamedbCur = gamedbCon.cursor()
        gamedbCur.execute("select DISTINCT  g.guildid, g.name, (select count() from building_instances where object_id in (select object_id from buildings where owner_id = g.guildId)) as count FROM guilds as g LEFT JOIN buildings as b ON b.owner_id = g.guildId ORDER BY count DESC")
        dbRows = gamedbCur.fetchall()
        if dbRows != None and len(dbRows) > 0:
            dbCur.execute("DELETE FROM {servername}_building_piece_tracking".format(servername=config.Server_Name))
            for row in dbRows:
                dbCur.execute("INSERT INTO {servername}_building_piece_tracking (clan_id, clan_name, building_piece_count) VALUES (?, ?, ?)".format(servername=config.Server_Name), (row[0], row[1], row[2]))
            dbCon.commit()

        gamedbCur.execute("SELECT g.guildid, g.name, count(*) as InventoryCount FROM Detailed_structure_inventory as dsi JOIN buildings as b on dsi.owner_id = b.object_id JOIN guilds as g on b.owner_id = g.guildId GROUP BY g.guildId ORDER BY InventoryCount DESC")
        invdbrows = gamedbCur.fetchall()
        if invdbrows != None and len(invdbrows) > 0:
            dbCur.execute("DELETE FROM {servername}_inventory_tracking".format(servername=config.Server_Name))
            for row in invdbrows:
                dbCur.execute("INSERT INTO {servername}_inventory_tracking (clan_id, clan_name, inventory_count) VALUES (?, ?, ?)".format(servername=config.Server_Name), (row[0], row[1], row[2]))
            dbCon.commit()
        gamedbCon.close()
        dbCon.close()
        time.sleep(60)

    