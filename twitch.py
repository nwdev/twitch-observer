class Game:
	def __init__(self, name, viewers, channels):
		self.name     = name
		self.viewers  = viewers
		self.channels = channels


	def __str__(self):
		return "%s, viewers: %d, channels: %d" %\
		(self.name, self.viewers, self.channels)



class Stream:
	def __init__(self, stream_name, game_name, viewers):
		self.name      = stream_name
		self.game_name = game_name
		self.viewers   = viewers


	def __str__(self):
		return "%s, game: %s, viewers: %d" %\
		(self.name, self.game_name, self.viewers)


import requests
import json
import logging


class Twitch:


	def __init__(self, client_id):
		if client_id is None:
			logging.error("Client-ID must be provided! Exiting")
			exit()
		self.client_id = client_id
		self.base_url  = 'https://api.twitch.tv/kraken'
		self.version   = 'application/vnd.twitchtv.v3+json'
		self.header    = {
			'Accept'   : self.version,
			'Client-ID': self.client_id
		}


	def http_get(self, url):
		res = requests.get(url, headers=self.header)
		if res.status_code >= 400:
			logging.error("%s returned bad status code(%d)! Exiting..." %\
			(url, res.status_code))
			exit()
		return res


	def get_top_games(self, **options):
		
		# default values
		limit  = 10
		offset = 0

		if options.get('limit') is not None and options['limit'] <= 100:
			limit = options['limit']
		if options.get('offset') is not None and options['offset'] >= 0:
			offset = options['offset']
		
		suffix_url = '/games/top?limit=' + str(limit) +'&offset=' + str(offset)
		res        = self.http_get(self.base_url + suffix_url)
		games_json = json.loads(res.text).get('top')
		games      = []
		for game in games_json:
			g_name = game.get('game').get('name')
			g_view = game.get('viewers')
			g_chan = game.get('channels')
			games.append(Game(g_name, g_view, g_chan))
		return games


	def streams(self, **options):

		# default values
		game        = None
		limit       = 25
		offset      = 0
		stream_type = 'live'

		if options.get('game') is not None:
			game = options['game']
		if options.get('limit') is not None and options['limit'] <= 100:
			limit = options['limit']
		if options.get('offset') is not None and options['offset'] >= 0:
			offset = options['offset']
		if options.get('stream_type') is not None:
			stream_type = options['stream_type']

		suffix_url = '/streams?' +\
			'limit=' + str(limit) +\
			'&offset=' + str(offset) +\
			'&stream_type=' + stream_type
		if game is not None:
			suffix_url = suffix_url + '&game=' + game
		res = self.http_get(self.base_url + suffix_url)
		streams_json = json.loads(res.text).get('streams')
		streams = []
		for stream in streams_json:
			s_name  = stream.get('channel').get('name')
			s_gname = stream.get('game')
			s_view  = stream.get('viewers')
			streams.append(Stream(s_name, s_gname, s_view))
		return streams