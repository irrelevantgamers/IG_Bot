import configparser
global config
global DB_host
global DB_port
global DB_user
global DB_pass
global DB_name
global Server_Name
global Server_RCON_Host
global Server_RCON_Port
global Server_RCON_Pass
global Server_SteamQuery_Port
global Server_Game_DB_Location
global Server_Game_Log_Location
global Discord_ServerLog_Channel
global Discord_Killlog_Channel
global Discord_Solo_LeaderBoardAll_Channel
global Discord_Solo_LeaderBoard30Days_Channel
global Discord_Solo_LeaderBoard7Days_Channel
global Discord_Clan_LeaderBoard30Days_Channel
global Discord_Clan_LeaderBoard7Days_Channel
global Discord_Clan_LeaderBoardAll_Channel
global Discord_BuildingPieceTracking_Channel
global Discord_InventoryPieceTracking_Channel
global Discord_Wanted_Channel
global Discord_Jail_Channel
global Discord_Items_for_Sale_Channel
global Discord_ServerBuffs_Channel
global Discord_VaultRental_Channel
global Discord_API_KEY
global Shop_StartingCash
global Shop_PayCheck
global Shop_PayCheck_Interval
global Shop_CurrencyName
global Time_Timezone
config = configparser.ConfigParser()
config.read("..\\config.ini")
DB_host = config["MariaDB"]["Host"]
DB_port = int(config["MariaDB"]["Port"])
DB_user = config["MariaDB"]["User"]
DB_pass = config["MariaDB"]["Pass"]
DB_name = config["MariaDB"]["DatabaseName"]
Server_Name = config["Server"]["Name"]
Server_RCON_Host = config["Server"]["RCON_Host"]
Server_RCON_Port = int(config["Server"]["RCON_Port"])
Server_RCON_Pass = config["Server"]["RCON_Pass"]
Server_SteamQuery_Port = int(config["Server"]["SteamQuery_Port"])
Server_Game_DB_Location = config["Server"]["Game_DB_Location"]
Server_Game_Log_Location = config["Server"]["Game_Log_Location"]
Discord_ServerLog_Channel = config["Discord"]["ServerLog_Channel"]
Discord_Killlog_Channel = int(config["Discord"]["Killlog_Channel"])
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
Discord_Event_Channel = config["Discord"]["Event_Channel"]
Discord_API_KEY = config["Discord"]["API_KEY"]
Shop_StartingCash = config["Shop"]["StartingCash"]
Shop_PayCheck = config["Shop"]["PayCheck"]
Shop_PayCheck_Interval = config["Shop"]["PayCheckInterval"]
Shop_CurrencyName = config["Shop"]["CurrencyName"]
Time_Timezone = int(config["Time"]["Timezone"])