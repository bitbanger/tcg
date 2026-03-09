import ll

from model import Card, CardSet


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
	cards = [Card.by_id(
		row['tcg_category_id'],
		row['tcg_group_id'],
		row['tcg_product_id'],
		variant=row['tcg_subtype'],
	) for row in ll.csv('_collection/coll.csv')]

	cards = sorted(cards, key=ll.dotcall('price'))

	for card in cards:
		print(card.fmt())
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
