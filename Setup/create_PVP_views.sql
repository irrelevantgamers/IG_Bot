#
#setup solo leaderboards
#
CREATE VIEW IF NOT EXISTS {server}_SOLO_PVP_LEADER_ALL AS SELECT RANK() OVER (ORDER BY Kills DESC) AS Rank, player, kills, deaths FROM (
(SELECT a.player, COUNT(*) AS kills FROM (select distinct kill_location_x, kill_location_y, player, victim from {server}_kill_log where loadDate <= now()) AS a  GROUP BY a.player) AS pKills
JOIN
(SELECT b.victim, COUNT(*) AS Deaths FROM (SELECT DISTINCT kill_location_x, kill_location_y, player, victim FROM {server}_kill_log WHERE loadDate <= NOW()) AS b GROUP BY b.victim) AS pDeaths
ON player = victim) ORDER BY kills DESC;
CREATE VIEW IF NOT EXISTS {server}_SOLO_PVP_LEADER_30Day AS SELECT RANK() OVER (ORDER BY Kills DESC) AS Rank, player, kills, deaths FROM (
(SELECT a.player, COUNT(*) AS kills FROM (select distinct kill_location_x, kill_location_y, player, victim from {server}_kill_log where killlog_last_event_time >= NOW() - INTERVAL 30 Day) AS a  GROUP BY a.player) AS pKills
JOIN
(SELECT b.victim, COUNT(*) AS Deaths FROM (SELECT DISTINCT kill_location_x, kill_location_y, player, victim FROM {server}_kill_log WHERE killlog_last_event_time >= NOW() - INTERVAL 30 Day) AS b GROUP BY b.victim) AS pDeaths
ON player = victim) ORDER BY kills DESC;
CREATE VIEW IF NOT EXISTS {server}_SOLO_PVP_LEADER_7Day AS SELECT RANK() OVER (ORDER BY Kills DESC) AS Rank, player, kills, deaths FROM (
(SELECT a.player, COUNT(*) AS kills FROM (select distinct kill_location_x, kill_location_y, player, victim from {server}_kill_log where killlog_last_event_time >= NOW() - INTERVAL 7 Day) AS a  GROUP BY a.player) AS pKills
JOIN
(SELECT b.victim, COUNT(*) AS Deaths FROM (SELECT DISTINCT kill_location_x, kill_location_y, player, victim FROM {server}_kill_log WHERE killlog_last_event_time >= NOW() - INTERVAL 7 Day) AS b GROUP BY b.victim) AS pDeaths
ON player = victim) ORDER BY kills DESC;
CREATE VIEW IF NOT EXISTS {server}_SOLO_PVP_LEADER_1Day AS SELECT RANK() OVER (ORDER BY Kills DESC) AS Rank, player, kills, deaths FROM (
(SELECT a.player, COUNT(*) AS kills FROM (select distinct kill_location_x, kill_location_y, player, victim from {server}_kill_log where killlog_last_event_time >= NOW() - INTERVAL 1 Day) AS a  GROUP BY a.player) AS pKills
JOIN
(SELECT b.victim, COUNT(*) AS Deaths FROM (SELECT DISTINCT kill_location_x, kill_location_y, player, victim FROM {server}_kill_log WHERE killlog_last_event_time >= NOW() - INTERVAL 1 Day) AS b GROUP BY b.victim) AS pDeaths
ON player = victim) ORDER BY kills DESC;
#
#Setup Clan LeaderBoards
#
CREATE VIEW IF NOT EXISTS {server}_CLAN_PVP_LEADER_ALL AS SELECT RANK() OVER (ORDER BY Kills DESC) AS Rank, player_clan as Clan, kills, deaths FROM (
(SELECT a.player_clan, COUNT(*) AS kills FROM (select distinct kill_location_x, kill_location_y, player_clan, victim from {server}_kill_log where loadDate <= NOW()) AS a  GROUP BY a.player_clan) AS cKills
JOIN
(SELECT b.victim_clan, COUNT(*) AS Deaths FROM (SELECT DISTINCT kill_location_x, kill_location_y, player, victim_clan FROM {server}_kill_log WHERE loadDate <= NOW()) AS b GROUP BY b.victim_clan) AS cDeaths
ON player_clan = victim_clan) ORDER BY kills DESC;
CREATE VIEW IF NOT EXISTS {server}_CLAN_PVP_LEADER_30Day AS SELECT RANK() OVER (ORDER BY Kills DESC) AS Rank, player_clan as Clan, kills, deaths FROM (
(SELECT a.player_clan, COUNT(*) AS kills FROM (select distinct kill_location_x, kill_location_y, player_clan, victim from {server}_kill_log where killlog_last_event_time >= NOW() - INTERVAL 30 Day) AS a  GROUP BY a.player_clan) AS cKills
JOIN
(SELECT b.victim_clan, COUNT(*) AS Deaths FROM (SELECT DISTINCT kill_location_x, kill_location_y, player, victim_clan FROM {server}_kill_log WHERE killlog_last_event_time >= NOW() - INTERVAL 30 Day) AS b GROUP BY b.victim_clan) AS cDeaths
ON player_clan = victim_clan) ORDER BY kills DESC;
CREATE VIEW IF NOT EXISTS {server}_CLAN_PVP_LEADER_7Day AS SELECT RANK() OVER (ORDER BY Kills DESC) AS Rank, player_clan as Clan, kills, deaths FROM (
(SELECT a.player_clan, COUNT(*) AS kills FROM (select distinct kill_location_x, kill_location_y, player_clan, victim from {server}_kill_log where killlog_last_event_time >= NOW() - INTERVAL 7 Day) AS a  GROUP BY a.player_clan) AS cKills
JOIN
(SELECT b.victim_clan, COUNT(*) AS Deaths FROM (SELECT DISTINCT kill_location_x, kill_location_y, player, victim_clan FROM {server}_kill_log WHERE killlog_last_event_time >= NOW() - INTERVAL 7 Day) AS b GROUP BY b.victim_clan) AS cDeaths
ON player_clan = victim_clan) ORDER BY kills DESC;
CREATE VIEW IF NOT EXISTS {server}_CLAN_PVP_LEADER_1Day AS SELECT RANK() OVER (ORDER BY Kills DESC) AS Rank, player_clan as Clan, kills, deaths FROM (
(SELECT a.player_clan, COUNT(*) AS kills FROM (select distinct kill_location_x, kill_location_y, player_clan, victim from {server}_kill_log where killlog_last_event_time >= NOW() - INTERVAL 1 Day) AS a  GROUP BY a.player_clan) AS cKills
JOIN
(SELECT b.victim_clan, COUNT(*) AS Deaths FROM (SELECT DISTINCT kill_location_x, kill_location_y, player, victim_clan FROM {server}_kill_log WHERE killlog_last_event_time >= NOW() - INTERVAL 1 Day) AS b GROUP BY b.victim_clan) AS cDeaths
ON player_clan = victim_clan) ORDER BY kills DESC;