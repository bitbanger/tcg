import ll

from model import Game, Set, CardSet

# Name,Set code,Set name,Collector number,Foil,Rarity,Quantity,ManaBox ID,Scryfall ID,Purchase price,Misprint,Altered,Condition,Language,Purchase price currency

# Become Anonymous,ACR,Assassin's Creed,14,normal,uncommon,1,95532,long,0.12,false,false,near_mint,en,USD

def main():
	scry2tcg = {}
	sfn = 'data/scryfall.json'
	buf = []
	for l in ll.track(ll.lines(sfn, stream=True), total=ll.wc_l(sfn)):
		buf.append(l)
	for r in ll.track(ll.json('\n'.join(buf))):
		if 'tcgplayer_id' in r:
			scry2tcg[r['id']] = r['tcgplayer_id']

	total = 0
	bad = 0
	for row in ll.track(ll.csv('mtg.csv', stream=True), total=ll.wc_l('mtg.csv')-1):
		total += 1
		scry_id = row['Scryfall ID']
		if scry_id not in scry2tcg:
			print(row)
			bad += 1
		continue
	print(f'{bad}/{total}')

	'''
	mtg = Game.by_name('magic')
	tcg2prod = {}
	for g in ll.track(ll.json(ll.read('data/groups/1.json'))):
		s = Set.by_id(mtg, g['groupId'])
		for c in s.all_cards:
			tcg2prod[c.product_id] = c
	'''

	'''
	mtg = Game.by_name('magic')
	sc2set = {}
	for row in ll.csv('mtg.csv'):
		sc = row['Set code']
		if sc == 'PLST':
			sc = 'LIST' # :/
		if len(sc)==4 and sc.startswith('P'):
			sc = 'P' + sc
		match sc:
			case 'DVD':
				sc = 'DDC'
			case 'GDY':
				sc = 'GAME'
			case 'F17':
				print('Have to use name and number for F17->FNM')
				quit()
				sc = 'FNM'
		if sc not in sc2set:
			sc2set[sc] = Set.by_abbr(mtg, sc)
		print(sc2set[sc].abbreviation)
		continue
		print(ll.csv(row.keys()))
		print('')
		print(ll.csv(row.values()))
		quit()

	pass
	'''

if __name__ == '__main__':
	main()
