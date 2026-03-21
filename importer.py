import ll

from collection import fmt_row, parse_row
from model import Game, Set, CardSet


def main():
	added_card_rows = []

	rows = []
	for fn in ll.arg('fns', nargs='+'):
		game = None
		set = None
		last_filt = ''
		for line in ll.lines(fn):
			line = line.strip()

			if len(spl:=line.strip().split('/')) >= 3:
				_, _game, _set = ll.map(ll.strip, spl)
				game = Game.by_name(_game)
				set = game.set(_set)
				last_filt = ''
				last_var = ''
				continue
			else:
				if line.startswith('[') and line.endswith(']'):
					# Persistent variant declaration
					last_var = line[1:-1].strip()
				elif line.startswith('(') and line.endswith(')'):
					# Persistent name filter declaration
					last_filt = line[1:-1].strip()
				else:
					# Card
					if (game is None) or (set is None):
						raise Exception(f"Gotta declare /game/set before you can list cards")

					num = line
					var, filt = last_var, last_filt
					# if (_filt:=ll.regf('\\((.*)\\)')(num)):
					if '(' in num and ')' in num:
						_filt = num.split('(')[-1].split(')')[0]
						num = num.replace(f'({_filt})', '').strip()
						filt = _filt.strip()
						while '  ' in num:
							num = num.replace('  ', ' ').strip()
					if '[' in num and ']' in num:
						_var = num.split('[')[-1].split(']')[0]
						num = num.replace(f'[{_var}]', '').strip()
						var = _var.strip()
						while '  ' in num:
							num = num.replace('  ', ' ').strip()

					possibles = set.cards(num, filter=filt)
					possibles = ll.flatten([[c.realize(v) for v in c.variants] for c in possibles])
					possibles = [c for c in possibles if (not var) or var.lower()==c.variant.lower()]

					opts = ll.map(ll.dotcall('fmt_no_price'), possibles)
					if len(possibles) > 1:
						card = possibles[ll.options(opts, idx=True)]
					else:
						card = possibles[0]

					row = {
						'tcg_category_id': card.category_id,
						'tcg_group_id': card.group_id,
						'tcg_product_id': card.product_id,
						'tcg_subtype': card.variant,
						'game': game.name,
						'set': set.name,
						'number': card.number,
						'name': card.name,
						'vars': card.variant,
						'rarity': card.rarity,
						'value': card.price(),
						'value_updated': ll.ctime(f'data/prices/{card.category_id}/{card.group_id}.json'),
						'language': 'en',
						'condition': '',
						'psa_10': card.graded_price(grade='manual-only-price') or '',
						'cgc_10': card.graded_price(grade='condition-17-price') or '',
						'grade_9': card.graded_price(grade='graded-price') or '',
					}
					print(card.fmt())
					rows.append(row)

	gcs = [x for x in rows if x['value'] >= 5]
	ttl_val = sum(r['value'] for r in rows)
	ttl_good_val = sum(r['value'] for r in gcs)
	ll.rule(f'Total value for {len(rows)} [grey70]([/grey70]{len(gcs)}[grey70])[/grey70] cards: [green]${ttl_val:,.2f}[/green] ([green]${ttl_good_val:,.2f}[/green])')
	print('')

	try:
		ans = ll.yn("Add these cards to your collection?")
	except KeyboardInterrupt:
		quit(1)
	if ans:
		cfn = ll.here('_collection/coll.csv')
		for i, row in enumerate(rows):
			if i==0 and (not ll.fexists(cfn)):
				ll.write(cfn, ll.csv(row.keys()).strip())
			ll.append(cfn, ll.csv(row).strip())


if __name__ == '__main__':
	main()
