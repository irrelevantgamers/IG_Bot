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
            )
            COLLATE='utf8mb4_general_ci'
            ENGINE=InnoDB"""
        )
        changes_made = True
    if not check_if_table_exists("order_processing"):
        print("Creating order_processing table...")
        mariaCur.execute(
            """CREATE TABLE `order_processing` (
                    `id` INT(11) NOT NULL AUTO_INCREMENT,
                    `order_number` INT(11) NOT NULL,
                    `order_value` INT(11) NOT NULL,
                    `itemid` INT(11) NOT NULL,
                    `count` INT(11) NOT NULL,
                    `purchaser_platformid` TEXT NULL DEFAULT NULL COLLATE 'utf8mb4_general_ci',
                    `purchaser_steamid` TEXT NULL DEFAULT NULL COLLATE 'utf8mb4_general_ci',
                    `in_process` INT(11) NULL DEFAULT NULL,
                    `completed` INT(11) NULL DEFAULT NULL,
                    `refunded` INT(11) NULL DEFAULT NULL,
                    `order_date` DATETIME NULL DEFAULT current_timestamp(),
                    `last_attempt` DATETIME NULL DEFAULT NULL,
                    `completed_date` DATETIME NULL DEFAULT NULL,
                    `discordChannelID` TEXT NULL DEFAULT NULL COLLATE 'utf8mb4_general_ci',
                    `discordMessageID` TEXT NULL DEFAULT NULL COLLATE 'utf8mb4_general_ci',
                    `orderCompleteNoticeSent` INT(11) NULL DEFAULT NULL,
                    PRIMARY KEY (`id`) USING BTREE
                )
                COLLATE='utf8mb4_general_ci'
                ENGINE=InnoDB"""
            )
        changes_made = True
