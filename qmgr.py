import collections
import functools
from typing import List

class QueueManager(object):
	actualQueue = {}

	def __init__(self, hideSingers):
		self.skip: List[str] = list()
		self.singerRotation = []
		self.song2singer = {}
		self.hideSingers = hideSingers
	
	def getSinger(self, s):
		return "N/A" if 'singer' not in s else s['singer']
	
	def getQueue(self):
		return self.actualQueue
	
	def getParsedSinger(self, s):
		return self.getSinger(s)

	def unique_id(self, e):
		singer = e["singer"]
		artist = e["artist"]
		title = e["title"]
		return f"{singer}{artist}{title}"
	
	def skip_this_one(self, elem):
		self.skip.append(self.unique_id(elem))
	
	def reconcile(self, queue: List):
		self.actualQueue = queue
		if not queue:
			self.singerRotation = []
			self.song2singer = {}
			return

		# Clean up old entries in self.song2singer.
		unseen = set(self.song2singer.keys()) - {s['id'] for s in queue}
		for qid in unseen:
			del self.song2singer[qid]

		# also clean old next entries
		for key in self.skip:
			if not any(key == self.unique_id(e) for e in queue) or self.unique_id(queue[0]) in self.skip:
				b = key.replace(" ", "-")
				print(f"Cleaning prioritized key {b}")
				self.skip = list(filter(lambda x: x != key, self.skip))

		singerQueues = collections.defaultdict(list)
		for s in queue[1:]:
			singer = self.getParsedSinger(s)
			if (self.unique_id(s) in self.skip):
				continue
			if singer not in self.singerRotation:
				self.singerRotation.append(singer)
			
			singerQueues[singer].append([s])

		if self.singerRotation and self.getParsedSinger(queue[0])[0] == self.singerRotation[0]:
			self.singerRotation = self.singerRotation[1:] + self.singerRotation[:1]

		# If you don't have anything queued, you lose your place in the scheduler.
		self.singerRotation = list(filter(lambda singer: singer in singerQueues, self.singerRotation))

		if self.hideSingers:
			# Deduplicate songs, keeping the first.
			seen = set()
			for s in queue[1:]:
				if s['id'] > 0 and s['id'] in seen:
					return ('queueRemove', s['queueId'])
				seen.add(s['id'])

		def calc_remaining(singer_list):
			values = singer_list.values()
			return functools.reduce(lambda a,b: a + len(b), values, 0)
		
		idx = 1 + len(self.skip)

		while calc_remaining(singerQueues) > 0:
			for singer in [''] if singerQueues[''] else self.singerRotation:
				if not singerQueues[singer]:
					continue
				for s in singerQueues[singer].pop(0):
					if s['id'] != idx:
						return ('queueMove', {'queueId': s['queueId'], 'from': s['id'], 'to': idx})
					idx += 1

		if self.hideSingers:
			for s in queue[1:]:
				if s['id'] > 0 and s['singer'] != '':
					return ('queueAdd', {'id': int(s['id']), 'pos': s['id'], 'singer': ''})

		return None
