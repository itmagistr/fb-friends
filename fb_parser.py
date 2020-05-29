# -*- coding: utf-8 -*-
import sys
import time
from pathlib import Path
import datetime
from bs4 import BeautifulSoup as bs
from fb_models import ProfDB, dObj, FLTYPE
import json
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import * #

class FBParser:
	#_profile = dObj() #{'ID':'', 'friends': {}}
	_db = None
	_wh = []
	# создание объекта
	def __init__(self, pdriver, ptimeout, pmaximize=True):
		chrome_options = Options()
		chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222") # запустить предварительно Хром
		self._driver = webdriver.Chrome(pdriver, options=chrome_options)
		time.sleep(3)
		self._driver.set_page_load_timeout(120)
		self._driver.implicitly_wait(ptimeout)
		if pmaximize:
			self._driver.maximize_window()
	# инициализация данных профиля
	def initProfile(self, pID, irunuid=None, flname=None):
		self._profile = dObj()
		self._profile.ID=pID
		self._profile.irunuid = irunuid
		self._profile.friends = dObj()
		self._profile.friends.cntF = -1
		self._profile.friends.cntM = -1
		self._db = ProfDB(ppID=self._profile.ID, puid=irunuid, flname=flname)
		self._profile.irunuid = self._db.curUID

	# переход на страницу профиля
	def nav2Profile(self):
		self._driver.get('https://www.facebook.com/{}'.format(self._profile.ID))
		#self._driver.get('https://m.facebook.com/{}'.format(self._profile.ID))
		time.sleep(3)
		self._driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
		time.sleep(1)
		
		titls=self._driver.find_elements_by_xpath('//h1[@class="_2nlv"]')
		try:
			self._profile.name = titls[0].text
		except :
			self._profile.name = 'имя не найдено'
		# self._driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
		# time.sleep(1)
		frnds=self._driver.find_elements_by_xpath('//div[@class="fsm fwn fcb"]//a[contains(@href,"friends") and @class="_39g5"]')
		logging.info(len(frnds))
		for f in frnds:
			logging.info(f.text)
			if 'общи' in f.text:
				self._profile.friends.cntM = int(onlyDigits(f.text))
			else:
				self._profile.friends.cntF = int(onlyDigits(f.text))
		logging.info(self._profile.toJSON())
		self._db.saveProfile(self._profile)
	
	# переход на страницу друзей
	def nav2Friends(self):
		#TODO требует адаптации к новой структуре бд
		self._driver.execute_script("window.scrollTo(0, 0);")
		links = self._driver.find_elements_by_xpath('//a[@data-tab-key="friends"]')
		try:
			if self._profile.friends.cntF + self._profile.friends.cntM < 0:
				spans = links[0].find_elements_by_xpath('./span[@class="_gs6"]')
				try:
					self._profile.friends.cntF = int(removeSpaces(spans[0].text))
				except:
					logging.info('ошибка чтения кол-ва друзей из закладки Друзья')
			links[0].click()
		except IndexError:
			logging.info('не найдена ссылка перехода на страницу Друзья')
		time.sleep(3)
		return self._profile.friends.cntF
	
	# скролинг страницы друзей
	def scroll2EndPG(self):
		# cкролить список друзей
		if self._profile.friends.cntF > 0:
			cntPGDown = 1 + round(self._profile.friends.cntF/16)
		else:
			cntPGDown = 300
		toDo = True
		alltime = 0
		time_avg = 0
		estim = None
		i = 0
		h_cnt = 3
		while i < cntPGDown and toDo:
		#for i in range(1, cntPGDown):
			i+=1
			started_at = time.monotonic()
			h_old=self._driver.execute_script("return document.body.scrollHeight")
			self._driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

			if time_avg > 0:
				estim = (cntPGDown-i)*time_avg
			logging.info('Листаем список друзей {:03d}/{:03d} ({:05.2f}%), {} сек.'.format(i, cntPGDown, i*100/cntPGDown, estim))
			time.sleep(3)
						
			for elm in self._driver.find_elements_by_xpath("//h3[@class='uiHeaderTitle']"):
				if oneElementInStr(['Больше о вас', 'Дополнительная информация о', ], elm.text):
					logging.info('На странице отображен полный список друзей')
					toDo = False
					break
			
			if toDo and abs(cntPGDown - i)<2:
				cntPGDown += 1
			
			total_slept_for = time.monotonic() - started_at
			alltime+=total_slept_for
			time_avg = round(alltime/i)
			
			h_cur=self._driver.execute_script("return document.body.scrollHeight")
			if toDo and abs(h_cur - h_old) < 5:
				if h_cnt > 0:
					h_cnt-=1
				else:
					toDo = False
					logging.info('Профиль {} не содержит дополнительной информации'.format(self._profile.ID))
			else:
				h_cnt = 3

	# скролинг страницы постов, хронологии публикаций
	def scrollLenta(self, cntPosts=100):
		# cкролить список постов, чтобы было отображено cntPosts вледельца профиля
		cntPGDown = round(cntPosts / 4) + 1
		toDo = True
		alltime = 0
		time_avg = 0
		estim = None
		i = 0
		h_cnt = 3
		while i < cntPGDown and toDo:
			i+=1
			started_at = time.monotonic()
			h_old=self._driver.execute_script("return document.body.scrollHeight")
			self._driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

			if time_avg > 0:
				estim = (cntPGDown-i)*time_avg
			logging.info('Листаем список публикаций {:03d}/{:03d} ({:05.2f}%), {} сек.'.format(i, cntPGDown, i*100/cntPGDown, estim))
			time.sleep(3)
			
			# for elm in self._driver.find_elements_by_xpath("//h3[@class='uiHeaderTitle']"):
			# 	if oneElementInStr(['Больше о вас', 'Дополнительная информация о', ], elm.text):
			# 		logging.info('На странице отображен полный список друзей')
			# 		toDo = False
			# 		break
			
			# if toDo and abs(cntPGDown - i)<2:
			# 	cntPGDown += 1
			
			total_slept_for = time.monotonic() - started_at
			alltime+=total_slept_for
			time_avg = round(alltime/i)
			
			h_cur=self._driver.execute_script("return document.body.scrollHeight")
			if toDo and abs(h_cur - h_old) < 5:
				if h_cnt > 0:
					h_cnt-=1
				else:
					toDo = False
					logging.info('Профиль {} не содержит дополнительной информации'.format(self._profile.ID))
			else:
				h_cnt = 3
		pass
		return	

	# сохранение списка реакций на публикацию
	def saveReactionList(self, inFL=''):
		if len(inFL) > 0:
			# карточки постов в файле
			logging.info(f'Читаем карточки постов из файла {inFL}')
			with open(inFL, 'r', encoding='utf-8') as flh:
				html = bs(flh, 'html.parser')
				posts = html.find_all('div', class_='_5pcb _4b0l _2q8l')
		else:
			# карточки постов в браузере
			posts = self._driver.find_elements_by_xpath('//div[@class="_5pcb _4b0l _2q8l"]')
		
		# соберем список ссылок реакций
		psts = []
		cnt = 0
		for p in posts:
			cnt+=1
			tp = dObj()
			tp.urlReactions = ''

			if len(inFL) > 0:
				tp.postid = p.get('id')

				logging.info(f'{cnt}, postid: {tp.postid}')
				likes = p.select_one('a[href*="/ufi/reaction/profile/browser"]')
				# взять ссылку на список реакций по данному посту
				try:
					tp.urlReactions = likes.get('href')
					logging.info(f'reaction url: {tp.urlReactions}')
				except:
					logging.info(f'??? urlReactions not difined postid: {tp.postid}')
			else:
				tp.postid = p.get_attribute('id')
				logging.info(f'postid: {tp.postid}')
				likes = p.find_elements_by_xpath('.//a[contains(@href,"ufi/reaction/profile/browser")]')
				# взять ссылку на список реакций по данному посту
				try:
					tp.urlReactions = likes[0].get_attribute('href')
					logging.info(f'reaction url: {tp.urlReactions}')
				except:
					logging.info(f'??? urlReactions not difined postid: {tp.postid}')
				
			psts.append(tp)

		# пройдемся по списку ссылок
		lenpsts = len(psts)
		logging.info(f'Запускаем сбор реакций по публикациям {lenpsts}')
		indx=0
		for p in psts:
			indx+1
			logging.info(f'Сбор реакций {indx}/{lenpsts}')
			if len(p.urlReactions) > 0:
				if 'http' not in p.urlReactions:
					self._driver.get(f'https://facebook.com{p.urlReactions}')
				else:
					self._driver.get(p.urlReactions)
				time.sleep(3)
				self.saveReaction2File(postID=p.postid)
			else:
				logging.info(f'Отсутствует реакция на публикациию {p.postid}')
		return

	# сбор и сохранение списка запросов в друзья
	def getFriendReqList(self):
		self._driver.get('https://www.facebook.com/friends/requests/?fcref=jwl')
		time.sleep(3)
		self.save2File('frReq') #??? возможно другой темплейт названия файла требуется назначать во время вызова
		links = self._driver.find_elements_by_xpath('//div[contains(@class,"friendRequestItem")]')
		self._profile.friendReq = [l.get_attribute('data-id') for l in links]
		self._db.saveFriendReq(self._profile.friendReq)
		return self._profile.friendReq
	
	# сохранение открытой страницы в файл html
	def save2File(self, fltmpl, fltype):
		pth = './profiles/{}'.format(self._profile.ID)
		Path(pth).mkdir(parents=True, exist_ok=True)
		flname = '{}/{}_{}_{}.html'.format(pth, FLTYPE[fltype]['litera'], fltmpl, datetime.datetime.now().strftime('%y%m%d_%H%M%S'))
		
		self._db.saveProfFile(flname=flname, fltype=fltype)
		
		with open(flname, 'w', encoding='utf-8') as flres:
			flres.writelines([self._driver.page_source])
		return flname

	# сохранение списка отреагировавших на публикацию в файл
	def saveReaction2File(self, postID):
		pth = './profiles/{}'.format(self._profile.ID)
		Path(pth).mkdir(parents=True, exist_ok=True)
		flname = '{}/{}_{}_{}.html'.format(pth, FLTYPE['REACT']['litera'], 
											self._profile.ID, 
											datetime.datetime.now().strftime('%y%m%d_%H%M%S'))
		
		self._db.saveReactFile(flname=flname, postID=postID)

		with open(flname, 'w', encoding='utf-8') as flres:
			flres.writelines([self._driver.page_source])
		return

	# ??? пока что не задействована
	# --- к удалению
	def parseFriends(self):
		indx = 0
		for fr in self._driver.find_elements_by_xpath('//li[@class="_698"]'):
			indx+=1
			tP = {'name': '', 'cntFriends': None, 'cntFriendsM': None, 'txtFriends': '', 'cnt39g5': 0, 'emptyFP': 0, }
			cntL = 0
			for l in fr.find_elements_by_xpath('.//a'):
				cntL+=1
				if l.get_attribute('class') == '':
					tP['name'] = l.text
					tP['frID'] = getFriendID(l.get_attribute('href'))
				elif l.get_attribute('class') == '_39g5':
					tP['cnt39g5']+=1
					(tP['cntFriends'], tP['cntFriendsM'], tP['txtFriends']) = getNumFriends(l.text)
				
			
			if cntL == 2:
				tP['emptyFP'] = 1
			logging.info('{:04d}; {}; {}'.format(indx, tP['name'], tP['emptyFP']))

			self._db.saveFriend([tP]) #далее передавать несколько для ускорения сохранения
			# exit(1) #!!!
		
	@property
	def runUID(self):
		return self._db.curUID if not self._db is None else None

# вспомогательная функция вычитывания кол-ва друзей из текста
def getNumFriends(pstr):
	resN = 0
	resM = 0
	resT = ''
	try:
		resT = pstr.replace('&nbsp;', ' ').strip()
		
		if 'общи' in resT:
			pos = resT.find(' общи')
			resM = int(removeSpaces(resT[0:pos]))
		elif 'дру' in resT:
			pos = resT.find(' дру')
			resN = int(removeSpaces(resT[0:pos]))
	except:
		logging.info("getNumFriends() Unexpected error: {}".format(sys.exc_info()[0]))
	return (resN, resM, resT)

# вспомогательная функция вычитывания ИД профиля
def getFriendID(linkstr):
	res = ''
	if '?fref=profile' in linkstr:
			pos = linkstr.find('?fref=profile')
			res = linkstr[25:pos]
	elif 'profile.php?id=' in linkstr:
		posEnd = linkstr.find('&fref=profile')
		posStart = linkstr.find('profile.php?id=') + len('profile.php?id=')
		res = linkstr[posStart:posEnd]
	return res

# вспомогательная функция удаления пробелов
def removeSpaces(s):
	return s.replace(' ', '').replace(chr(160), '').strip()

# вспомогательная функция проверки нахождения одной из подстрок в анализируемой строке
def oneElementInStr(elements, pstr):
	res = False
	#if any(b'\r\n' in line for line in lines):
	for el in elements:
		if el in pstr:
			res = True
			break
	return res

# вспомогательная функция вычитывания только цифр из строки
def onlyDigits(pstr):
	return ''.join([ch for ch in pstr if ch.isdigit()])