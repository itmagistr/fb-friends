# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup as bs
import asyncio
from fb_models import *
import logging
import os
import time

class ParseLenta:
	def __init__(self, dirname, owner):
		self.profDir = dirname
		self.owner = owner
		pass
		
	async def prepareCards(self, flname, threds=50):
		self.flname = flname
		tasks=[]
		q = asyncio.Queue()
		cnt = 0
		# проход по файлу
		if len(flname) > 0 :
			# обработать файл
			with open(flname, 'r', encoding='utf-8') as flh:
				html = bs(flh, 'html.parser')
				for el in html.find_all('div', class_='_5pcb _4b0l _2q8l'):
					# карточки в очередь сообщений
					#logging.info('-----------------------------')
					#logging.info(str(el))
					q.put_nowait(str(el))
					cnt+=1
		logging.info('карточек в очереди на обработку: {}'.format(cnt))

		# стартуем задачи в заданном кол-ве
		for n in range(threds):
			task = asyncio.create_task(self.parseCard(f'work-{n}, ', q))
			tasks.append(task)
		logging.info('Ожидаем выполнения обработки карточек в {} потоках...'.format(len(tasks)))
		await asyncio.gather(*tasks, return_exceptions=False)
		logging.info('Обработка карточек завершена')
	
	async def parseCard(self, name, msgq):
		htmlstr = 'run first time'
		cdb = ProfDB(ppID=self.owner, flname=self.flname)

		while len(htmlstr) > 0:
			await asyncio.sleep(0.5)
			try:
				htmlstr = msgq.get_nowait()
			except asyncio.QueueEmpty:
				htmlstr = ''
			if len(htmlstr) > 0 :
				html = bs(htmlstr, 'html.parser')
				card = dObj()
				# обработать карточку
				
				# дата и время публикации
				card.pubdt = getPubDT(html.div.get('data-store'))
				card.veid = html.div.get('data-veid')
				card.id = html.div.get('id')
				card.actions = []
				t = html.find('a', class_='profileLink')
				if not t is None:
					card.title = t.get('title')  
				else:
					t = html.find('h5', class_='_7tae _14f3 _14f5 _5pbw _5vra')
					card.title = t.span.span.a['title'] if not t is None else '-'

				t = html.find('div', class_='_5pbx userContent _3576')
				card.content = t.p.string if not t is None else '-'
				t = html.find('a', class_='_3hg- _42ft')
				card.comments = t.string if not t is None else '-'
				t = html.find('a', class_='_3rwx _42ft', rel='dialog')
				card.reposts = t.string if not t is None else '-'
				
				for t in html.find_all('a', role='button', ):
					card.actions.append(t.get('aria-label'))
				logging.info(card.toJSON())
				#if card.title == self.owner:
				await cdb.save2ProfPost(card)

				#сообщить, что сообщение обработано
				msgq.task_done()

	async def parseFiles(self):
		tasks=[]
		q = asyncio.Queue()

		# проход по папке с файлами
		for root, dirs, files in os.walk(self.profDir):
			for x in files:
				curFl = os.path.join(root, x)
				# путь к файлу строкой в очередь сообщений для обработки
				q.put_nowait(curFl)
			
		for n in range(50):
			task = asyncio.create_task(self.parseFile(f'work-{n}, ', q))
			tasks.append(task)
		logging.info('Ожидаем выполнения обработки файлов в {} потоках...'.format(len(tasks)))
		await asyncio.gather(*tasks, return_exceptions=False)
		logging.info('Обработка файлов завершена')

	async def parseFile(self, name, msgq):
		cfl = 'run first time'
		while len(cfl) > 0:
			await asyncio.sleep(0.5)
			try:
				cfl = msgq.get_nowait()
			except asyncio.QueueEmpty:
				cfl = ''
			if len(cfl) > 0 :
				# обработать файл
				with open(cfl, 'r', encoding='utf-8') as flh:
					html = bs(flh, 'html.parser')
					
				print(name, cfl)
				#сообщить, что сообщение обработано
				msgq.task_done()
			
def getPubDT(dtstr):
	res = ''
	j=json.loads(dtstr)
	if 'timestamp' in j.keys():
		res = datetime.datetime.utcfromtimestamp(j['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
	return res


