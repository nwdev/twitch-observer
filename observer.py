from twitch import Twitch
import sqlite3
from datetime import datetime
import statistics
import logging
import sys
import os

def calculate_expected_viewers_for_channel(streams):
	viewers = []
	usual_viewers = []
	for stream in streams:
		viewers.append(stream.viewers)
	mean = statistics.mean(viewers)
	pstdev = statistics.pstdev(viewers)
	logging.info("%d %d" % (mean, pstdev))
	for v in viewers:
		if v < mean + pstdev and v > mean - pstdev:
			usual_viewers.append(v)
	return statistics.mean(usual_viewers)

os.makedirs('logs', exist_ok=True)

curtime = datetime.now()
curtime = str("%s-%s-%s %s:%s" % (\
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
		name text, viewers integer, channels integer, expectedviewersforchannel integer,\
		curtime datetime, PRIMARY KEY(name, curtime))')

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
		expectedviewersforchannel = calculate_expected_viewers_for_channel(total_streams)
		c.execute('INSERT INTO games VALUES (?,?,?,?,?)',\
			(game.name, game.viewers, game.channels, int(expectedviewersforchannel), curtime))
	conn.commit()
	conn.close()
except Exception as e:
	logging.exception(e)
	if conn is not None:
		conn.close()