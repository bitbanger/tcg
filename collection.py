import ll

from model import CardSet


def parse_row(row):
	cat_id = row['tcg_category_id']
	group_id = row['tcg_group_id']
	product_id = row['tcg_product_id']
	card = CardSet.by_id(row['tcg_category_id'], row['tcg_group_id'], row['tcg_product_id'])
	subtype = row['tcg_subtype']

	return (card, row['vars'].split(','), subtype)


def fmt_row(row):
	card, vs, subtype = parse_row(row)
	return CardSet.fmt(card, vs, subtype)


def main():
	cards = []
	variants = []
	for row in ll.csv('_collection/coll.csv'):
		card = CardSet.by_id(row['tcg_category_id'], row['tcg_group_id'], row['tcg_product_id'])
		cards.append(card)
		variants.append(row['tcg_subtype'])
		# print(card.fmt_card(var=row['tcg_subtype']))
		# print(fmt_row(row))
	cards_and_variants = sorted(zip(cards, variants), key=lambda t: t[0].price(var=t[1]))
	for card, var in cards_and_variants:
		print(card.fmt(card, card.variants, var))

	print(f'\n{len(cards)} cards')


if __name__ == '__main__':
	main()
