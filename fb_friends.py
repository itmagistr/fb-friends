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
	fbparse.nav2Profile(opts.fbID)
	cnt = fbparse.nav2Friends()
	logging.info('Выполнен переход на закладку Друзья: {}'.format(cnt))
	logging.info('Листаем список ...')
	fbparse.scroll2EndPG()
	logging.info('Сохраняем список друзей ...')
	fl = fbparse.save2File()

	fbparse.parseFriends()
	logging.info(fl)
	logging.info('Работа скрипта завершена.')
	return 0

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('--timeout', help='waiting timeout to load the page', default='10')
	parser.add_argument('--webdriver', help='web driver path', default='C:\\bin\\webdriver\\chromedriver')
	parser.add_argument('--fbID', help='facebook ID page', default='-')
	args = parser.parse_args()
	main(args)

	# python
