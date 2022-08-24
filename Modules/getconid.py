import valve.rcon
import time
def getconid(rcon_host,rcon_port,rcon_pass,platformid):

    attempts = 0
    success=0
    while success == 0 and attempts <= 5:
        try:
            with valve.rcon.RCON((rcon_host, int(rcon_port)), rcon_pass) as rcon:
                response = rcon.execute("listplayers")
                rcon.close()
                response_text = response.body.decode('utf-8', 'ignore')
                print(response_text)
            playerlist = response_text.split('\n')
            for player in playerlist:
                if platformid in player:
                    conid = player.split(' | ')[0].strip()
                    return conid
        except Exception:
            success = 0
            attempts = attempts + 1
            time.sleep(1)
   