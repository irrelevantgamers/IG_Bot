import valve.rcon
import time
import sys
import config
# add Modules folder to system path
sys.path.insert(0, '..\\Modules')
# read in the config variables from importconfig.py


def easyRcon(command):
    attempts = 0
    success = 0
    rcon_host = config.Server_RCON_Host
    rcon_port = config.Server_RCON_Port
    rcon_pass = config.Server_RCON_Pass

    while success == 0 and attempts <= 5:
        try:
            with valve.rcon.RCON((rcon_host, int(rcon_port)), rcon_pass) as rcon:
                response = rcon.execute(command)
                rcon.close()
                response_text = response.body.decode('utf-8', 'ignore')
                print(response_text)
                return response_text
        except Exception as e:
            success = 0
            attempts = attempts + 1
            print(e)
            time.sleep(1)
