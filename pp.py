import ll

from collection import parse_row
from model import CardSet, Game, Set

tcg_id_to_srow = {}
for row in ll.track(ll.csv('data/scp/pokemon.csv', stream=True), total=ll.wc_l('data/scp/pokemon.csv')):
	if 'tcg-id' not in row:
		continue
	tcg_id_to_srow[row['tcg-id']] = row


def main():
	for row in ll.csv('_collection/coll.csv', stream=True):
		if row['game'] != 'Pokemon':
			continue
		try:
			raw_price = tcg_id_to_srow[row['tcg_product_id']]['loose-price']
			print(f"{raw_price}\t{row['name']}")
		except:
			print(f'not found: {row["name"]}')
	quit()

	for row in []:
		if row['game'] != 'Pokemon':
			continue
		if 'misc' not in row['set'].lower():
			continue

		card, vs, subtype = parse_row(row)

		vs = [v.lower().replace('holofoil', 'holo') for v in vs]
		nvs = []
		for v in vs:
			v = v.lower()
			v = v.replace('holofoil', 'holo')
			if v.endswith('stamped'):
				v = 'stamped'
			v = ' '.join(ll.uppercamel(w) for w in v.strip().split())
			nvs.append(v)
		nvs = sorted(nvs)
		vs = nvs

		for i in range(len(vs)):
			if vs[i] not in ('Holo', 'Reverse Holo'):
				vs = [vs[i]]
				break

		set = Set.by_id(Game.by_id(card.category_id), card.group_id)
		sset = 'Pokemon ' + set.name.split(':')[-1].strip()

		poke_name = card.name.split('(')[0].strip()
		poke_num = card.number

		vsstr = ' ' + ' '.join(f'[{v}]' for v in vs)
		print(f'{poke_name} #{poke_num}{vsstr}')


		# for srow in ll.csv('data/scp/pokemon.csv'):
			# print(srow)


if __name__ == '__main__':
	main()
