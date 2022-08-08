import mariadb
import configparser
import sys

# add Modules folder to system path
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


def check_if_table_exists(table_name):
    mariaCur.execute(f"SHOW TABLES LIKE '{table_name}'")
    if mariaCur.fetchone():
        return True
    else:
        return False


if __name__ == '__main__':
    print("Connecting to MariaDB...")
    connect_mariadb()
    # Maria SQL for create tables
    accounts = """
        CREATE TABLE IF NOT EXISTS accounts (
            id					MEDIUMINT NOT NULL AUTO_INCREMENT	COMMENT 'Primary KEY for the accounts Table',
            discordID 			CHAR(100)							COMMENT 'Needed to link the players conanUserId to their discordID to allow them to buy items in discord to be sent to their Conan player',
            conanplayer 		CHAR(100)							COMMENT 'In game player name',
            conanUserId 		CHAR(100) NOT NULL					COMMENT 'In game funcom ID', 
            conanPlatformId 	CHAR(100) NOT NULL UNIQUE			COMMENT 'Funcom Platform ID',
            walletBalance 		INT NOT NULL DEFAULT 0 		        COMMENT 'Current balance of the players account',
            steamPlatformId 	CHAR(100)							COMMENT 'Steam Platform ID',
            earnRateMultiplier 	INT DEFAULT 1 						COMMENT 'Based on the players subscription level, if they do not have one, DEFAULT to 1', 
            lastUpdated 		DATETIME							COMMENT 'Last time this record was updated',
            PRIMARY KEY (id)
        );
    """
    order_processing = """
        CREATE TABLE IF NOT EXISTS order_processing (
            id						MEDIUMINT NOT NULL AUTO_INCREMENT	COMMENT 'Primary KEY for the order_processing Table',
            order_number			INT NOT NULL						COMMENT 'FK: Unique identifier for the the specific order the player makes',
            itemid		 			INT NOT NULL						COMMENT 'FK: Unique identifier for the specific item',
            counts		 			INT NOT NULL						COMMENT 'How many of the item that will be delivered to the player',
            purchaser_platformid 	CHAR(100) NOT NULL UNIQUE			COMMENT 'Funcom Platform ID of the player who made the order',
            purchaser_steamid 		CHAR(100) NOT NULL UNIQUE			COMMENT 'steamID of the player who made the order',
            in_process	 			BOOL NOT NULL						COMMENT 'Boolean to indicate if the order is in process',
            completed	 			BOOL NOT NULL						COMMENT 'Boolean to indicate if the order is completed',
            refunded	 			BOOL NOT NULL						COMMENT 'Boolean value of refunded or not',
            order_date	 			DATETIME DEFAULT CURRENT_TIMESTAMP	COMMENT 'Date and time of when the order was received by the shop bot',
            last_attempt 			DATETIME 							COMMENT 'Last time the shop bot tried to deliver the item to the player',
            completed_date	 		DATETIME							COMMENT 'Date and time of when the order was confirmed complete by the shop bot',
            discordChannelID 		CHAR(100) NOT NULL UNIQUE			COMMENT 'ID of the channel in discord to post the order confirmation to',
            discordMessageID 		CHAR(100) NOT NULL UNIQUE			COMMENT 'ID of the message to update order status in discord',
            orderCompleteNoticeSent	BOOL NOT NULL						COMMENT 'Boolean to indicate if the order complete notice has been sent to the player',
            PRIMARY KEY (id)
        );
    """
    registration_codes = """
        CREATE TABLE IF NOT EXISTS registration_codes(
            ID						MEDIUMINT NOT NULL AUTO_INCREMENT	COMMENT 'Primary KEY for the registration_codes Table',
            discordID 				CHAR(100)							COMMENT 'Needed to link the players conanUserId to their discordID to allow them to buy items in discord to be sent to their Conan player',
            discordObjID 			CHAR(100) 							COMMENT 'Discord Object ID of the Discord account who created the code',
            registrationCode 		CHAR(100) NOT NULL UNIQUE			COMMENT 'A Unique code that is sent to the player to register their discordID with their character',
            status	 				BOOL NOT NULL DEFAULT 0				COMMENT 'Bool to indicate if the code has been used or not. This is used to clean up the table',
            PRIMARY KEY (ID)
        );
    """
    servers = """
        CREATE TABLE IF NOT EXISTS servers(
            ID						                MEDIUMINT NOT NULL AUTO_INCREMENT	COMMENT 'Primary KEY for the servers Table',
            serverName 				                CHAR(100) NOT NULL UNIQUE			COMMENT 'Name of the server',
            enabled 				                BOOL NOT NULL 					    COMMENT 'If the server is active or not',
            dedicated 				                BOOL NOT NULL 					COMMENT 'If the server is dedicated or not',
            rcon_host 				                CHAR(100) NOT NULL 					COMMENT 'RCON IP address',
            rcon_port	 			                INT NOT NULL						COMMENT 'RCON port number',
            rcon_pass 				                CHAR(100) NOT NULL 					COMMENT 'Password for RCON',
            steamQueryPort 			                INT NOT NULL						COMMENT 'Steam Query port number',
            databaseLocation		                CHAR(255) NOT NULL 					COMMENT 'path to the game server database file',
            logLocation				                CHAR(255) NOT NULL 					COMMENT 'path to the game server log file',
            ServerLog_Channel                       CHAR(100) NOT NULL 					COMMENT 'Discord Channel ID to send the server log to',
            Killlog_Channel			                CHAR(100) NOT NULL 					COMMENT 'Discord channel to send the kill log to',
            Killlog_Last_Event_Time                 TIMESTAMP NOT NULL DEFAULT 0 COMMENT 'Last time the kill event was sent to the log',
            Solo_LeaderBoardAll_Channel		        CHAR(100) NOT NULL 					COMMENT 'Discord channel to send the solo leader board all time to',
            Solo_LeaderBoard7Days_Channel			CHAR(100) NOT NULL 					COMMENT 'Discord channel to send the solo leader board 7 days to',
            Solo_LeaderBoard30Days_Channel			CHAR(100) NOT NULL 					COMMENT 'Discord channel to send the solo leader board 30 days to',
            Clan_LeaderBoardAll_Channel			    CHAR(100) NOT NULL 					COMMENT 'Discord channel to send the clan leader board all time to',
            Clan_LeaderBoard7Days_Channel			CHAR(100) NOT NULL 					COMMENT 'Discord channel to send the clan leader board 7 days to',
            Clan_LeaderBoard30Days_Channel			CHAR(100) NOT NULL 					COMMENT 'Discord channel to send the clan leader board 30 days to',
            BuildingPieceTracking_Channel			CHAR(100) NOT NULL 					COMMENT 'Discord channel to send the building piece tracking to',
            InventoryPieceTracking_Channel			CHAR(100) NOT NULL 					COMMENT 'Discord channel to send the inventory piece tracking to',
            Wanted_Channel              			CHAR(100) NOT NULL 					COMMENT 'Discord channel to send the wanted list to',
            Jail_Channel             			    CHAR(100) NOT NULL 					COMMENT 'Discord channel to send the jail list to',
            Items_for_Sale_Channel              	CHAR(100) NOT NULL 					COMMENT 'Discord channel to send the items for sale to',
            ServerBuffs_Channel            			CHAR(100) NOT NULL 					COMMENT 'Discord channel to send the server buffs to',
            VaultRental_Channel           			CHAR(100) NOT NULL 					COMMENT 'Discord channel to send the vault rental to',
            lastCheckIn                             DATETIME DEFAULT CURRENT_TIMESTAMP	COMMENT 'Date and time of when the server last checked in',
            lastUserSync                            DATETIME DEFAULT 0              	COMMENT 'Date and time of when the server last synced users',
            PRIMARY KEY (ID)
        );
    """
    shop_items = """
        CREATE TABLE IF NOT EXISTS shop_items (
            ID						MEDIUMINT NOT NULL AUTO_INCREMENT	COMMENT 'Primary KEY for the shop_items Table',
            itemName 				CHAR(100) NOT NULL UNIQUE			COMMENT 'Name of the item',
            price		 			INT NOT NULL DEFAULT 0				COMMENT 'Price of the item',
            itemId		 			INT NOT NULL        				COMMENT 'In game item ID used for rcon commands',
            count		 			INT NOT NULL DEFAULT 1				COMMENT 'How many of the item',
            enabled		 			INT NOT NULL DEFAULT 0				COMMENT 'Make the item available to the store',
            itemType 				CHAR(100) NOT NULL      			COMMENT 'Type of the item',
            kitId		 			MEDIUMINT NULL						COMMENT 'FK to the shop_kits table',
            PRIMARY KEY (ID)
        );
    """
    shop_kits = """
        CREATE TABLE IF NOT EXISTS shop_kits (
            ID						MEDIUMINT NOT NULL AUTO_INCREMENT	COMMENT 'Primary KEY for the shop_kits Table',
            kitId		 			INT NOT NULL			    		COMMENT 'ID of kit this item belongs to',
            Name 				    CHAR(100) NOT NULL      			COMMENT 'Name of the conan item in the kit',
            itemId		 			INT NOT NULL						COMMENT 'in game item ID used for rcon commands',
            count		 			INT NOT NULL DEFAULT 1				COMMENT 'How many of the item',
            PRIMARY KEY (ID)
        );
    """
    shop_log = """
        CREATE TABLE IF NOT EXISTS shop_log (
            ID						MEDIUMINT NOT NULL AUTO_INCREMENT	COMMENT 'Primary KEY for the shop_log Table also serves as order_number',
            item 					CHAR(100) NOT NULL					COMMENT 'Item which was purchased in the order',
            count		 			CHAR(100) NOT NULL					COMMENT 'How many of the item',
            price		 			CHAR(100) NOT NULL					COMMENT 'Price of the item',
            player		 			CHAR(100) NOT NULL					COMMENT 'Player of the order',
            status		 			CHAR(100) NOT NULL					COMMENT 'Order status',
            logTimestamp 			DATETIME NOT NULL					COMMENT 'Timestamp of when the order was processed',
            PRIMARY KEY (ID)
        );
    """

    server_currentusers = f"""
        CREATE TABLE IF NOT EXISTS {config.Server_Name}_currentusers (
            conid           CHAR(100) NOT NULL UNIQUE COMMENT 'Connection ID of the player',
            player          CHAR(100) COMMENT 'Name of the player',
            userid          CHAR(100) COMMENT 'Funcom ID of the player',
            platformid      CHAR(100) COMMENT 'Funcom Platform ID of the player',
            steamPlatformId CHAR(100) COMMENT 'Steam Platform ID of the player',
            X               CHAR(100) COMMENT 'X position of the player',
            Y               CHAR(100) COMMENT 'Y position of the player',
            loadDate        DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Date and time of when the player was loaded'
            );
            """
    server_historicalusers = f"""
        CREATE TABLE IF NOT EXISTS {config.Server_Name}_historicalusers (
            conid           CHAR(100) NOT NULL COMMENT 'Connection ID of the player',
            player          CHAR(100) COMMENT 'Name of the player',
            userid          CHAR(100) COMMENT 'Funcom ID of the player',
            platformid      CHAR(100) COMMENT 'Funcom Platform ID of the player',
            steamPlatformId CHAR(100) COMMENT 'Steam Platform ID of the player',
            X               CHAR(100) COMMENT 'X position of the player',
            Y               CHAR(100) COMMENT 'Y position of the player',
            loadDate        DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Date and time of when the player was loaded'
            );
            """
    server_jailinfo = f"""
        CREATE TABLE IF NOT EXISTS {config.Server_Name}_jailinfo (
            id              MEDIUMINT NOT NULL AUTO_INCREMENT COMMENT 'Primary KEY for the jailinfo Table',
            name            CHAR(100) NOT NULL COMMENT 'Name of the jail cell',
            spawnLocation   CHAR(100) NOT NULL COMMENT 'Spawn location for the jail cell',
            prisoner        CHAR(100) NOT NULL COMMENT 'Playername of the prisoner',
            assignedPlayerPlatformID CHAR(100) NOT NULL COMMENT 'Funcom Platform ID of the prisoner',
            sentenceTime    datetime NOT NULL COMMENT 'Date and time of when the prisoner was assigned to the jail cell',
            sentenceLength  MEDIUMINT NOT NULL COMMENT 'Length of the sentence in minutes',
            PRIMARY KEY (id)
            );
    """
    server_offenders = f"""
        CREATE TABLE IF NOT EXISTS {config.Server_Name}_offenders (
        player          CHAR(100) NOT NULL COMMENT 'Name of the player',
        platformid      CHAR(100) NOT NULL UNIQUE COMMENT 'Funcom Platform ID of the player',
        current_strikes         MEDIUMINT NOT NULL COMMENT 'Number of strikes the player has',
        last_Strike      DATETIME NOT NULL COMMENT 'Date and time of when the player last got a strike',
        strike_outs    MEDIUMINT NOT NULL COMMENT 'Number of times the player has been punished'
        );
        """

    server_protected_areas = f"""
        CREATE TABLE IF NOT EXISTS {config.Server_Name}_protected_areas (
            id              MEDIUMINT NOT NULL AUTO_INCREMENT COMMENT 'Primary KEY for the protected_areas Table',
            name            CHAR(100) NOT NULL COMMENT 'Name of the protected area',
            minX            CHAR(100) NOT NULL COMMENT 'Minimum X position of the protected area',
            minY            CHAR(100) NOT NULL COMMENT 'Minimum Y position of the protected area',
            maxX            CHAR(100) NOT NULL COMMENT 'Maximum X position of the protected area',
            maxY            CHAR(100) NOT NULL COMMENT 'Maximum Y position of the protected area',
            PRIMARY KEY (id)
            );
    """

    server_recent_pvp = f"""
        CREATE TABLE IF NOT EXISTS {config.Server_Name}_recent_pvp (
            id              MEDIUMINT NOT NULL AUTO_INCREMENT COMMENT 'Primary KEY for the recent_pvp Table',
            name            CHAR(100) NOT NULL COMMENT 'Name of the pvp location',
            x               CHAR(100) NOT NULL COMMENT 'X position of the pvp location',
            y               CHAR(100) NOT NULL COMMENT 'Y position of the pvp location',
            loadDate        DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Date and time of when the pvp location was loaded',
            PRIMARY KEY (id)
            );
    """

    server_bans = f"""
        CREATE TABLE IF NOT EXISTS {config.Server_Name}_bans (
            id              MEDIUMINT NOT NULL AUTO_INCREMENT COMMENT 'Primary KEY for the bans Table',
            player          CHAR(100) NOT NULL COMMENT 'Name of the player',
            platformid      CHAR(100) NOT NULL UNIQUE COMMENT 'Funcom Platform ID of the player',
            steamPlatformId CHAR(100) NOT NULL COMMENT 'Steam Platform ID of the player',
            banTime         DATETIME NOT NULL COMMENT 'Date and time of when the player was banned',
            banEndTime      DATETIME NOT NULL COMMENT 'Date and time of when the player ban will end',
            banReason       CHAR(100) NOT NULL COMMENT 'Reason for the ban',
            banIssued       BOOL NOT NULL COMMENT 'If the player was banned by the server',
            PRIMARY KEY (id)
            );
    """

    server_server_buffs = f"""
        CREATE TABLE IF NOT EXISTS {config.Server_Name}_server_buffs (
            id              MEDIUMINT NOT NULL AUTO_INCREMENT COMMENT 'Primary KEY for the server_buffs Table',
            name            CHAR(100) NOT NULL COMMENT 'Name of the buff',
            active          BOOL NOT NULL COMMENT 'If the buff is active',
            activateCommand CHAR(100) NOT NULL COMMENT 'Command to activate the buff',
            deactivateCommand CHAR(100) NOT NULL COMMENT 'Command to deactivate the buff',
            lastActivated   DATETIME NOT NULL COMMENT 'Date and time of when the buff was last activated',
            endTime         DATETIME NOT NULL COMMENT 'Date and time of when the buff will end',
            lastActivatedBy CHAR(100) NOT NULL COMMENT 'Name of the player who last activated the buff',
            PRIMARY KEY (id)
            );
    """

    server_vault_rentals = f"""
        CREATE TABLE IF NOT EXISTS {config.Server_Name}_vault_rentals (
            id              MEDIUMINT NOT NULL AUTO_INCREMENT COMMENT 'Primary KEY for the vault_rentals Table',
            name            CHAR(100) NOT NULL COMMENT 'Name of the vault',
            renterDiscordID CHAR(100) NOT NULL COMMENT 'Discord ID of the player who rented the vault',
            renterPlatformID CHAR(100) NOT NULL COMMENT 'Funcom Platform ID of the player who rented the vault',
            renterClanName  CHAR(100) NOT NULL COMMENT 'Clan name of the player who rented the vault',
            renterClanID    CHAR(100) NOT NULL COMMENT 'Funcom Clan ID of the player who rented the vault',
            rentTime        DATETIME NOT NULL COMMENT 'Date and time of when the vault was rented',
            rentedUntil     DATETIME NOT NULL COMMENT 'Date and time of when the vault will be rented until',
            lastAccessed    DATETIME NOT NULL COMMENT 'Date and time of when the vault was last accessed',
            inUse           BOOL NOT NULL COMMENT 'If the vault is in use',
            location        CHAR(100) NOT NULL COMMENT 'Location of the vault',
            PRIMARY KEY (id)
            );
    """

    server_wanted_players = f"""
        CREATE TABLE IF NOT EXISTS {config.Server_Name}_wanted_players (
            id              MEDIUMINT NOT NULL AUTO_INCREMENT COMMENT 'Primary KEY for the wanted_players Table',
            player          CHAR(100) NOT NULL COMMENT 'Name of the player',
            platformid      CHAR(100) NOT NULL UNIQUE COMMENT 'Funcom Platform ID of the player',
            killstreak      MEDIUMINT NOT NULL COMMENT 'Killstreak of the player',
            highestKillStreak MEDIUMINT NOT NULL COMMENT 'Highest killstreak of the player',
            wantedLevel     MEDIUMINT NOT NULL COMMENT 'Wanted level of the player',
            bounty          MEDIUMINT NOT NULL COMMENT 'Bounty of the player',
            X              CHAR(100) NOT NULL COMMENT 'X position of the player',
            Y              CHAR(100) NOT NULL COMMENT 'Y position of the player',
            lastSeen       DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Date and time of when the player was last seen',
            PRIMARY KEY (id)
            );
    """

    server_kill_log = f"""
        CREATE TABLE IF NOT EXISTS {config.Server_Name}_kill_log (
            id              MEDIUMINT NOT NULL AUTO_INCREMENT COMMENT 'Primary KEY for the kill_log Table',
            player          CHAR(100) NOT NULL COMMENT 'Name of the player',
            player_id       CHAR(100) NOT NULL COMMENT 'conan player ID of the player',
            player_level    MEDIUMINT NOT NULL COMMENT 'Level of the player',
            player_clan     CHAR(100) NOT NULL COMMENT 'Clan of the player',
            victim          CHAR(100) NOT NULL COMMENT 'Name of the victim',
            victim_id       CHAR(100) NOT NULL COMMENT 'conan player ID of the victim',
            victim_level    MEDIUMINT NOT NULL COMMENT 'Level of the victim',
            victim_clan     CHAR(100) NOT NULL COMMENT 'Clan of the victim',
            kill_location_x CHAR(100) NOT NULL COMMENT 'X position of the kill',
            kill_location_y CHAR(100) NOT NULL COMMENT 'Y position of the kill',
            kill_type       CHAR(100) NOT NULL COMMENT 'Type of the kill (Normal, Arena, Event)',
            protected_area  CHAR(100) COMMENT 'Protected area of the kill',
            wanted_kill     BOOL NOT NULL COMMENT 'If the killer was wanted',
            wanted_paid_amount MEDIUMINT NOT NULL COMMENT 'Amount of the bounty paid for the kill',
            bounty_kill      BOOL NOT NULL COMMENT 'If the kill was a bounty kill',
            bounty_paid_amount   MEDIUMINT NOT NULL COMMENT 'Amount of the bounty',
            Killlog_Last_Event_Time DATETIME NOT NULL COMMENT 'Date and time of when the last event occurred',
            discord_notified BOOL NOT NULL DEFAULT '0' COMMENT 'If the kill log has been notified to the discord channel',
            loadDate        DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Date and time of when the kill was logged',
            PRIMARY KEY (id)
            );
    """

    server_ArenaParticipants = f"""
        CREATE TABLE IF NOT EXISTS {config.Server_Name}_ArenaParticipants (
            player          CHAR(100) NOT NULL UNIQUE COMMENT 'Name of the player',
            conanUserId     CHAR(100) NOT NULL COMMENT 'conan user ID of the player',
            platformid      CHAR(100) NOT NULL UNIQUE COMMENT 'Funcom Platform ID of the player',
            steamPlatformId CHAR(100) NOT NULL COMMENT 'Steam Platform ID of the player',
            arenaName       CHAR(100) NOT NULL COMMENT 'Name of the arena',
            loadDate        DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Date and time of when the player was loaded'
            );
    """

    server_ArenaParticipants_stats = f"""
        CREATE TABLE IF NOT EXISTS {config.Server_Name}_ArenaParticipants_stats (
            player          CHAR(100) NOT NULL UNIQUE COMMENT 'Name of the player',
            points          MEDIUMINT NOT NULL COMMENT 'Points of the player',
            kills           MEDIUMINT NOT NULL COMMENT 'Kills of the player',
            deaths          MEDIUMINT NOT NULL COMMENT 'Deaths of the player',
            platformid      CHAR(100) NOT NULL UNIQUE COMMENT 'Funcom Platform ID of the player'
            );
    """

    server_ArenaPrize_pool = f"""
        CREATE TABLE IF NOT EXISTS {config.Server_Name}_ArenaPrize_pool (
            place           MEDIUMINT NOT NULL COMMENT 'Place required to win prize',
            PrizeName       CHAR(100) NOT NULL COMMENT 'Name of the prize',
            PrizeCount      MEDIUMINT NOT NULL COMMENT 'Number of the prize to give at once',
            PrizeItemID     MEDIUMINT NOT NULL COMMENT 'Item ID of the prize'
            );
    """

    server_ArenaPrizes = f"""
        CREATE TABLE IF NOT EXISTS {config.Server_Name}_ArenaPrizes (
            Place           MEDIUMINT NOT NULL COMMENT 'Place of the player',
            PrizeName       CHAR(100) NOT NULL COMMENT 'Name of the prize',
            PrizeCount      MEDIUMINT NOT NULL COMMENT 'Number of the prize to give at once',
            PrizeItemID     MEDIUMINT NOT NULL COMMENT 'Item ID of the prize'
            );
    """

    server_Arenas = f"""
        CREATE TABLE IF NOT EXISTS {config.Server_Name}_Arenas (
            id              MEDIUMINT NOT NULL AUTO_INCREMENT COMMENT 'Primary KEY for the arenas Table',
            Name            CHAR(100) NOT NULL COMMENT 'Name of the arena',
            Active          BOOL NOT NULL COMMENT 'If the arena is active',
            MinX            MEDIUMINT NOT NULL COMMENT 'Minimum X position of the arena',
            MinY            MEDIUMINT NOT NULL COMMENT 'Minimum Y position of the arena',
            MaxX            MEDIUMINT NOT NULL COMMENT 'Maximum X position of the arena',
            MaxY            MEDIUMINT NOT NULL COMMENT 'Maximum Y position of the arena',
            SpawnPoint1     CHAR(100) NOT NULL COMMENT 'Spawn point 1 of the arena',
            SpawnPoint2     CHAR(100) NOT NULL COMMENT 'Spawn point 2 of the arena',
            SpawnPoint3     CHAR(100) NOT NULL COMMENT 'Spawn point 3 of the arena',
            SpawnPoint4     CHAR(100) NOT NULL COMMENT 'Spawn point 4 of the arena',
            SpawnPoint5     CHAR(100) NOT NULL COMMENT 'Spawn point 5 of the arena',
            SpawnPoint6     CHAR(100) NOT NULL COMMENT 'Spawn point 6 of the arena',
            StartingPoints  MEDIUMINT NOT NULL COMMENT 'Starting points for each player of the arena',
            HomeAllowed     BOOL NOT NULL COMMENT 'If the arena allows returning to the home base',
            MaxScore        MEDIUMINT NOT NULL COMMENT 'Maximum score of the arena',
            Primary Key (id)
            );
    """
    server_homelocations = f"""
        CREATE TABLE IF NOT EXISTS {config.Server_Name}_homelocations (
            Player          CHAR(100) NOT NULL UNIQUE COMMENT 'Name of the player',
            HomeLocation    CHAR(100) NOT NULL COMMENT 'Home location of the player',
            platformid      CHAR(100) NOT NULL UNIQUE COMMENT 'Funcom Platform ID of the player',
            loadDate        DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Date and time of when the player was loaded'
            );
    """

    server_activeTeleports = f"""
        CREATE TABLE IF NOT EXISTS {config.Server_Name}_activeTeleports (
            conid           CHAR(100) NOT NULL COMMENT 'conan ID of the player',
            player          CHAR(100) NOT NULL UNIQUE COMMENT 'Name of the player',
            srcLocation     CHAR(100) NOT NULL COMMENT 'Source location of the player',
            dstLocation     CHAR(100) NOT NULL COMMENT 'Destination location of the player',
            platformid      CHAR(100) NOT NULL UNIQUE COMMENT 'Funcom Platform ID of the player',
            loadDate        DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Date and time of when the player was loaded'
            );
    """

    server_event_details = f"""
        CREATE TABLE IF NOT EXISTS {config.Server_Name}_event_details (
            ID              MEDIUMINT NOT NULL AUTO_INCREMENT COMMENT 'Primary KEY for the event_details Table',
            Name            CHAR(100) NOT NULL UNIQUE COMMENT 'Name of the event',
            GeneralLocation CHAR(100) NOT NULL COMMENT 'General location of the event',
            BlueTeamLocation CHAR(100) NOT NULL COMMENT 'Blue team location of the event',
            RedTeamLocation CHAR(100) NOT NULL COMMENT 'Red team location of the event',
            SpectateLocation CHAR(100) NOT NULL COMMENT 'Spectate location of the event',
            Active          BOOL NOT NULL COMMENT 'If the event is active',
            MinX            MEDIUMINT NOT NULL COMMENT 'Minimum X position of the event',
            MinY            MEDIUMINT NOT NULL COMMENT 'Minimum Y position of the event',
            MaxX            MEDIUMINT NOT NULL COMMENT 'Maximum X position of the event',
            MaxY            MEDIUMINT NOT NULL COMMENT 'Maximum Y position of the event',
            HomeAllowed     BOOL NOT NULL COMMENT 'If the event allows returning to the home base',
            PRIMARY KEY (ID)
            );
    """

    server_insults = f"""
        CREATE TABLE IF NOT EXISTS {config.Server_Name}_insults (
            ID              MEDIUMINT NOT NULL AUTO_INCREMENT COMMENT 'Primary KEY for the insults Table',
            Insult          CHAR(100) NOT NULL UNIQUE COMMENT 'Insult',
            PRIMARY KEY (ID)
            );
    """

    server_teleportLog = f"""
        CREATE TABLE IF NOT EXISTS {config.Server_Name}_teleportLog (
            conid           CHAR(100) NOT NULL COMMENT 'conan ID of the player',
            player          CHAR(100) NOT NULL COMMENT 'Name of the player',
            srcLocation     CHAR(100) NOT NULL COMMENT 'Source location of the player',
            dstLocation     CHAR(100) NOT NULL COMMENT 'Destination location of the player',
            platformid      CHAR(100) NOT NULL UNIQUE COMMENT 'Funcom Platform ID of the player',
            loadDate        DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Date and time of when the player was loaded'
            );
    """

    # Add tables to the table list
    tableList = [accounts, order_processing, registration_codes, servers, shop_items, shop_log, shop_kits, shop_log,
                 server_currentusers, server_historicalusers, server_jailinfo, server_offenders, server_protected_areas,
                 server_recent_pvp, server_bans, server_server_buffs, server_vault_rentals, server_wanted_players,
                 server_kill_log, server_ArenaParticipants, server_ArenaParticipants_stats, server_ArenaPrize_pool,
                 server_ArenaPrizes, server_Arenas, server_homelocations, server_activeTeleports, server_event_details,
                 server_insults, server_teleportLog]

    # Attempt to execute the create table queries
    print("Creating tables if they don't exist...")
    for i in tableList:
        try:
            mariaCur.execute(i)
        except mariadb.Error as e:
            print(f"Error: {e}")
    mariaCon.commit()

    # Attempt to create server info if it doesn't exist
    print("Creating server info if it doesn't exist...")
    try:
        mariaCur.execute("SELECT * FROM servers WHERE id = ?", (config.Server_Name,))
        server_info = mariaCur.fetchone()
        if server_info is None or len(server_info) == 0:
            server_info = """
                INSERT INTO servers (
                    serverName, 				          
                    enabled, 				          
                    dedicated,			          
                    rcon_host, 				          
                    rcon_port,	 			          
                    rcon_pass, 				          
                    steamQueryPort, 			          
                    databaseLocation,		          
                    logLocation,
                    ServerLog_Channel,				          
                    Killlog_Channel,           
                    Solo_LeaderBoardAll_Channel,		  
                    Solo_LeaderBoard7Days_Channel,	
                    Solo_LeaderBoard30Days_Channel,	
                    Clan_LeaderBoardAll_Channel,		
                    Clan_LeaderBoard7Days_Channel,	
                    Clan_LeaderBoard30Days_Channel,	
                    BuildingPieceTracking_Channel,	
                    InventoryPieceTracking_Channel,	
                    Wanted_Channel,              	
                    Jail_Channel,             		
                    Items_for_Sale_Channel,            
                    ServerBuffs_Channel,            	
                    VaultRental_Channel
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""



            mariaCur.execute(server_info,(
                config.Server_Name,
                True,
                True,
                config.Server_RCON_Host,
                config.Server_RCON_Port,
                config.Server_RCON_Pass,
                config.Server_SteamQuery_Port,
                config.Server_Game_DB_Location,
                config.Server_Game_Log_Location,
                config.Discord_ServerLog_Channel,
                config.Discord_Killlog_Channel,
                config.Discord_Solo_LeaderBoardAll_Channel,
                config.Discord_Solo_LeaderBoard7Days_Channel,
                config.Discord_Solo_LeaderBoard30Days_Channel,
                config.Discord_Clan_LeaderBoardAll_Channel,
                config.Discord_Clan_LeaderBoard7Days_Channel,
                config.Discord_Clan_LeaderBoard30Days_Channel,
                config.Discord_BuildingPieceTracking_Channel,
                config.Discord_InventoryPieceTracking_Channel,
                config.Discord_Wanted_Channel,
                config.Discord_Jail_Channel,
                config.Discord_Items_for_Sale_Channel,
                config.Discord_ServerBuffs_Channel,
                config.Discord_VaultRental_Channel))
            mariaCon.commit()
    except mariadb.Error as e:
        if "Duplicate entry" in str(e):
            pass
        else:
            print(f"Error: {e}")





    close_mariaDB()
