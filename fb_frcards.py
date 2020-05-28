# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup as bs
import asyncio
from fb_models import *
from fb_parser import getFriendID, getNumFriends
import logging
import os

class ParseFrCards:
	def __init__(self, flname, profile):
		self.flName = flname
		#self.irun = 0 # вычислить на следующем шаге
		#self.profile = profile
		

	async def prepareCards(self, threads=50):
		
		tasks=[]
		q = asyncio.Queue()
		cnt = 0
		# проход по файлу
		if len(self.flName) > 0 :
			# обработать файл
			with open(self.flName, 'r', encoding='utf-8') as flh:
				html = bs(flh, 'html.parser')
				for el in html.find_all('li', class_="_698"):
					# карточки в очередь сообщений
					#q.put_nowait(str(el))
					cnt+=1
		logging.info('карточек в очереди на обработку: {}'.format(cnt))

		# стартуем задачи в заданном кол-ве
		for n in range(threads):
			task = asyncio.create_task(self.parseCard(f'work-{n}, ', q))
			tasks.append(task)
		logging.info('Ожидаем выполнения обработки карточек в {} потоках...'.format(len(tasks)))
		await asyncio.gather(*tasks, return_exceptions=False)
		logging.info('Обработка карточек завершена')

	async def parseCard(self, name, msgq):
		htmlstr = 'run first time'
		print(name, self.irun, self.profile)
		await asyncio.sleep(1)
		return 0
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
						tP['name'] = t.string
						tP['frID'] = getFriendID(t.get('href'))
					elif '_39g5' in t.get('class'):
						tP['cnt39g5']+=1
						(tP['cntFriends'], tP['cntFriendsM'], tP['txtFriends']) = getNumFriends(t.string)
				#print(f'cntL={cntL}')
				if cntL == 2:
					tP['emptyFP'] = 1
				#logging.info('{}, {}; {}; {}'.format(p, name, tP['name'], tP['emptyFP']))
				
				#сообщить, что сообщение обработано
				msgq.task_done()
			
