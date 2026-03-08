import ll
import os

from datetime import datetime, timedelta


def norm(s):
	return ''.join(c.lower() for c in s if c.lower() in 'abcdefghijklmnopqrstuvwxyz 0123456789')


_global_fetch_cache = dict()


class Fetcher:
	def __init__(
		self,
		base_url='https://tcgcsv.com/tcgplayer/',
		data_dir=None,
		stale_days=1,
	):
		global _global_fetch_cache

		self.data_dir = data_dir if data_dir is not None else ll.here('data')
		self.base_url = base_url
		self.stale_days = stale_days if isinstance(stale_days, timedelta) else ll.days(stale_days)
		self.fetch_cache = _global_fetch_cache


	# Transforms the API path into a local path
	# for a better local directory structure
	def to_local_path(self, api_path):
		local_path = api_path[::]

		# Check if the path is to a filename
		if '.' not in local_path.split('/')[-1]:
			# It isn't
			if '/' in local_path:
				# If there are multiple directories as well
				# as the endpoint, then we'll put the endpoint
				# at the beginning
				endpoint = local_path.split('/')[-1]
				local_path = '/'.join([endpoint] + local_path.split('/')[:-1])

			# Add an extension to the end
			local_path = f'{local_path}.json'
		else:
			# It is
			# TODO: see if this will ever even happen,
			# and, if so, if we can get away with no
			# modification
			local_path = local_path

		# Join with the data dir
		local_path = ll.ospj(self.data_dir, local_path)

		return local_path


	def fetch(self, api_path):
		# Cut off leading and trailing slashes
		api_path = api_path[::]
		if api_path.startswith('/'):
			api_path = api_path[1:]
		if api_path.endswith('/'):
			api_path = api_path[:-1]

		# Compute the local file path
		local_path = self.to_local_path(api_path)
		local_fn, local_dir = ll.bn(local_path), ll.dn(local_path)
		url = self.base_url + api_path

		# First, check to see if this file is in our mem cache
		if local_path in self.fetch_cache:
			# It is
			return self.fetch_cache[local_path]
		else:
			# It isn't; put it there

			# Check to see if we've downloaded this file recently
			if (not ll.fexists(local_path)) or (ll.age(local_path) >= self.stale_days):
				# We haven't; download it
				ll.write((j:=ll.json(url)['results']), local_path)
			else:
				# We have!
				j = ll.json(local_path)

			self.fetch_cache[local_path] = j

		return j


_fetcher = Fetcher()
def fetch(*a, **kw):
	global _fetcher
	return _fetcher.fetch(*a, **kw)


class CardSet:
	def __init__(self, json):
		self.json = json
		for k, v in json.items():
			setattr(self, ll.uncamel(k), v)

		for d in self.extended_data:
			n = ll.uncamel(d['name'])
			if hasattr(self, n):
				setattr(self, 'card_'+ll.uncamel(d['name']), d['value'])
			else:
				setattr(self, ll.uncamel(d['name']), d['value'])

		self.number = str(self.number)
		if f' #{self.number}' in self.name:
			self.name = self.name.replace(f' #{self.number}', '').strip()
		if f' - {self.number}' in self.name:
			self.name = self.name.replace(f' - {self.number}', '').strip()
		if self.number in self.name:
			self.name = self.name.replace(self.number, '').strip()

		if '/' in self.number and '//' not in self.number:
			self.number = self.number.split('/')[0]
		while self.number.startswith('0'):
			self.number = self.number[1:]
		self.number = CardSet.normnum(self.number)

		self.var2prices = {}
		self.variants = []
		for price in fetch(f'{self.category_id}/{self.group_id}/prices'):
			if price['productId'] == self.product_id:
				var = price['subTypeName']
				self.variants = sorted(ll.dedupe(self.variants + [var]))
				price = price['marketPrice'] or price['midPrice'] or price['lowPrice'] or price['highPrice']
				if price is not None:
					self.var2prices[var] = price

		self.var2prices = {norm(k): self.var2prices[k]
			for k in sorted(self.var2prices)} # by variant name


	@staticmethod
	def normnum(s):
		n = ''.join(c.lower() for c in s if c.lower() in 'abcdefghijklmnopqrstuvwxyz */0123456789')
		if '/' in n and '//' not in n:
			n = n.split('/')[0].strip()
		while n.startswith('0'):
			n = n[1:]
		return n


	def prices(self):
		return {k: v for k, v in self.var2prices.items()} # copy


	def image(self):
		ext = self.image_url.split('.')[-1]
		path = ll.here(f'data/images/{self.category_id}/{self.group_id}/{self.product_id}.{ext}')

		os.makedirs(ll.dirname(path), exist_ok=True)

		if not ll.fexists(path):
			resp = ll.http(self.image_url, b=True)
			if len(resp) < 9001:
				return '(no image)'

			ll.write(path, resp)

		return path

	def price(self, var=None):
		if (not var):
			if len(self.var2prices)==1:
				var = list(self.var2prices.keys())[0]
			else:
				vsstr = ll.andify(self.var2prices.keys(), quote="'")
				raise Exception(f"{str(self)} has multiple variants ({vsstr}); pick one, please")

		return self.prices()[norm(var)]


	def min_price(self):
		return min(self.var2prices.values())


	def max_price(self):
		return max(self.var2prices.values())


	def max_price_variant(self):
		return max(self.var2prices.items(), key=ll.nth(1))[0]


	@staticmethod
	def fmt(card, vs, subtype):
		price = card.price(var=subtype)

		name_col = 'khaki3'
		num_col = 'blue'
		mag = 0.75
		vcol = f'rgb({int(100*mag)},{int(100*mag)},{int(175*mag)})'
		if price >= 20:
			pcol = 'rgb(0,200,75)'
		elif price >= 10:
			pcol = 'rgb(0,130,37)'
		elif price >= 5:
			pcol = 'grey50'
		elif price >= 2:
			pcol = 'grey42'
		else:
			pcol = 'grey30'

		s = str(card)
		vsstr = ' '.join(sorted(f'({v})' for v in vs))
		n, nm = (spl:=s.split('#'))[0].strip(), spl[1].strip()

		for v in vs:
			n = n.replace(f' ({v})', '')

		pstr = f'[{pcol}]${price:.02f}[/{pcol}]'

		s = f'{pstr}\t'
		s += f'[{name_col}]{n}[/{name_col}] [{num_col}]#{nm}[/{num_col}]'
		if vsstr:
			s += f' [{vcol}]{vsstr}[/{vcol}]'

		return s


	@staticmethod
	def by_id(game_id, set_id, card_id):
		cards = fetch(f'{game_id}/{set_id}/products')
		for c in cards:
			if str(c['productId']) == str(card_id):
				return CardSet(c)
		raise Exception(f"Product ID {card_id} (category ID {game_id}, group ID {set_id}) not found")


	def __str__(self):
		return f'{self.name} #{self.number}'


class Set:
	def __init__(self, game, json):
		self.game = game
		self.json = json

		for k, v in self.json.items():
			setattr(self, ll.uncamel(k), v)

		self.cards = []
		# TODO: differentiate cards from boxes, etc.?
		for c in fetch(f'{self.game.category_id}/{self.group_id}/products'):
			if 'extendedData' not in c or (not any(e['name']=='Number' for e in c['extendedData'])):
				# It's not a card
				continue
			self.cards.append(CardSet.by_id(self.game.category_id, self.group_id, c['productId']))


	@staticmethod
	def by_name(game, name):
		assert(isinstance(game, Game))

		json = None
		best_score = 0
		fields = ('name', 'abbreviation')
		for g in fetch(f'{game.category_id}/groups'):
			if any(norm(name) == norm(g[f]) for f in fields):
				# Exact name match
				json = g
				break
			else:
				# Score approx. name match based on word overlap
				if (score:=ll.words_in(norm(name), norm(g['name']))) > best_score:
					best_score = score
					json = g
				elif score==best_score and json and len(norm(g['name'])) < len(norm(json['name'])):
					json = g

		if json is None:
			raise Exception(f"No product group found in category ID {game.category_id} for '{name}'")

		return Set(game, json)


	@staticmethod
	def by_id(game, set_id):
		for g in fetch(f'{game.category_id}/groups'):
			if str(g['groupId']) == str(set_id):
				return Set(game, g)
		raise Exception(f"Group ID {set_id} (category ID {game.category_id}) not found")


	@staticmethod
	def by_abbr(game, abbr):
		for g in fetch(f'{game.category_id}/groups'):
			if g['abbreviation'].lower() == abbr.lower():
				return Set(game, g)
		raise Exception(f"Group abbreviation '{abbr}' (category ID {game.category_id}) not found")


	def card(self, num, limit=1):
		cands = []
		for c in self.cards:
			if CardSet.normnum(c.number) == CardSet.normnum(str(num)):
				cands.append(c)
		if len(cands) > 1 and limit==1:
			raise Exception(f"Too many {self.game.name} {self.name} cands with number {num}")
		elif len(cands) == 0:
			return None

		return cands if (len(cands)>1 or limit!=1) else cands[0]


	def __str__(self):
		return f'{self.name} ({self.abbreviation})'


class Game:
	def __init__(self, json, query=None):
		self.json = json
		self.query = query

		for k, v in self.json.items():
			setattr(self, ll.uncamel(k), v)

		self.sets = {}


	@staticmethod
	def by_name(query):
		query = norm(query)

		json = None
		best_score = 0
		fields = ('name', 'displayName')
		for c in fetch('categories'):
			if any(query == norm(c[f]) for f in fields):
				# Exact name match
				json = c
				break
			else:
				# Score approx. name match based on word overlap
				for f in fields:
					if (score:=ll.words_in(query, norm(c[f]))) > best_score:
						best_score = score
						json = c
					elif score==best_score and json and len(norm(c[f])) < len(norm(json[f])):
						json = c

		if json is None:
			raise Exception(f"No category found for query '{query}'")

		return Game(json, query=query)


	@staticmethod
	def by_id(game_id):
		cats = fetch(f'categories')
		for c in cats:
			if str(c['categoryId']) == str(game_id):
				return Game(c)
		raise Exception(f"Category ID {game_id} not found")


	def set(self, name):
		# Try abbr first
		name = norm(name)
		if name not in self.sets:
			def _lkup(nm):
				try:
					return Set.by_abbr(self, nm)
				except:
					return Set.by_name(self, nm)
			s = _lkup(name)
			self.sets[name] = s
			self.sets[s.name] = s
			self.sets[s.abbreviation] = s

		return self.sets[name]


	'''
	def card(self, name):
		for g in fetch(f'{self.category_id}/groups'):
			for c in (s:=Set(self, g)).cards:
				if 'Luffy' in c.name and 'Monkey' in c.name:
					# print(ll.regf('\([^)]*\)')(c.name))
					if 'OP07' not in s.abbreviation:
						continue
					print(c.name, s.abbreviation, c.category_id, c.group_id, c.product_id)
	'''

	def card(self, abbr, num, limit=1):
		return Set.by_abbr(self, abbr).card(num)
