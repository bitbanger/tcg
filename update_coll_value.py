import ll
import sys

from collection import parse_row
from model import Card


def main():
	# Parse CSV
	coll_path = '_collection/coll.csv'
	rows = ll.csv(coll_path)

	for row in rows:
		card, _, subtype = parse_row(row)

		price = card.price(var=subtype)
		price_updated = ll.ctime(f'data/prices/{card.category_id}/{card.group_id}.json')

		# Update row
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
