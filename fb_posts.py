# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup as bs
import asyncio
from fb_models import *
import logging
import os
import time

class ParseLenta:
	def __init__(self, files, irunuid=None):
		#!!!!self.owner = owner
		self.files = files # файл со списком файлов, которые требуется распарсить
		self.irun = irunuid # вычислить на следующем шаге
		pass
	
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

				logging.info('Размещаем карточки постов в очередь на обработку')
				# обработать файл
				started_at = time.monotonic()
				with open(flstr, 'r', encoding='utf-8') as flh:
					html = bs(flh, 'html.parser')
					for el in html.find_all('div', class_='_5pcb _4b0l _2q8l'):
						# карточки в очередь сообщений
						#logging.info('-----------------------------')
						#logging.info(str(el))
						q.put_nowait(str(el))
						cnt+=1
				total_slept_for = time.monotonic() - started_at
				logging.info('за {:.3f} сек. размещено {} карточек в очередь на обработку'.format(total_slept_for, cnt))

				# стартуем задачи в заданном кол-ве
				for n in range(threads):
					task = asyncio.create_task(self.parseCard(f'work-{n}, ', q, curDB))
					tasks.append(task)
				logging.info('Ожидаем выполнения обработки карточек в {} потоках...'.format(len(tasks)))
				started_at = time.monotonic()
				await asyncio.gather(*tasks, return_exceptions=False)
				total_slept_for = time.monotonic() - started_at
				logging.info(f'Обработка карточек {cnt} в {threads} потоков завершена за {total_slept_for:.3f} сек.')
	
	async def parseCard(self, name, msgq, cdb):
		htmlstr = 'run first time'
		#cdb = ProfDB(ppID=self.owner, flname=self.flname)

		while len(htmlstr) > 0:
			await asyncio.sleep(0.1)
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
				
				#t = html.find('h5', class_='_7tae _14f3 _14f5 _5pbw _5vra') 
				#_7tae mbs _4bxd _5pbw _5vra
				t = html.select_one('h5[class*="_7tae"]')
				pl = t.find('a', class_='profileLink') if t is not None else None
				if not pl is None:
					card.title = pl.get('title')  
				else:
					card.title = t.span.span.a.string if not t is None else '-'

				t = html.find('div', class_='_5pbx userContent _3576')
				card.content = t.p.string if not t is None else '-'
				t = html.find('a', class_='_3hg- _42ft')
				card.comments = int(t.string.replace('Комментарии: ','').strip()) if not t is None else 0
				t = html.find('a', class_='_3rwx _42ft', rel='dialog')
				card.reposts = int(t.string.replace('Поделились: ','').strip()) if not t is None else 0
				
				for t in html.find_all('a', role='button', ):
					tstr = t.get('aria-label')
					if tstr is not None and ':' in tstr:
						card.actions.append(tstr)
				card.likes = agregateActions(card.actions)
				logging.info(card.toJSON())
				
				card.rlist = [] #для проверки в последующих функциях
				if len(card.id) > 0:
					rfl = await cdb.getReactionFile(postID=card.id)
					if os.path.exists(rfl): 
						logging.info(f'файл реакций: {rfl}')
						with open(rfl, 'r', encoding='utf-8') as flh:
							html = bs(flh, 'html.parser')
							for el in html.find_all('li', class_=False):
								for el2 in el.find_all('li', class_='_5i_q'):
									robj = dObj()
									#t = el2.find('div', class_='_5j0e fsl fwb fcb')
									t = el2.select_one('div[class*="_5j0e"]') #_5j0e fsl fwb fcb _5wj-
									robj.name = ''
									try:
										robj.name = t.a.string #el2.div.a.get('title') 
									except:
										logging.info(f'!!! ошибка определения имени отреагировавшего, файл {rfl}')
									robj.subtype = el.div.string
									robj.rtype = 'LIKES'
									#logging.info('reaction obj: {}'.format(robj.toJSON()))
									card.rlist.append(robj)
				#if card.title == self.owner:
				await cdb.save2ProfPost(card)
				#сообщить, что сообщение обработано
				msgq.task_done()

	
			
def getPubDT(dtstr):
	res = ''
	j=json.loads(dtstr)
	if 'timestamp' in j.keys():
		res = datetime.datetime.fromtimestamp(j['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
	return res

def agregateActions(acts):
	res = 0
	for a in acts:
		try:
			tmp = a.split(':')[-1].strip()
			res+= int(tmp)
		except:
			continue
	return res
