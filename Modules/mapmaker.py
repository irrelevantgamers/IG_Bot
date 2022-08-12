import folium
import mariadb
import sqlite3
from sqlite3 import Error
import configparser
import os
import shutil
from datetime import datetime, timedelta
from folium.plugins import HeatMap, Search, FeatureGroupSubGroup
import subprocess
from subprocess import Popen
import config
import sys
import time


def create_conan_maps():
    while True:
        def addAutoRefresh(map_name):
            with open(map_name, encoding="utf-8",errors="ignore") as f:
                content = f.read()
            content = content.replace("<head>", """<head>\n<meta http-equiv="refresh" content="120" >""")
            with open(map_name, "w") as f:
                f.write(content)
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
        dbCur.execute("SELECT ID, serverName FROM servers WHERE enabled =True")
        enabledServers = dbCur.fetchall()

        if enabledServers != None:
            for enabledServer in enabledServers:
                serverName = enabledServer[1]
                os.chdir("..\\WebPages")
                base_map = folium.Map(crs='Simple', min_zoom=1, max_zoom=3, zoom_start=2, tiles=None, location=[0,0], control_scale=True)
                conan_overlay = folium.raster_layers.ImageOverlay(name='map', image='images\\conan.jpg', bounds=[[-370, -342], [445, 475]], zindex=1)
                conan_overlay.add_to(base_map)
                mainFeatureGroup = folium.FeatureGroup(name='Features')
                base_map.fit_bounds(bounds=[[-370, -342], [445, 475]])

                try:
                    wantedPlayers = folium.plugins.FeatureGroupSubGroup(mainFeatureGroup, name='Wanted Players')
                    dbCur.execute("SELECT player, x, y, killstreak, wantedlevel, bounty FROM {servername}_wanted_players".format(servername=serverName))
                    users = dbCur.fetchall()
                    rowcount = len(users)
                    if rowcount != 0:
                        for user in users:
                            player = str(user[0].encode('utf-8', errors='ignore'))[2:-1]
                            playerX = user[1]
                            playerY = user[2]
                            killstreak = user[3]
                            wantedlevel = user[4]
                            bounty = user[5]
                            if wantedlevel > 1:
                                mapX = int(playerX) / 1000
                                mapY = (int(playerY) / 1000) * -1
                                
                                html = '''{player}<br/>Kill Streak:{killstreak}<br/>Wanted Level:{wantedlevel}<br/>Bounty:{bounty}'''.format(player=player, killstreak=killstreak, wantedlevel=wantedlevel, bounty=bounty)
                                popupdata = folium.Popup(html,min_width=100,max_width=500)

                                folium.Marker([mapY, mapX], popup=popupdata,icon=folium.DivIcon(html=f"""<div style="font-family: courier new; -webkit-text-fill-color: #ff00ff; -webkit-text-stroke-width: 2px; -webkit-text-stroke-color: black; font-size: large;"><img src="images\MASCOT_icon.png" width="50" height="50">{player}</center></div>""")).add_to(wantedPlayers) 

                    recentpvp = folium.plugins.FeatureGroupSubGroup(mainFeatureGroup, name='Recent PVP')            
                    dbCur.execute("SELECT id, pvpname, x, y, loadDate FROM {servername}_recent_pvp".format(servername=serverName))
                    pvps = dbCur.fetchall()
                    rowcount = len(pvps)
                    if rowcount != 0:
                        for pvp in pvps:
                            name = str(pvp[1].encode('utf-8', errors='ignore'))[2:-1]
                            x = pvp[2]
                            y = pvp[3]
                            datetime = pvp[4]
                            
                            mapX = int(x) / 1000
                            mapY = (int(y) / 1000) * -1
                            html = '''PVP Detected!<br/>{pvpname}<br/>detection time at:{pvpdatetime}'''.format(pvpname=name, pvpdatetime=datetime)
                            popupdata = folium.Popup(html,min_width=100,max_width=500)
                            folium.Marker([mapY, mapX], popup=popupdata,icon=folium.DivIcon(html=f"""<div style="font-family: courier new; -webkit-text-fill-color: #ff00ff; -webkit-text-stroke-width: 2px; -webkit-text-stroke-color: black; font-size: large;"><img src="images\pvpmarker.gif" width="50" height="50"></center></div>""")).add_to(recentpvp)
                        #base_map.add_child(recentpvp)

                    #OnlinePlayers=folium.plugins.FeatureGroupSubGroup(mainFeatureGroup,name="Online Player Heat Map")
                    #dbCur.execute("SELECT x, y FROM {servername}_currentusers".format(servername=serverName))
                    #data = dbCur.fetchall()
                    #heatmap = []
                    #for dat in data:
                    #    y = (int(dat[1]) / 1000) * -1
                    #    x = int(dat[0]) / 1000
                    #    info = [[int(y), int(x), int(1.0)],]
                    #    
                    #    heatmap.extend(info)
                    #    
                    #HeatMap(heatmap, name='Heat Map', radius=100, min_opacity=0.1, max_zoom=1, gradient={.2: '#482d61', .5:"#5aa7d6", 1: '#fffaad'}).add_to(folium.FeatureGroup(name='Heat Map')).add_to(OnlinePlayers)
                    

                    base_map.add_child(mainFeatureGroup)
                    base_map.add_child(wantedPlayers)
                    base_map.add_child(recentpvp)
                    #base_map.add_child(OnlinePlayers)

                    #protected areas
                    
                    #mariaCur.execute("select name, minx, miny, maxx, maxy FROM exi_protected_areas")
                    #areas = mariaCur.fetchall()
                    #for area in areas:
                    #    name = area[0]
                    #    minx = area[1]
                    #    miny = area[2]
                    #    maxx = area[3]
                    #    maxy = area[4]

                    #    minx = int(minx) / 1000
                    #    miny = int(miny) / 1000
                    #    maxx = (int(maxx) / 1000) * -1
                    #    maxy = (int(maxy) / 1000) * -1
                    #    conan_overlay = folium.raster_layers.ImageOverlay(image='conan.jpg', bounds=[[-370, -342], [445, 475]], zindex=1)
                    
                    #base_map.add_child(folium.LatLngPopup())
                    Search(layer=mainFeatureGroup, placeholder='Search...', collapsed=False,).add_to(base_map)
                    folium.LayerControl().add_to(base_map)
                    
                    map_name = '{servername}_map.html'.format(servername=serverName)
                    base_map.save(map_name)
                    
                    dbCur.close()
                    dbCon.close()
                    addAutoRefresh(map_name)
                except Exception as e:
                    print(f"Map Error: {e}")
        time.sleep(30)
        

   

