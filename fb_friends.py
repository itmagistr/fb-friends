# -*- coding: utf-8 -*-
import asyncio
import argparse
import time
import datetime
#import pyperclip
from fb_parser import *
from fb_posts import ParseLenta
from fb_frcards import *

import logging
logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)
logging.getLogger().addHandler(logging.FileHandler("fb_friends.log"))

def main(opts):
	if opts.scen=='01':
		run01_CollectFrCards(opts)
		logging.info(f'Выполнение сценария {opts.scen} завершено')
		return 1
	elif opts.scen=='02':
		run02_ParseFileFrCards(opts)
		logging.info(f'Выполнение сценария {opts.scen} завершено')
		return 2
	elif opts.scen=='031':
		run031_CollectPosts(opts)
		logging.info(f'Выполнение сценария {opts.scen} завершено')
		return 31
	elif opts.scen=='032':
		run032_CollectPosts(opts)
		logging.info(f'Выполнение сценария {opts.scen} завершено')
		return 31
	elif opts.scen=='041':
		run041_ParsePosts(opts)
		logging.info(f'Выполнение сценария {opts.scen} завершено')
		return 41
	elif opts.scen == '05':
		run05_CollectFrRequest(opts)
		logging.info(f'Выполнение сценария {opts.scen} завершено')
	elif opts.scen == '11':
		run11_ListCollectFrCards(opts)
		logging.info(f'Выполнение сценария {opts.scen} завершено')
	else:
		logging.info(f'сценарий {opts.scen} не доступен к запуску')
		return -1
	logging.info('Работа скрипта завершена.')
	return 0

def run01_CollectFrCards(opts):
	fbparse = FBParser(pdriver=opts.webdriver, ptimeout=opts.timeout)
	fbparse.nav2Profile(opts.fbID)
	# читаем список друзей указанного профиля
	cnt = fbparse.nav2Friends()
	logging.info('Выполнен переход на закладку Друзья: {}'.format(cnt))
	logging.info('Листаем список ...')
	fbparse.scroll2EndPG()
	logging.info('Сохраняем список друзей ...')
	fl = fbparse.save2File(opts.fbID, 'FRCARDS')
	logging.info(fl)
	return

def run02_ParseFileFrCards(opts):
	pc = ParseFrCards(opts.inFL, profile=opts.fbID)
	asyncio.run(pc.prepareCards(3), debug=False)
	return

def run031_CollectPosts(opts):
	fbparse = FBParser(pdriver=opts.webdriver, ptimeout=opts.timeout)
	fbparse.nav2Profile(opts.fbID)
	# читаем ленту постов указанного профиля
	logging.info('Листаем список ...')
	fbparse.scrollLenta(int(opts.posts))
	logging.info('Сохраняем список сообщений в хронике ...')
	fl = fbparse.save2File(opts.fbID, 'LENTA')
	logging.info(fl)
	return

def run032_CollectPosts(opts):
	fbparse = FBParser(pdriver=opts.webdriver, ptimeout=opts.timeout)
	fbparse.nav2Profile(opts.fbID)
	# читаем ленту постов указанного профиля
	logging.info('Листаем список ...')
	fbparse.scrollLenta(int(opts.posts))
	logging.info('Сохраняем список сообщений в хронике ...')
	fl = fbparse.save2File(opts.fbID, 'LENTA')
	logging.info(fl)
	fbparse.saveReactionList()
	logging.info('Завершено сохранение списков реакций на публикации')
	return

def run041_ParsePosts(opts):
	pp = ParseLenta(dirname='', owner=opts.fbID)
	asyncio.run(pp.prepareCards(opts.inFL, 3), debug=False)
	return

def run05_CollectFrRequest(opts):
	fbparse = FBParser(pdriver=opts.webdriver, ptimeout=opts.timeout)
	fbparse.nav2Profile(opts.fbID)
	# читаем список запросов в друзья указанного профиля
	frReqs = fbparse.getFriendReqList()
	lenfr = len(frReqs)
	logging.info(f'Запросов в друзья {lenfr}')
	for fr in frReqs:
		#frparse = FBParser(pdriver=opts.webdriver, ptimeout=opts.timeout)
		fbparse.nav2Profile(fr, fbparse.runUID)
		fl = fbparse.save2File(fr)
		logging.info(f'Лента постов профиля {fr} сохранена в файле {fl}')
	return

def run11_ListCollectFrCards(opts):
	fbparse = FBParser(pdriver=opts.webdriver, ptimeout=opts.timeout)
	with open(opts.inFL, 'r') as infl:
		profiles=[l.strip() for l in infl.readlines()]
	for p in profiles:
		fbparse.nav2Profile(p)
		# читаем список друзей указанного профиля
		cnt = fbparse.nav2Friends()
		logging.info('Выполнен переход на закладку Друзья: {}'.format(cnt))
		logging.info('Листаем список ...')
		fbparse.scroll2EndPG()
		logging.info('Сохраняем список друзей ...')
		fl = fbparse.save2File(p, 'FRCARDS')
		logging.info(fl)
	return

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('--timeout', help='waiting timeout to load the page', default='10')
	parser.add_argument('--webdriver', help='web driver path', default='C:\\bin\\webdriver\\chromedriver')
	parser.add_argument('--fbID', help='facebook ID page', default='-')
	parser.add_argument('--scen', help='choose the user story', default='1')
	parser.add_argument('--inFL', help='the file of facebook ID pages', default='-')
	parser.add_argument('--posts', help='posts count', default='10')
	args = parser.parse_args()
	main(args)

	# python

	# +01 - сбор друзей нулевого участника - сохранить файл друзей
	#  02 - парсинг файла 01, распараллелить парсинг файла 01
	#  !031 - сбор 100 постов нулевого участника + список реакций и отреагирующих - сохранить файлы
	#   032 - сбор 100 постов со списком отреагировавших на пост 
	#  !041 - парсинг постов нулевого участника из файлов 03
	#   042 - парсинг 032

	# +05 - сбор запросов в друзья нулевого участника + в бд сохраняем + сохранить файл постов и списки лайкнувших
	
	# +11 - сбор первого круга друзей - сохраняем файлы список друзей
	#  12 - парсинг файлов 11
	#  13 - сбор постов первого круга друзей - сохраняем файлы
	#  14 - парсинг постов файлов 21



