import json as _json
import ll
import os

from datetime import datetime, timedelta


def p2pcol(price):
	if price >= 50:
		pcol = 'rgb(0,200,75)'
	elif price >= 20:
		pcol = 'rgb(0,130,37)'
	elif price >= 10:
		pcol = 'rgb(0,80,15)'
	elif price >= 2:
		pcol = 'grey50'
	else:
		pcol = 'grey30'
	return pcol


class AmbiguousError(Exception): pass


def norm(s):
	return ''.join(c.lower() for c in s if c.lower() in 'abcdefghijklmnopqrstuvwxyz 0123456789')


_global_fetch_cache = dict()

_graded_prices = ll.dd(dict)
def graded_prices(game, stale_days=1):
	global _graded_prices

	# Be forgiving about the input
	if isinstance(game, Game):
		game = game.name
	elif isinstance(game, int):
		game = Game.by_id(game).name
	elif isinstance(game, str) and game.isnumeric():
		game = Game.by_id(int(game)).name

	# We can only bulk download some game CSVs
	game = game.lower().strip()
	if game not in ('magic', 'pokemon', 'one-piece', 'yugioh'):
		return {}

	data_dir = ll.here('data')
	fn = f'scp_{game}_prices.json'
	path = ll.ospj(data_dir, fn)

	# Download the price data if necessary
	if (not ll.fexists(path)) or (ll.age(path) >= ll.days(stale_days)):
		def _prices(row):
			_price = lambda s: float(s[1:]) if s else None
			return {k: _price(v) for k, v in row.items() if '-price' in k}

		url = f"https://www.pricecharting.com/price-guide/download-custom?t={ll.env('SCP_API_TOKEN')}&category={game}-cards"
		_rows = ll.csv(ll.sel_dl(url, clobber=True, tries=30))

		d = {str(r['tcg-id']): _prices(r) for r in _rows}

		ll.write(path, _json.dumps(d, indent=2))

	# Load & return the prices
	if game not in _graded_prices:
		_graded_prices[game] = _json.loads(ll.read(path))
	return _graded_prices[game]


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

		self._game = None
		self._set = None


	# TODO: figure out why the game & set members have to be
	# properties to avoid an infinite recursion issue :/
	@property
	def game(self):
		if self._game is None:
			self._game = Game.by_id(self.category_id)
		return self._game


	@property
	def set(self):
		if self._set is None:
			self._set = Set.by_id(self.game, self.group_id)
		return self._set


	@staticmethod
	def normnum(s):
		n = ''.join(c.lower() for c in s if c.lower() in 'abcdefghijklmnopqrstuvwxyz */0123456789')
		if '/' in n and '//' not in n:
			n = n.split('/')[0].strip()
		while n.startswith('0'):
			n = n[1:]
		return n


	def realize_all(self):
		return [self.realize(variant=v) for v in self.variants]


	def realize(self, variant=None):
		if variant is None:
			return self.realize(variant=ll.options(self.variants))

		return Card.from_card_set(self, variant=variant)


	def prices(self):
		return {k: v for k, v in self.var2prices.items()} # copy


	def image(self, stale_days_404=1):
		ext = self.image_url.split('.')[-1]
		img_path = f'{self.category_id}/{self.group_id}/'
		img_fn = f'{self.product_id}.{ext}'
		path = ll.ospj(ll.here(f'data/images'), img_path, img_fn)

		os.makedirs(ll.dirname(path), exist_ok=True)

		no_img_path = ll.ospj(ll.here(f'data/images/.no_imgs'), img_path, img_fn)

		if ll.fexists(no_img_path) and ((datetime.now()-ll.dt(ll.read(no_img_path)))<=timedelta(days=stale_days_404)):
			return '(no image)'

		if not ll.fexists(path):
			resp = ll.http(self.image_url, b=True)
			if len(resp) < 9001:
				ll.write(no_img_path, ll.dt(datetime.now()))
				return '(no image)'

			try:
				os.remove(no_img_path)
			except FileNotFoundError:
				pass
			ll.write(path, resp, swap=False)

		return path


	def vsstr(self, vs=None):
		return ll.andify(vs or self.var2prices.keys(), quote="'")


	def price(self, var=None, safe=False):
		try:
			if (not var):
				if len(self.var2prices)==1:
					var = list(self.var2prices.keys())[0]
				else:
					vsstr = ll.andify(self.var2prices.keys(), quote="'")
					raise AmbiguousError(f"{str(self)} has multiple variants ({vsstr}); pick one, please")

			return self.prices()[norm(var)]
		except Exception as e:
			if safe:
				return 0.0
			else:
				raise e


	def min_price(self):
		return min(self.var2prices.values())


	def max_price(self):
		return max(self.var2prices.values())


	def max_price_variant(self):
		return max(self.var2prices.items(), key=ll.nth(1))[0]


	@staticmethod
	def fmt(card, vs, variant):
		price = card.price(var=variant)

		name_col = 'khaki3'
		num_col = 'blue'
		mag = 0.75
		vcol = f'rgb({int(100*mag)},{int(100*mag)},{int(175*mag)})'
		pcol = p2pcol(price)

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
	@ll.cache(stale=ll.days(1))
	def by_id(game_id, set_id, card_id):
		cards = fetch(f'{game_id}/{set_id}/products')
		for c in cards:
			if str(c['productId']) == str(card_id):
				return CardSet(c)
		raise Exception(f"Product ID {card_id} (category ID {game_id}, group ID {set_id}) not found")




	def __iter__(self):
		return (c for c in self.realize_all())


	def __str__(self):
		return f'{self.name} #{self.number}' + (f' (variants: {self.vsstr()})' if len(self.variants)>1 else '')


class Card(CardSet):
	def __init__(self, json, variant=None, choose=True):
		super().__init__(json)

		if variant is None:
			if len(self.variants) > 1:
				if not choose:
					raise AmbiguousError(f"Multiple possible variants for card '{super().__str__()}'")
				variant = ll.options(self.variants)
			else:
				variant = self.variants[0]

		self.possible_variants = self.variants
		self.variant = variant
		if self.variant.lower() not in ll.map(ll.lower, self.possible_variants):
			raise Exception(f"Variant '{self.variant}' not one of the possible variants for card '{self}' ({self.vsstr()})")


	def price(self):
		return super().price(var=self.variant)


	def graded_price(self, grade='condition-17-price', stale_days=1):
		return (graded_prices(self.game.name).get(str(self.product_id)) or {}).get(grade)


	def __str__(self):
		name = self.name.split(' (variants')[0]
		return f'{name} #{self.number} ({self.variant})'


	def fmt(self, grade='manual-only-price', show_price=True):
		price = self.price()

		name_col = 'khaki3'
		num_col = 'blue'
		mag = 0.75
		vcol = f'rgb({int(100*mag)},{int(100*mag)},{int(175*mag)})'
		pcol = p2pcol(price)

		match grade:
			case 'manual-only-price':
				gstr = 'PSA 10'
			case 'condition-17-price':
				gstr = 'CGC 10'
			case _:
				gstr = grade
		pstr = f'[{pcol}]${price:.02f}[/{pcol}]'

		s = f'{pstr}\t' if show_price else ''
		name = self.name.split(' (variants')[0]
		s += f'[{name_col}]{name}[/{name_col}] [{num_col}]#{self.number}[/{num_col}] [{vcol}]{self.variant}[/{vcol}]'
		if show_price and (gprc:=self.graded_price(grade=grade)):
			s += f'\t[grey70]({gstr}: ${gprc:,.2f})[/grey70]'

		return s


	def fmt_no_price(self):
		return self.fmt(show_price=False)


	@staticmethod
	def from_card_set(cs, variant=None):
		return Card(cs.json, variant=variant)


	@staticmethod
	@ll.cache(stale=ll.days(1))
	def by_id(game_id, set_id, card_id, variant=None):
		return Card.from_card_set(
			CardSet.by_id(game_id, set_id, card_id),
			variant=variant,
		)


	def __iter__(self):
		# Just lie:
		raise TypeError(f"'Card' object is not iterable")


	def __eq__(self, other):
		return hash(self) == hash(other)


	def __hash__(self):
		return ll.md5_int(self.game.name + self.set.name + self.name + self.number + self.variant)


# this is the end of the Card class definition


class Set:
	def __init__(self, game, json):
		self.game = game
		self.json = json

		for k, v in self.json.items():
			setattr(self, ll.uncamel(k), v)

		self.all_cards = []
		# TODO: differentiate cards from boxes, etc.?
		for c in fetch(f'{self.game.category_id}/{self.group_id}/products'):
			if 'extendedData' not in c or (not any(e['name']=='Number' for e in c['extendedData'])):
				# It's not a card
				continue
			self.all_cards.append(CardSet.by_id(self.game.category_id, self.group_id, c['productId']))

		self.abbr = self.abbreviation


	@staticmethod
	@ll.cache(stale=ll.days(1))
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
	@ll.cache(stale=ll.days(1))
	def by_id(game, set_id):
		for g in fetch(f'{game.category_id}/groups'):
			if str(g['groupId']) == str(set_id):
				return Set(game, g)
		raise Exception(f"Group ID {set_id} (category ID {game.category_id}) not found")


	@staticmethod
	@ll.cache(stale=ll.days(1))
	def by_abbr(game, abbr):
		for g in fetch(f'{game.category_id}/groups'):
			if g['abbreviation'].lower() == abbr.lower():
				return Set(game, g)
		raise Exception(f"Group abbreviation '{abbr}' (category ID {game.category_id}) not found")


	def cards(self, num, filter=''):
		cands = []
		for c in self.all_cards:
			if CardSet.normnum(c.number) == CardSet.normnum(str(num)):
				if filter.lower() in c.name.lower():
					for cc in c.realize_all():
						cands.append(cc)
		return cands


	def card(self, num, variant=None, filter='', choose=True):
		# return self.card(num, filter=filter).realize_all()
		cards = [c for c in self.cards(num, filter=filter)
			if ((variant is None) or (c.variant==variant))]
		if len(cards) == 1:
			return cards[0]
		elif not choose:
			cardsstr = ll.andify(cards, quote="'")
			raise AmbiguousError(f"Too many {self.game.name} {self.name} cards with number {num} ({cardsstr})")
		else:
			return ll.options(cards)


	def __str__(self):
		return f'{self.name} ({self.abbreviation})'


	def __hash__(self):
		return ll.md5_int(self.game.name + self.name)


class Game:
	def __init__(self, json, query=None):
		self.json = json
		self.query = query

		for k, v in self.json.items():
			setattr(self, ll.uncamel(k), v)

		self._sets = {}
		self._loaded = False


	@staticmethod
	@ll.cache(stale=ll.days(1))
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
	@ll.cache(stale=ll.days(1))
	def by_id(game_id):
		cats = fetch(f'categories')
		for c in cats:
			if str(c['categoryId']) == str(game_id):
				return Game(c)
		raise Exception(f"Category ID {game_id} not found")


	def set(self, name):
		# Try abbr first
		name = norm(name)
		if name not in self._sets:
			def _lkup(nm):
				try:
					return Set.by_abbr(self, nm)
				except:
					return Set.by_name(self, nm)
			s = _lkup(name)
			self._sets[name] = s
			self._sets[s.name] = s
			self._sets[s.abbreviation] = s

		return self._sets[name]


	@property
	def sets(self):
		if not self._loaded:
			gs = ll.json(ll.read(f'data/groups/{self.category_id}.json'))
			for s in ll.track(gs):
				ss = Set.by_id(self, s['groupId'])
				if ss.name in self._sets:
					continue
				self._sets[ss.name] = ss
				self._sets[ss.abbreviation] = ss
			self._loaded = True

		seen = set()
		ret = []
		for k, v in self._sets.items():
			if v.group_id not in seen:
				seen.add(v.group_id)
				ret.append(v)
		return ret


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

	def card(self, nabbr, num, filter='', variant=None, choose=True):
		return self.set(nabbr).card(num, filter=filter, variant=variant, choose=choose)


	def cards(self, nabbr, num, filter=''):
		return self.set(nabbr).cards(num, filter=filter, limit=limit)


	def __hash__(self):
		return ll.md5_int(self.name)

