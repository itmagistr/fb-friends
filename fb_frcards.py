# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup as bs
import asyncio
from fb_models import *
from fb_parser import getFriendID, getNumFriends
import logging
import os

class ParseFrCards:
	def __init__(self, files, irunuid=None):
		self.files = files # файл со списком файлов, которые требуется распарсить
		self.irun = irunuid # вычислить на следующем шаге
		#self.profile = profile # профиль к которому привязать друзей
	# Запускаем обработку файлов в потоках
	async def prepareFiles(self, threads=20):
		lenfiles = len(self.files)
		logging.info('файлов на обработку: {}'.format(lenfiles))
		tasks=[]
		fq = asyncio.Queue()
		for f in self.files:
			fq.put_nowait(f.strip())
		# стартуем задачи в заданном кол-ве
		threads = threads if lenfiles > threads else lenfiles
		for n in range(threads):
			task = asyncio.create_task(self.prepareCards(f'procfile-{n}, ', fq))
			tasks.append(task)
		logging.info('Ожидаем выполнения обработки файлов в {} потоках...'.format(len(tasks)))
		await asyncio.gather(*tasks, return_exceptions=False)
		logging.info('Обработка файлов завершена')

	# читаем содержимое файла и запускаем парсинг одного файла так же в потоках
	async def prepareCards(self, workname, flq, threads=10):
		flstr = 'run first time'
		oldfl = flstr
		#print(name, self.irun, self.profile)
		while len(flstr) > 0:
			await asyncio.sleep(0.1)
			try:
				flstr = flq.get_nowait()
			except asyncio.QueueEmpty:
				flstr = ''
			if len(flstr) > 0 :
				# обработка очередного файла
				tasks=[]
				q = asyncio.Queue()
				cnt = 0
				
				# по файлу получить профиль 
				if oldfl == flstr:
					pass
				else:
					curDB = ProfDB('UNKNOWN', flname=flstr)
					oldfl = flstr
				
				profID = curDB.curProfID if curDB is not None else 'UNKNOWN' # itmagistr

				# обработать файл
				with open(flstr, 'r', encoding='utf-8') as flh:
					html = bs(flh, 'html.parser')
					for el in html.find_all('li', class_="_698"):
						# карточки в очередь сообщений
						q.put_nowait(str(el))
						cnt+=1
				logging.info('карточек в очереди на обработку: {}'.format(cnt))

				# стартуем задачи в заданном кол-ве
				for n in range(threads):
					task = asyncio.create_task(self.parseCard(f'proccard-{n}, ', q, curDB))
					tasks.append(task)
				logging.info('Ожидаем выполнения обработки карточек в {} потоках...'.format(len(tasks)))
				await asyncio.gather(*tasks, return_exceptions=False)
				logging.info('Обработка карточек завершена')
				# отметить сообщение обработанным
				flq.task_done()

	# парсим одну карточку
	async def parseCard(self, workname, msgq, cdb):
		htmlstr = 'run first time'
		while len(htmlstr) > 0:
			await asyncio.sleep(0.1)
			try:
				htmlstr = msgq.get_nowait()
			except asyncio.QueueEmpty:
				htmlstr = ''
			if len(htmlstr) > 0 :
				# обработать карточку
				suop = bs(htmlstr, 'html.parser') 

				tP = {'name': '', 'cntFriends': None, 'cntFriendsM': None, 'txtFriends': '', 'cnt39g5': 0, 'emptyFP': 0, }
				#print(tP)
				cntL = 0
				for t in suop.find_all('a'):
					cntL+=1
					if not t.has_attr('class'):
						tP['name'] = t.text
						tP['frID'] = getFriendID(t.get('href'))
					elif '_39g5' in t.get('class'):
						tP['cnt39g5']+=1
						(tP['cntFriends'], tP['cntFriendsM'], tP['txtFriends']) = getNumFriends(t.string)
				#print(f'cntL={cntL}')
				if cntL == 2:
					tP['emptyFP'] = 1
				#logging.info('{}, {}; {}; {}'.format(p, name, tP['name'], tP['emptyFP']))
				await cdb.saveFriend([tP])
				#сообщить, что сообщение обработано
				msgq.task_done()
			
