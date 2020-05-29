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
logging.getLogger().addHandler(logging.FileHandler("fb_friends.log", encoding="utf-8"))

def main(opts):
	started_at = time.monotonic()
	if opts.scen=='01':
		run01_CollectFrCards(opts)
		proctime = time.monotonic() - started_at
		logging.info(f'Выполнение сценария {opts.scen} завершено за {proctime:.3f} сек.')
		return 1
	elif opts.scen=='02':
		run02_ParseFileFrCards(opts)
		proctime = time.monotonic() - started_at
		logging.info(f'Выполнение сценария {opts.scen} завершено за {proctime:.3f} сек.')
		return 2
	elif opts.scen=='031':
		run031_CollectPosts(opts)
		proctime = time.monotonic() - started_at
		logging.info(f'Выполнение сценария {opts.scen} завершено за {proctime:.3f} сек.')
		return 31
	elif opts.scen=='032':
		run032_CollectPosts(opts)
		proctime = time.monotonic() - started_at
		logging.info(f'Выполнение сценария {opts.scen} завершено за {proctime:.3f} сек.')
		return 31
	elif opts.scen=='041':
		run041_ParsePosts(opts)
		proctime = time.monotonic() - started_at
		logging.info(f'Выполнение сценария {opts.scen} завершено за {proctime:.3f} сек.')
		return 41
	elif opts.scen=='042':
		run042_ParsePosts(opts)
		proctime = time.monotonic() - started_at
		logging.info(f'Выполнение сценария {opts.scen} завершено за {proctime:.3f} сек.')
		return 42
	elif opts.scen == '05':
		run05_CollectFrRequest(opts)
		proctime = time.monotonic() - started_at
		logging.info(f'Выполнение сценария {opts.scen} завершено за {proctime:.3f} сек.')
		return 5
	elif opts.scen == '11':
		run11_ListCollectFrCards(opts)
		proctime = time.monotonic() - started_at
		logging.info(f'Выполнение сценария {opts.scen} завершено за {proctime:.3f} сек.')
		return 11
	elif opts.scen == '12':
		run12_ListParseFrCards(opts)
		proctime = time.monotonic() - started_at
		logging.info(f'Выполнение сценария {opts.scen} завершено за {proctime:.3f} сек.')
		return 12
	else:
		logging.info(f'сценарий {opts.scen} не доступен к запуску')
		return -1
	logging.info('Работа скрипта завершена.')
	return 0

def run01_CollectFrCards(opts):
	fbparse = FBParser(pdriver=opts.webdriver, ptimeout=opts.timeout)
	fbparse.initProfile(opts.fbID)
	fbparse.nav2Profile()
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
	pc = ParseFrCards(files=[opts.inFL])
	asyncio.run(pc.prepareFiles(threads=int(opts.threads)), debug=False)
	return

def run031_CollectPosts(opts):
	fbparse = FBParser(pdriver=opts.webdriver, ptimeout=opts.timeout)
	fbparse.initProfile(opts.fbID)
	fbparse.nav2Profile()
	# читаем ленту постов указанного профиля
	logging.info('Листаем список ...')
	fbparse.scrollLenta(int(opts.posts))
	logging.info('Сохраняем список сообщений в хронике ...')
	fl = fbparse.save2File(opts.fbID, 'LENTA')
	logging.info(fl)
	return

def run032_CollectPosts(opts):
	fbparse = FBParser(pdriver=opts.webdriver, ptimeout=opts.timeout)
	fbparse.initProfile(opts.fbID, flname=opts.inFL)
	if len(opts.inFL) > 1 :
		# список карточек постов из файла
		fbparse.saveReactionList(opts.inFL)
	else:
		fbparse.nav2Profile()
		# читаем ленту постов указанного профиля
		logging.info('Листаем список ...')
		fbparse.scrollLenta(int(opts.posts))
		logging.info('Сохраняем список сообщений в хронике ...')
		fl = fbparse.save2File(opts.fbID, 'LENTA')
		logging.info(fl)
		# список карточек постов из браузера после листания ленты
		fbparse.saveReactionList()
	logging.info('Завершено сохранение списков реакций на публикации')
	return

def run041_ParsePosts(opts):
	pp = ParseLenta(dirname='', owner=opts.fbID)
	asyncio.run(pp.prepareCards(opts.inFL, threads=int(opts.threads)), debug=False)
	return

def run042_ParsePosts(opts):
	pp = ParseLenta(dirname='', owner=opts.fbID)
	asyncio.run(pp.prepareCards(opts.inFL, threads=int(opts.threads)), debug=False)

	return

def run05_CollectFrRequest(opts):
	fbparse = FBParser(pdriver=opts.webdriver, ptimeout=opts.timeout)
	fbparse.initProfile(opts.fbID)
	fbparse.nav2Profile()
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
	# во входном файле список профайлов по которым сохранить список друзей
	with open(opts.inFL, 'r') as infl:
		profiles=[l.strip() for l in infl.readlines()]
	curIRun = None
	for p in profiles:
		fbparse.initProfile(pID=p, irunuid=curIRun)
		curIRun=fbparse.runUID
		fbparse.nav2Profile()
		# читаем список друзей указанного профиля
		cnt = fbparse.nav2Friends()
		logging.info('Выполнен переход на закладку Друзья: {}'.format(cnt))
		logging.info('Листаем список ...')
		fbparse.scroll2EndPG()
		logging.info('Сохраняем список друзей ...')
		fl = fbparse.save2File(p, 'FRCARDS')
		logging.info(fl)
	return

def run12_ListParseFrCards(opts):
	with open(opts.inFL, 'r') as fl:
		ffiles = fl.readlines()
	pc = ParseFrCards(files=ffiles)
	asyncio.run(pc.prepareFiles(threads=int(opts.threads)), debug=False)
	return

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('--timeout', help='waiting timeout to load the page', default='10')
	parser.add_argument('--webdriver', help='web driver path', default='C:\\bin\\webdriver\\chromedriver')
	parser.add_argument('--fbID', help='facebook ID page', default='-')
	parser.add_argument('--scen', help='choose the user story', default='1')
	parser.add_argument('--inFL', help='the file of facebook ID pages', default='-')
	parser.add_argument('--posts', help='posts count', default='10')
	parser.add_argument('--threads', help='threads count', default='10')
	parser.add_argument('--irun', help='irun UID', default='-')
	
	args = parser.parse_args()
	main(args)

	# python

	# +01 - сбор друзей нулевого участника - сохранить файл друзей
	# ?02 - парсинг файла 01, распараллелить парсинг файла 01
	# +031 - сбор 100 постов нулевого участника + список реакций и отреагирующих - сохранить файлы
	# +032 - сбор 100 постов со списком отреагировавших на пост (использовать на вход файл с постами и пропустить шаг листания ленты)
	# +041 - парсинг постов нулевого участника из файлов 03
	# +042 - парсинг 032

	# +05 - сбор запросов в друзья нулевого участника + в бд сохраняем + сохранить файл постов и списки лайкнувших
	
	# +11 - сбор первого круга друзей - сохраняем файлы список друзей
	#  12 - парсинг файлов 11
	#  131 - сбор постов первого круга друзей - сохраняем файлы
	#  132 -
	#  141 - парсинг постов файлов 21
	#  142 -

#_1 определять страницу блокировки, выйти с ошибкой
#_2 s12 распарсить и узнать какие друзья уникальные в круге
#_3 сводная таблица кто кому друг
#_4 сводная таблица друг к посту (по интегральной оценке от 10 до 01)


