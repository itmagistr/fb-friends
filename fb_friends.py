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
	

	if opts.scen == '1':
		# читаем список друзей указанного профиля
		cnt = fbparse.nav2Friends()
		logging.info('Выполнен переход на закладку Друзья: {}'.format(cnt))
		logging.info('Листаем список ...')
		fbparse.scroll2EndPG()
		logging.info('Сохраняем список друзей ...')
		fl = fbparse.save2File('fbfriends')

		fbparse.parseFriends()
		logging.info(fl)
	elif opts.scen == '2':
		# читаем список запросов в друзья указанного профиля
		frReqs = fbparse.getFriendReqList()
		lenfr = len(frReqs)
		logging.info(f'Запросов в друзья {lenfr}')
		for fr in frReqs:
			frparse = FBParser(pdriver=opts.webdriver, ptimeout=opts.timeout)
			frparse.nav2Profile(fr, fbparse.runUID)
			fl = frparse.save2File('frLenta')
			logging.info(f'Лента постов профиля {fr} сохранена в файле {fl}')
			time.sleep(5)
			


	logging.info('Работа скрипта завершена.')
	return 0

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('--timeout', help='waiting timeout to load the page', default='10')
	parser.add_argument('--webdriver', help='web driver path', default='C:\\bin\\webdriver\\chromedriver')
	parser.add_argument('--fbID', help='facebook ID page', default='-')
	parser.add_argument('--scen', help='choose the user story', default='1')
	args = parser.parse_args()
	main(args)

	# python
