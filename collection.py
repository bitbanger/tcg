import ll

from model import Card, CardSet

GRADE = 'condition-17-price'

def parse_row(row):
	cat_id = row['tcg_category_id']
	group_id = row['tcg_group_id']
	product_id = row['tcg_product_id']
	subtype = row['tcg_subtype']
	card = Card.by_id(row['tcg_category_id'], row['tcg_group_id'], row['tcg_product_id'], variant=subtype)

	return (card, row['vars'].split(','), subtype)


def fmt_row(row):
	card, vs, subtype = parse_row(row)
	# cs = CardSet.fmt(card, vs, subtype)
	return card.fmt()


def main():
	def _card(row):
		cat = row['tcg_category_id']
		gr = row['tcg_group_id']
		pr = row['tcg_product_id']
		va = row['tcg_subtype']
		try:
			card = Card.by_id(cat, gr, pr, variant=va)
		except Exception as e:
			card = None

		if str(pr).startswith('fake_id'):
			class A: pass
			mag = 0.75
			vcol = f'rgb({int(100*mag)},{int(100*mag)},{int(175*mag)})'
			vstr = f' [{vcol}]{va}[/{vcol}]' if va else ''
			price = float(row['value'])
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
			pstr = f'${price:,.2f}'
			A.fmt = lambda self, grade=None: f'[{pcol}][/{pcol}]\t[khaki3]{row["name"]}[/khaki3] [blue]#{row["number"]}[/blue]' + vstr
			A.price = lambda self: float(price)
			A.graded_price = lambda self, grade=None: None
			a = A()
			return a
		else:
			return Card.by_id(cat, gr, pr, variant=va)

	rows = ll.csv(ll.arg('-f', '--file', default='_collection/coll.csv'))
	cards = [_card(row)
		for row in rows]

	# cards = sorted(cards, key=ll.dotcall('price'))
	# cards = sorted(cards, key=ll.dotcall('graded_price'))
	cards = sorted(cards, key=lambda c: c.graded_price(grade=GRADE) or 0)

	for card in cards:
		print(card.fmt(grade=GRADE))
		if ll.arg('-i', '--images', action='store_true'):
			print('')
			print(card.image())
			print('')

	print('')
	cs = cards
	gcs = [x for x in cs if x.price()>=5]
	ttl_val = sum(x.price() for x in cs)
	ttl_good_val = sum(x.price() for x in gcs)
	ll.rule(f'Total value for {len(cs)} [grey70]([/grey70]{len(gcs)}[grey70])[/grey70] cards: [green]${ttl_val:,.2f}[/green] ([green]${ttl_good_val:,.2f}[/green])')
	print('')



if __name__ == '__main__':
	main()
