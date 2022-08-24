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
global Server_Map_Url
global Server_Prison_Exit_Coordinates
global Server_Prison_min_x
global Server_Prison_max_x
global Server_Prison_min_y
global Server_Prison_max_y
global Discord_ServerLog_Channel
global Discord_Killlog_Channel
global Discord_Solo_LeaderBoardAll_Channel
global Discord_Solo_LeaderBoard30Day_Channel
global Discord_Solo_LeaderBoard7Day_Channel
global Discord_Solo_LeaderBoard1Day_Channel
global Discord_Clan_LeaderBoard30Day_Channel
global Discord_Clan_LeaderBoard7Day_Channel
global Discord_Clan_LeaderBoard1Day_Channel
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
global PrivilegedRoles_Admin
global PrivilegedRoles_Mod
global PrivilegedRoles_VIP1
global PrivilegedRoles_VIP2
global PrivilegedRoles_VIP3
global PrivilegedRoles_VIP4


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
Server_Map_Url = config["Server"]["Map_Url"]
Server_Prison_Exit_Coordinates = config["Server"]["Prison_Exit_Coordinates"]
Server_Prison_min_x = int(config["Server"]["Prison_min_x"])
Server_Prison_max_x = int(config["Server"]["Prison_max_x"])
Server_Prison_min_y = int(config["Server"]["Prison_min_y"])
Server_Prison_max_y = int(config["Server"]["Prison_max_y"])
Discord_ServerLog_Channel = config["Discord"]["ServerLog_Channel"]
Discord_Killlog_Channel = int(config["Discord"]["Killlog_Channel"])
Discord_Solo_LeaderBoardAll_Channel = config["Discord"]["Solo_LeaderBoardAll_Channel"]
Discord_Solo_LeaderBoard30Day_Channel = config["Discord"]["Solo_LeaderBoard30Day_Channel"]
Discord_Solo_LeaderBoard7Day_Channel = config["Discord"]["Solo_LeaderBoard7Day_Channel"]
Discord_Solo_LeaderBoard1Day_Channel = config["Discord"]["Solo_LeaderBoard1Day_Channel"]
Discord_Clan_LeaderBoardAll_Channel = config["Discord"]["Clan_LeaderBoardAll_Channel"]
Discord_Clan_LeaderBoard30Day_Channel = config["Discord"]["Clan_LeaderBoard30Day_Channel"]
Discord_Clan_LeaderBoard7Day_Channel = config["Discord"]["Clan_LeaderBoard7Day_Channel"]
Discord_Clan_LeaderBoard1Day_Channel = config["Discord"]["Clan_LeaderBoard1Day_Channel"]
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
PrivilegedRoles_Admin = config["PrivilegedRoles"]["Admin"]
PrivilegedRoles_Moderator = config["PrivilegedRoles"]["Moderator"]
PrivilegedRoles_VIP1 = config["PrivilegedRoles"]["VIP1"]
PrivilegedRoles_VIP2 = config["PrivilegedRoles"]["VIP2"]
PrivilegedRoles_VIP3 = config["PrivilegedRoles"]["VIP3"]
PrivilegedRoles_VIP4 = config["PrivilegedRoles"]["VIP4"]
Time_Timezone = int(config["Time"]["Timezone"])
