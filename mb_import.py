import ll

from model import Game, Set, CardSet

# Name,Set code,Set name,Collector number,Foil,Rarity,Quantity,ManaBox ID,Scryfall ID,Purchase price,Misprint,Altered,Condition,Language,Purchase price currency

# Become Anonymous,ACR,Assassin's Creed,14,normal,uncommon,1,95532,long,0.12,false,false,near_mint,en,USD

def main():
	mtg = Game.by_name('magic')
	sc2set = {}
	for row in ll.csv('ManaBox_Collection.csv'):
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

if __name__ == '__main__':
	main()
