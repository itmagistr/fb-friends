# -*- coding: utf-8 -*-

import argparse
import time
import datetime
#import pyperclip
from fb_parser import *
import logging
logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)
logging.getLogger().addHandler(logging.FileHandler("fb_friends.log"))

def main(opts):
	fbparse = FBParser(pdriver=opts.webdriver, ptimeout=opts.timeout)
	#fbdb = FBDB()
	if opts.inFL == '-' :
		profiles=[opts.fbID]
	else:
		with open(opts.inFL, 'r') as infl:
			profiles=[l.strip() for l in infl.readlines()]
	
	for p in profiles:
		fbparse.nav2Profile(p)
		cnt = fbparse.nav2Friends()
		logging.info('Выполнен переход на закладку Друзья: {}'.format(cnt))
		logging.info('Листаем список ...')
		fbparse.scroll2EndPG()
		logging.info('Сохраняем список друзей ...')
		fl = fbparse.save2File(p)

		#fbparse.parseFriends() # парсинг распараллелим отдельным сценарием
		logging.info(fl)

	logging.info('Работа скрипта завершена.')
	return 0

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('--timeout', help='waiting timeout to load the page', default='10')
	parser.add_argument('--webdriver', help='web driver path', default='C:\\bin\\webdriver\\chromedriver')
	parser.add_argument('--fbID', help='facebook ID page', default='-')
	parser.add_argument('--inFL', help='the file of facebook ID pages', default='-')
	args = parser.parse_args()
	main(args)

	# python
