# -*- coding: utf-8 -*-
import sys
import time
import datetime
from fb_models import FbDB
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import * #

class FBParser:
	_profile = {'ID':'',
				'friends': {}}
	_db = None

	def __init__(self, pdriver, ptimeout, pmaximize=True):
		chrome_options = Options()
		chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222") # запустить предварительно Хром
		self._driver = webdriver.Chrome(pdriver, options=chrome_options)
		time.sleep(3)
		self._driver.set_page_load_timeout(120)
		self._driver.implicitly_wait(ptimeout)
		if pmaximize:
			self._driver.maximize_window()
		

	def nav2Profile(self, pID):
		self._profile["ID"]=pID
		self._driver.get('https://www.facebook.com/{}'.format(self._profile["ID"]))
		time.sleep(3)
		self._db = FbDB(ppID=self._profile["ID"])
	
	def nav2Friends(self):
		links = self._driver.find_elements_by_xpath('//a[@data-tab-key="friends"]')
		self._profile["friends"]["cnt"] = 0
		try:
			spans = links[0].find_elements_by_xpath('./span[@class="_gs6"]')
			self._profile["friends"]["cnt"] = int(removeSpaces(spans[0].text))
			links[0].click()
		except IndexError:
			logging.info('не найдена ссылка перехода на страницу Друзья')
		time.sleep(3)
		self._db.saveFriendCount(self._profile["friends"]["cnt"])
		return self._profile["friends"]["cnt"]
	
	def scroll2EndPG(self):
		cntPGDown = 1 + round(self._profile["friends"]["cnt"]/16.0)
		toDo = True
		alltime = 0
		time_avg = 0
		estim = None
		i = 0
		while i < cntPGDown and toDo:
		#for i in range(1, cntPGDown):
			i+=1
			started_at = time.monotonic()
			self._driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
			if time_avg > 0:
				estim = (cntPGDown-i)*time_avg
			logging.info('Листаем список друзей {:03d}/{:03d} ({:05.2f}%), {} сек.'.format(i, cntPGDown, i*100/cntPGDown, estim))
			time.sleep(3)
			
			for elm in self._driver.find_elements_by_xpath("//h3[@class='uiHeaderTitle']"):
				if elm.text == 'Больше о вас':
					logging.info('На странице отображен полный список друзей')
					toDo = False
					break
			if toDo and abs(cntPGDown - i)<2:
				cntPGDown += 1
			
			total_slept_for = time.monotonic() - started_at
			alltime+=total_slept_for
			time_avg = round(alltime/i)
		

	
	def save2File(self):
		flname = 'x_fbfriends_{}.html'.format(datetime.datetime.now().strftime('%y%m%d_%H%M'))
		with open(flname, 'w', encoding='utf-8') as flres:
			flres.writelines([self._driver.page_source])
		return flname

	def parseFriends(self):
		self._profile["friends"]["lst"] = []
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


def removeSpaces(s):
	return s.replace(' ', '').replace(chr(160), '').strip()

#https://www.facebook.com/friends/requests/?fcref=jwl
#$x('//div[contains(@class,"friendRequestItem")]/@data-id')[0].value
#<div class="clearfix ruUserBox _3-z friendRequestItem" data-id="100003286515758" data-ft="{&quot;tn&quot;:&quot;-Z&quot;}" id="u_fetchstream_3_d"><a href="https://www.facebook.com/profile.php?id=100003286515758&amp;fref=%2Freqs.php" class="_8o _8t lfloat _ohe" tabindex="-1" aria-hidden="true"><div class="uiScaledImageContainer ruProfilePicXLarge"><img class="scaledImageFitWidth img" src="https://scontent-hel2-1.xx.fbcdn.net/v/t1.0-1/cp0/c3.5.75.75a/p80x80/74465175_2502816499837876_4791922280894562304_o.jpg?_nc_cat=105&amp;_nc_sid=dbb9e7&amp;_nc_ohc=5w77TOlHoLMAX992JZd&amp;_nc_ht=scontent-hel2-1.xx&amp;oh=e57589a65ff3cb3c282ef484663fc22d&amp;oe=5EEDC515" data-src="https://scontent-hel2-1.xx.fbcdn.net/v/t1.0-1/cp0/c3.5.75.75a/p80x80/74465175_2502816499837876_4791922280894562304_o.jpg?_nc_cat=105&amp;_nc_sid=dbb9e7&amp;_nc_ohc=5w77TOlHoLMAX992JZd&amp;_nc_ht=scontent-hel2-1.xx&amp;oh=e57589a65ff3cb3c282ef484663fc22d&amp;oe=5EEDC515" alt="" width="75" height="75" data-ft="{&quot;tn&quot;:&quot;-^&quot;}" itemprop="image"></div></a><div class="_42ef"><div class="_3qn7 _61-0 _2fyi _3qng"><div><div class="friendBrowserContent"><div class="fcg"><div class="_6-_"><a title="Ирина Богомолова" href="https://www.facebook.com/profile.php?id=100003286515758&amp;fref=%2Freqs.php&amp;__tn__=%2Cd-Z-R&amp;eid=ARBI9vEydV4QdyR4BRSKFwLVOl_nhAwE78h1UiEDMsd_NUtKSgHLHc1xElXNqIot-M5EqqRTn8GXNNo8" data-hovercard="/ajax/hovercard/user.php?id=100003286515758&amp;extragetparams=%7B%22__tn__%22%3A%22%2Cd-Z-R%22%2C%22eid%22%3A%22ARBI9vEydV4QdyR4BRSKFwLVOl_nhAwE78h1UiEDMsd_NUtKSgHLHc1xElXNqIot-M5EqqRTn8GXNNo8%22%7D" data-hovercard-prefer-more-content-show="1">Ирина Богомолова</a></div><div class="hidden_elem followUpQuestion _1byw fcg" id="u_fetchstream_3_k"><div class="clearfix _5hb1 _2dzh"><a role="button" class="_42ft _4jy0 _5hb3 rfloat _ohf _4jy3 _517h _51sy mls" href="#" data-hover="tooltip" data-tooltip-content="Если вы нажмете &quot;Отметить как спам&quot;, этот пользователь не сможет отправлять вам запросы на добавление в друзья.">Пометить как спам</a><div class="_2dze _1byw">Запрос удален.</div></div><img class="_9- hidden_elem img" src="https://static.xx.fbcdn.net/rsrc.php/v3/yk/r/LOOn0JtHNzb.gif" alt="" width="16" height="16"><div class="clearfix _5hb2 hidden_elem _2dzh"><a role="button" class="_42ft _4jy0 _2qk_ rfloat _ohf _4jy3 _517h _51sy mls" href="#">Отменить</a><div class="_2dze _1byw">Вы не будете получать новые запросы на добавление в друзья от этого человека.</div></div><div class="mrs _a2 hidden_elem _2dze _1byw">Вы снова сможете получать запросы на добавление в друзья  от этого человека.</div><div class="_9z hidden_elem _2dze _1byw">Произошла ошибка при изменении этого запроса на добавление в друзья. Попробуйте еще раз позже.</div></div><div class="requestInfoContainer"><div><ul class="uiList _7ebh _4kg"><li><table class="uiGrid _51mz" cellspacing="0" cellpadding="0" role="presentation"><tbody><tr class="_51mx"><td class="_51m- vTop hLeft prs"><div class="_43qm _7ebk _4usz"><ul class="uiList _4cg3 _509- _4ki" style="display:inline-block"><li class="_43q7"><a href="https://www.facebook.com/elina.braginskaya" class="link" data-jsid="anchor" data-hover="tooltip" data-tooltip-content="Элина Брагинская"><img class="_s0 _3qxe img" src="https://scontent-hel2-1.xx.fbcdn.net/v/t31.0-1/cp0/p50x50/14047292_1050461645038755_4344423548548203139_o.jpg?_nc_cat=111&amp;_nc_sid=dbb9e7&amp;_nc_ohc=s-Ei2ZwRjrcAX9ptDnQ&amp;_nc_ht=scontent-hel2-1.xx&amp;oh=8d727f0a36851cf36221f14059cca83e&amp;oe=5EEF0339" alt="Элина Брагинская" data-jsid="img"></a></li></ul></div></td><td class="_51m- vTop hLeft _51mw"><span class="_7ebi"><a class="_7ebj" title="Элина Брагинская" href="https://www.facebook.com/elina.braginskaya?__tn__=%2Cd-Z-R&amp;eid=ARC_PxdgTMXLXpMMDA3e5rq9ab8TVEkPfa_Kwh1Uam8Dgmtj-wNvXtsWy6g1mv1y0mcOUmRN2sTA3BkZ" data-hovercard="/ajax/hovercard/user.php?id=100002247898334&amp;extragetparams=%7B%22__tn__%22%3A%22%2Cd-Z-R%22%2C%22eid%22%3A%22ARC_PxdgTMXLXpMMDA3e5rq9ab8TVEkPfa_Kwh1Uam8Dgmtj-wNvXtsWy6g1mv1y0mcOUmRN2sTA3BkZ%22%7D" data-hovercard-prefer-more-content-show="1">Элина Брагинская</a> и <a ajaxify="/ajax/browser/dialog/mutual_friends/?uid=100003286515758" href="/browse/mutual_friends/?uid=100003286515758" rel="dialog" role="button" data-hover="tooltip" data-tooltip-uri="/ajax/mutual_friends/tooltip.php?friend_id=100003286515758&amp;exclude_id=100002247898334">еще 1 общий друг</a></span></td></tr></tbody></table></li></ul></div><div></div></div></div></div></div><div class="_7x0o ruResponse ruResponseSectionContainer"><div class="ruResponseButtons"><div class="_3qn7 _61-0 _2fyi _3qnf"><button value="1" class="_42ft _4jy0 _4jy3 _4jy1 selected _51sy" aria-label="Подтвердить запрос на добавление в друзья от Ирины Богомоловой" type="submit" id="u_fetchstream_3_l">Подтвердить</button><button value="1" class="_42ft _4jy0 _4jy3 _517h _51sy" aria-label="Удалить запрос на добавление в друзья от Ирины Богомоловой" type="submit" id="u_fetchstream_3_m">Удалить запрос</button></div></div><img class="ruResponseLoading hidden_elem img" src="https://static.xx.fbcdn.net/rsrc.php/v3/yk/r/LOOn0JtHNzb.gif" alt="" aria-busy="true" aria-valuemin="0" aria-valuemax="100" aria-valuetext="Загрузка" role="progressbar" tabindex="-1" width="16" height="16"><span class="ruTransportErrorMsg hidden_elem">Ошибка соединения. Пожалуйста, проверьте ваше подключение к Интернету.</span></div></div></div></div>