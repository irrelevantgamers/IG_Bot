import mariadb
import configparser
import sys

config = configparser.ConfigParser()
config.read("..\\config.ini")
DB_host = config["MariaDB"]["Host"]
DB_port = int(config["MariaDB"]["Port"])
DB_user = config["MariaDB"]["User"]
DB_pass = config["MariaDB"]["Pass"]
DB_name = config["MariaDB"]["DatabaseName"]
Server_ID = config["Server"]["ID"]
Server_RCON_Host = config["Server"]["RCON_Host"]
Server_RCON_Port = config["Server"]["RCON_Port"]
Server_RCON_Pass = config["Server"]["RCON_Pass"]
Discord_Killlog_Channel = config["Discord"]["Killlog_Channel"]
Discord_Solo_LeaderBoardAll_Channel = config["Discord"]["Solo_LeaderBoardAll_Channel"]
Discord_Solo_LeaderBoard30Days_Channel = config["Discord"]["Solo_LeaderBoard30Days_Channel"]
Discord_Solo_LeaderBoard7Days_Channel = config["Discord"]["Solo_LeaderBoard7Days_Channel"]
Discord_Clan_LeaderBoardAll_Channel = config["Discord"]["Clan_LeaderBoardAll_Channel"]
Discord_Clan_LeaderBoard30Days_Channel = config["Discord"]["Clan_LeaderBoard30Days_Channel"]
Discord_Clan_LeaderBoard7Days_Channel = config["Discord"]["Clan_LeaderBoard7Days_Channel"]
Discord_BuildingPieceTracking_Channel = config["Discord"]["BuildingPieceTracking_Channel"]
Discord_InventoryPieceTracking_Channel = config["Discord"]["InventoryPieceTracking_Channel"]
Discord_Wanted_Channel = config["Discord"]["Wanted_Channel"]
Discord_Jail_Channel = config["Discord"]["Jail_Channel"]
Discord_Items_for_Sale_Channel = config["Discord"]["Items_for_Sale_Channel"]
Discord_ServerBuffs_Channel = config["Discord"]["ServerBuffs_Channel"]
Discord_VaultRental_Channel = config["Discord"]["VaultRental_Channel"]
Discord_API_KEY = config["Discord"]["API_KEY"]
Shop_StartingCash = config["Shop"]["StartingCash"]
Shop_PayCheck = config["Shop"]["PayCheck"]
Shop_PayCheckInterval = config["Shop"]["PayCheckInterval"]
Shop_CurrencyName = config["Shop"]["CurrencyName"]

def connect_mariadb():
    try:
        global mariaCon
        mariaCon = mariadb.connect(
            user=DB_user,
            password=DB_pass,
            host=DB_host,
            port=DB_port,
            database=DB_name

        )
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)
    global mariaCur
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
    changes_made = False
    if not check_if_table_exists("accounts"):
        print("Creating accounts1 table...")
        mariaCur.execute(
            """CREATE TABLE accounts IF NOT EXISTS(
                	`ID` INT(11) NOT NULL AUTO_INCREMENT,
                    `discordID` TEXT NULL DEFAULT NULL COLLATE 'utf8mb4_general_ci',
                    `conanplayer` TEXT NULL DEFAULT NULL COLLATE 'utf8mb4_general_ci',
                    `conanUserId` TEXT NULL DEFAULT NULL COLLATE 'utf8mb4_general_ci',
                    `conanPlatformId` TEXT NULL DEFAULT NULL COLLATE 'utf8mb4_general_ci',
                    `walletBalance` INT(11) NOT NULL DEFAULT '0',
                    `steamPlatformId` TEXT NOT NULL COLLATE 'utf8mb4_general_ci',
                    `earnRateMultiplier` INT(11) NOT NULL DEFAULT '1',
                    `lastUpdated` DATETIME NOT NULL,
                    PRIMARY KEY (`ID`) USING BTREE,
                    UNIQUE INDEX `conanPlatformId` (`conanPlatformId`) USING HASH,
                    UNIQUE INDEX `steamPlatformId` (`steamPlatformId`) USING HASH
            )"""
        )
        changes_made = True
    if not check_if_table_exists("order_processing"):

    # Maria SQL for create tables
    accounts = """
        CREATE TABLE accounts IF NOT EXISTS (
            id					MEDIUMINT NOT NULL AUTO_INCREMENT	COMMENT 'Primary KEY for the accounts Table',
            discordID 			CHAR(100)							COMMENT 'Needed to link the players conanUserId to their discordID to allow them to buy items in discord to be sent to their Conan player',
            conanplayer 		CHAR(100)							COMMENT 'Not sure exactly what this is',
            conanUserId 		CHAR(100) NOT NULL					COMMENT 'Not sure exactly what this is', 
            conanPlatformId 	CHAR(100) NOT NULL UNIQUE			COMMENT 'Not sure exactly what this is',
            walletBalance 		MEDIUMINT NOT NULL DEFAULT 0 		COMMENT 'Current balance of the players account',
            steamPlatformId 	CHAR(100)							COMMENT 'Not sure exactly what this is',
            earnRateMultiplier 	INT DEFAULT 1 						COMMENT 'Based on the players subscription level, if they do not have one, DEFAULT to 1', 
            lastUpdated 		DATETIME							COMMENT 'Last time this record was updated',
            PRIMARY KEY (id)
        );
    """
    order_processing = """
        CREATE TABLE order_processing IF NOT EXISTS (
            id						MEDIUMINT NOT NULL AUTO_INCREMENT	COMMENT 'Primary KEY for the order_processing Table',
            order_number			INT NOT NULL						COMMENT 'FK: Unique identifier for the the specific order the player makes',
            itemid		 			INT NOT NULL						COMMENT 'FK: Unique identifier for the specific item',
            counts		 			INT NOT NULL						COMMENT 'How many of the item that will be delivered to the player',
            purchaser_platformid 	CHAR(100) NOT NULL UNIQUE			COMMENT 'Not sure exactly what this is',
            purchaser_steamid 		CHAR(100) NOT NULL UNIQUE			COMMENT 'Not sure exactly what this is',
            in_process	 			INT NOT NULL						COMMENT 'Should this be a boolean (true/false)?',
            completed	 			INT NOT NULL						COMMENT 'Should this be a boolean (true/false)?',
            refunded	 			INT NOT NULL						COMMENT 'Should this be a boolean (true/false)?',
            order_date	 			DATETIME DEFAULT CURRENT_TIMESTAMP	COMMENT 'Date and time of when the order was received by the shop bot',
            last_attempt 			DATETIME 							COMMENT 'Last time the shop bot tried to deliver the item to the player',
            completed_date	 		DATETIME							COMMENT 'Date and time of when the order was confirmed complete by the shop bot',
            discordChannelID 		CHAR(100) NOT NULL UNIQUE			COMMENT 'Not sure exactly what this is',
            discordMessageID 		CHAR(100) NOT NULL UNIQUE			COMMENT 'Not sure exactly what this is',
            orderCompleteNoticeSent	INT NOT NULL						COMMENT 'Should this be a boolean (true/false)?',
            PRIMARY KEY (id)
        );
    """
    registration_codes = """
        CREATE TABLE registration_codes IF NOT EXISTS (
            ID						MEDIUMINT NOT NULL AUTO_INCREMENT	COMMENT 'Primary KEY for the registration_codes Table',
            discordID 				CHAR(100)							COMMENT 'Needed to link the players conanUserId to their discordID to allow them to buy items in discord to be sent to their Conan player',
            discordObjID 			CHAR(100) 							COMMENT 'Not sure exactly what this is',
            registrationCode 		CHAR(100) NOT NULL UNIQUE			COMMENT 'A Unique code that is sent to the player to register their discordID with their character',
            status	 				INT NOT NULL DEFAULT 0				COMMENT 'Linked to status table?',
            PRIMARY KEY (ID)
        );
    """
    servers = """
        CREATE TABLE servers IF NOT EXISTS (
            ID						MEDIUMINT NOT NULL AUTO_INCREMENT	COMMENT 'Primary KEY for the servers Table',
            serverName 				CHAR(100) NOT NULL UNIQUE			COMMENT 'Name of the server',
            enabled 				CHAR(100) NOT NULL 					COMMENT 'If the server is active or not',
            dedicated 				CHAR(100) NOT NULL 					COMMENT 'If the server is dedicated or not',
            rcon_host 				CHAR(100) NOT NULL 					COMMENT 'RCON IP address',
            rcon_port	 			INT NOT NULL						COMMENT 'RCON port number',
            rcon_pass 				CHAR(100) NOT NULL 					COMMENT 'Password for RCON',
            steamQueryPort 			INT NOT NULL						COMMENT 'Steam Query port number',
            databaseLocation		CHAR(100) NOT NULL 					COMMENT 'Not sure exactly what this is',
            logLocation				CHAR(100) NOT NULL 					COMMENT 'Not sure exactly what this is',
            killLogChannel			CHAR(100) NOT NULL 					COMMENT 'Not sure exactly what this is',
            PRIMARY KEY (ID)
        );
    """
    shop_items = """
        CREATE TABLE shop_items IF NOT EXISTS (
            ID						MEDIUMINT NOT NULL AUTO_INCREMENT	COMMENT 'Primary KEY for the shop_items Table',
            itemName 				CHAR(100) NOT NULL UNIQUE			COMMENT 'Name of the item',
            price		 			INT NOT NULL DEFAULT 0				COMMENT 'Price of the item',
            itemId		 			INT NOT NULL UNIQUE					COMMENT 'Unique item ID for the discord list **Why cant use ID**',
            counts		 			INT NOT NULL DEFAULT 1				COMMENT 'How many of the item',
            enabled		 			INT NOT NULL DEFAULT 0				COMMENT 'Make the item available to the store',
            itemType 				CHAR(100) NOT NULL UNIQUE			COMMENT 'Type of the item',
            kitId		 			MEDIUMINT NULL						COMMENT 'Not sure exactly what this is',
            PRIMARY KEY (ID)
        );
    """
    shop_kits = """
        CREATE TABLE shop_kits IF NOT EXISTS (
            ID						MEDIUMINT NOT NULL AUTO_INCREMENT	COMMENT 'Primary KEY for the shop_kits Table',
            kitId		 			INT NOT NULL UNIQUE					COMMENT 'Unique item ID for the discord list **Why cant use ID**',
            kitName 				CHAR(100) NOT NULL UNIQUE			COMMENT 'Name of the item',
            itemId		 			INT NOT NULL						COMMENT 'Unique item ID for the discord list **Why cant use ID**',
            counts		 			INT NOT NULL DEFAULT 1				COMMENT 'How many of the item',
            PRIMARY KEY (ID)
        );
    """
    shop_log = """
        CREATE TABLE shop_log IF NOT EXISTS (
            ID						MEDIUMINT NOT NULL AUTO_INCREMENT	COMMENT 'Primary KEY for the shop_log Table',
            order_number 			MEDIUMINT NOT NULL					COMMENT 'Unique item ID for the discord list **Why cant use ID**',
            item 					CHAR(100) NOT NULL					COMMENT 'Item which was purchased in the order',
            counts		 			CHAR(100) NOT NULL					COMMENT 'How many of the item',
            price		 			CHAR(100) NOT NULL					COMMENT 'Price of the item',
            player		 			CHAR(100) NOT NULL					COMMENT 'Player of the order',
            server		 			CHAR(100) NOT NULL					COMMENT 'Server the order was placed from',
            status		 			CHAR(100) NOT NULL					COMMENT 'Server the order was placed from',
            logTimestamp 			DATETIME NOT NULL					COMMENT 'Timestamp of when the order was processed',
            PRIMARY KEY (ID)
        );
    """

    # Add tables to the table list
    tableList = [accounts, order_processing, registration_codes, servers, shop_items, shop_log, shop_kits, shop_log]

    # Attempt to execute the create table queries
    for i in tableList:
        try:
            mariaCur.execute(tableList[i])
        except mariadb.Error as e:
            print(f"Error: {e}")