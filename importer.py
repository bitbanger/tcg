import ll

from collection import fmt_row, parse_row
from model import Game, Set, CardSet


def main():
	added_card_rows = []

	for fn in ll.arg('fns', nargs='+'):
		lines = ll.lines(fn)
		game = lines[0]
		set = lines[1]
		nums = lines[2:]

		g = Game.by_name(game)
		s = g.set(set)

		for num in nums:
			var = ''
			num = CardSet.normnum(num)
			if len(spl:=num.strip().split()) > 1:
				num = spl[0]
				var = ' '.join(spl[1:])

			cards = s.card(num, limit=None)
			cards_and_vars = ll.flatten([[(card, _var) for _var in card.variants] for card in cards])
			cards_and_vars = [(c, v) for c, v in cards_and_vars if ((not var) or (v.lower().strip()==var.lower().strip()))]

			if len(cards_and_vars) > 1:
				# For each card, also list all of its variants
				opts = [f'{c} ({v})' for c, v in cards_and_vars]
				try:
					card, var = cards_and_vars[ll.options(opts, idx=True)]
				except KeyboardInterrupt:
					print('')
					quit(1)
			else:
				card, var = cards_and_vars[0]

			if card is None:
				ll.err(f'no card found for {num}')

			# Render the coll.csv row
			# all_vars = ll.no_nones(ll.regf('\(([^)]*)\)', all=True)(card.name) + [var] if var else [])
			all_vars = [var]
			row_name = card.name
			# for av in all_vars:
				# row_name = row_name.replace(f' ({av})', '')

			price = card.price(var=var)

			row = {
				'tcg_category_id': card.category_id,
				'tcg_group_id': card.group_id,
				'tcg_product_id': card.product_id,
				'tcg_subtype': var,
				'game': g.name,
				'set': s.name,
				'number': card.number,
				'name': row_name,
				'vars': ','.join(all_vars),
				'rarity': card.rarity,
				'value': price,
				'value_updated': ll.ctime(f'data/prices/{card.category_id}/{card.group_id}.json'),
				'language': 'en',
			}
			# print(ll.csv(row).strip())

			# if price > 10:
			varstr = ' ' + ' '.join([f'[grey70]({v})[/grey70]' for v in all_vars])
			print(fmt_row(row))
			# print(f'\t[bold blue]{card}{varstr}[/bold blue]')
			if price > 20:
				col = 'rgb(0,200,75)'
			elif price > 10:
				col = 'rgb(0,100,37)'
			else:
				col = 'grey70'
				# print(f'\t\t[grey70]${}[/grey70]')
			# print(f'\t\t[{col}]${price}[/{col}]')

			card = card.realize(variant=var)
			row['condition'] = ''
			row['psa_10'] = card.graded_price(grade='manual-only-price') or ''
			row['cgc_10'] = card.graded_price(grade='condition-17-price') or ''
			row['grade_9'] = card.graded_price(grade='graded-price') or ''

			added_card_rows.append(row)
			# ll.rule(row_name + varstr)
			# print(card.image())
			# ll.rule(f'${price:.02f}', pre_space=0, post_space=2)

	print('')
	ll.rule()

	def skey(r):
		_card, _, subtype = parse_row(r)
		return _card.price()
	added_card_rows = sorted(added_card_rows, key=skey)
	for row in added_card_rows:
		print(fmt_row(row))

	print('')
	cs = added_card_rows
	gcs = [x for x in cs if skey(x)>=5]
	ttl_val = sum(skey(x) for x in cs)
	ttl_good_val = sum(skey(x) for x in gcs)
	ll.rule(f'Total value for {len(cs)} [grey70]([/grey70]{len(gcs)}[grey70])[/grey70] cards: [green]${ttl_val:,.2f}[/green] ([green]${ttl_good_val:,.2f}[/green])')
	print('')

	try:
		ans = ll.yn("Add these cards to your collection?")
	except KeyboardInterrupt:
		quit(1)
	if ans:
		cfn = ll.here('_collection/coll.csv')
		for i, row in enumerate(added_card_rows):
			if i==0 and (not ll.fexists(cfn)):
				ll.write(cfn, ll.csv(row.keys()).strip())
			ll.append(cfn, ll.csv(row).strip())
		# for c in Game(game).set(set).cards:
			# print(c.name, c.number, c.price())


if __name__ == '__main__':
	main()
