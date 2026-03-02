import ll

from model import Game, Set, Card

def main():
	for fn in ll.arg('fns', nargs='+'):
		lines = ll.lines(fn)
		game = lines[0]
		set = lines[1]
		nums = lines[2:]

		g = Game.by_name(game)
		s = g.set(set)

		for num in nums:
			var = ''
			num = Card.normnum(num)
			if len(spl:=num.strip().split()) > 1:
				num = spl[0]
				var = ' '.join(spl[1:])

			cards = s.card(num, limit=None)

			if len(cards) > 1:
				card = cards[ll.options(cards, idx=True)]
			else:
				card = cards[0]

			if len(card.variants) == 1:
				var = card.variants[0]

			# Render the coll.csv row
			all_vars = ll.no_nones(ll.regf('\(([^)]*)\)', all=True)(card.name) + [var] if var else [])
			row_name = card.name
			for av in all_vars:
				row_name = row_name.replace(f' ({av})', '')

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
			}
			# print(ll.csv(row).strip())
			cfn = ll.here('_collection/coll.csv')
			if not ll.fexists(cfn):
				ll.write(cfn, ll.csv(row.keys()).strip())
			ll.append(cfn, ll.csv(row).strip())

			if card is None:
				ll.err(f'no card found for {num}')
			price = card.price(var=var)
			if price > 10:
				varstr = ' ' + ' '.join([f'[grey70]({v})[/grey70]' for v in all_vars])
				ll.rule(row_name + varstr)
				print(card.image())
				ll.rule(f'${price:.02f}', pre_space=0, post_space=2)
		# for c in Game(game).set(set).cards:
			# print(c.name, c.number, c.price())


if __name__ == '__main__':
	main()
