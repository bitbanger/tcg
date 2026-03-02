import ll

from model import Card


def main():
	cards = []
	for row in ll.csv('_collection/coll.csv'):
		card = Card.by_id(row['tcg_category_id'], row['tcg_group_id'], row['tcg_product_id'])
		cards.append(card)
		print(card.rarity)

	print(f'\n{len(cards)} cards')


if __name__ == '__main__':
	main()
