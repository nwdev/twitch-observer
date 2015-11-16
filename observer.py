#!/usr/bin/python3
from twitch import Twitch
import sqlite3
from datetime import datetime
import statistics
import logging
import sys
import os

def calc_stats(streams):
	viewers = []
	usual_viewers = []
	for stream in streams:
		viewers.append(stream.viewers)
	if len(viewers) == 0:
		logging.warning("Viewer count is zero!")
		return {'mean': 0, 'pstdev': 0, 'expected_viewers': 0}
	mean = statistics.mean(viewers)
	pstdev = statistics.pstdev(viewers)
	logging.info("%d %d" % (mean, pstdev))
	for v in viewers:
		if v <= mean + pstdev and v > mean - pstdev - 1: #azert, ha csak 1 channel van es a pstdev ekkor 0
			usual_viewers.append(v)
	stats = {
		'mean'           : mean,
		'pstdev'         : pstdev,
		'expected_viewers': statistics.mean(usual_viewers)
	}
	return stats

os.makedirs('logs', exist_ok=True)

curtime = datetime.now()
curtime_date = str("%s-%s-%s %s:%s" % (\
	str(curtime.year), str(curtime.month).zfill(2), str(curtime.day).zfill(2),\
	str(curtime.hour).zfill(2), str(curtime.minute).zfill(2)))
curtime_i = str("%s%s%s%s%s" % (\
	str(curtime.year), str(curtime.month).zfill(2), str(curtime.day).zfill(2),\
	str(curtime.hour).zfill(2), str(curtime.minute).zfill(2)))

logging.basicConfig(filename='logs/%s.log' % (curtime), level=logging.INFO)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)
logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)

try:
	client = Twitch(str(sys.argv[1]))
	games = client.get_top_games(limit=20)

	conn = sqlite3.connect('twitch.db')
	c = conn.cursor()
	c.execute('CREATE TABLE IF NOT EXISTS games(\
		name text, viewers integer, channels integer, expected_viewers integer,\
		mean integer, pstdev integer, curtime_date datetime, curtime_i integer,\
		PRIMARY KEY(name, curtime_i))')

	for game in games:
		logging.info(game.name)
		ofs = 0
		total_streams = []
		streams = client.streams(game=game.name, limit=100)
		while len(streams) != 0:
			total_streams.extend(streams)
			ofs += len(streams)
			logging.info(ofs)
			streams = client.streams(game=game.name, limit=100, offset=ofs)
		stats = calc_stats(total_streams)
		c.execute('INSERT INTO games VALUES (?,?,?,?,?,?,?,?)',\
			(game.name, game.viewers, game.channels, int(stats['expected_viewers']),\
				int(stats['mean']), int(stats['pstdev']), curtime_date, curtime_i))
	conn.commit()
	conn.close()
except Exception as e:
	logging.exception(e)
	if conn is not None:
		conn.close()
