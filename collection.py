import ll

from model import Card


def parse_row(row):
	cat_id = row['tcg_category_id']
	group_id = row['tcg_group_id']
	product_id = row['tcg_product_id']
	card = Card.by_id(row['tcg_category_id'], row['tcg_group_id'], row['tcg_product_id'])
	subtype = row['tcg_subtype']

	return (card, row['vars'].split(','), subtype)


def fmt_row(row):
	card, vs, subtype = parse_row(row)
	return Card.fmt(card, vs, subtype)


def main():
	cards = []
	for row in ll.csv('_collection/coll.csv'):
		card = Card.by_id(row['tcg_category_id'], row['tcg_group_id'], row['tcg_product_id'])
		cards.append(card)
		print(card.rarity)

	print(f'\n{len(cards)} cards')


if __name__ == '__main__':
	main()
