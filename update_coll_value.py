import ll
import sys

from argparse import ArgumentParser
from collection import parse_row
from model import CardSet


def main():
	ap = ArgumentParser()
	ap.add_argument('-g', '--graded', action='store_true')
	args = ap.parse_args()

	# Parse CSV
	coll_path = '_collection/coll.csv'
	rows = ll.csv(coll_path)

	for row in ll.track(rows):
		try:
			card, _, subtype = parse_row(row)
		except:
			continue

		if args.graded:
			row['psa_10'] = card.graded_price(grade='manual-only-price') or ''
			row['cgc_10'] = card.graded_price(grade='condition-17-price') or ''
			row['grade_9'] = card.graded_price(grade='graded-price') or ''

		# Update row
		match row['condition']:
			case 'CGC 10':
				price = row['cgc_10']
				price_updated = ll.ctime(f'data/scp_{card.game.name.lower()}_prices.json')
			case 'PSA 10':
				price = row['psa_10']
				price_updated = ll.ctime(f'data/scp_{card.game.name.lower()}_prices.json')
			case 'PSA 9':
				price = row['grade_9']
				price_updated = ll.ctime(f'data/scp_{card.game.name.lower()}_prices.json')
			case _:
				price = card.price()
				price_updated = ll.ctime(f'data/prices/{card.category_id}/{card.group_id}.json')

		row['value'] = price
		row['value_updated'] = price_updated

	# Back up old CSV
	base_fn = '.coll.csv.backup'
	backup = 0
	while ll.fexists(backup_path:=f'_collection/{base_fn}{backup}'):
		backup += 1
	ll.mv(coll_path, backup_path)

	# Write new CSV
	with open(coll_path, 'w+') as f:
		for line in ll.lines(ll.csv(rows)):
			f.write(line + '\n')


if __name__ == '__main__':
	main()
