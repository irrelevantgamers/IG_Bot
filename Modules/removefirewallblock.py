import sys
# read in the config variables from importconfig.py
import config
import ipaddress
import easyrcon

# add Modules folder to system path
sys.path.insert(0, '..\\Modules')


def removeIPfromBlocklist(ip):
    # read in block list
    found = 0
    with open(config.Firewall_Blocklist_file, 'r') as f:
        blocklist = f.readlines()
    # remove ip from block list
    for block in blocklist:
        cleanblock = block.strip('\n')
        if ipaddress.ip_address(ip) in ipaddress.ip_network(cleanblock):
            blocklist.remove(block)
            found = 1
    # write block list back to file
    with open(config.Firewall_Blocklist_file, 'w') as f:
        f.writelines(blocklist)
    if found == 1:
        return "IP removed from block list"
    else:
        return "IP not found in block list"


def unbanPlayer(steamid):
    # unban player
    print("Unbanning player " + steamid)
    rconreturn = easyrcon.easyRcon(f'unbanplayer {steamid}')
    return rconreturn
