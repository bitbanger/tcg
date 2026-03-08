import ll

from model import Card


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

	print(f'\n{len(cards)} cards')


if __name__ == '__main__':
	main()
