# -*- coding: utf-8 -*-
import json
from pony import orm
import pony.orm.dbproviders.sqlite
import datetime
import uuid
import logging

#orm.set_sql_debug(True)

db = orm.Database()


@db.on_connect(provider='sqlite')
def sqlite_case_sensitivity(db, connection):
    cursor = connection.cursor()
    cursor.execute('PRAGMA case_sensitive_like = OFF')

db.bind(provider='sqlite', filename='fbdb.sqlite', create_db=True)


class dObj:
	def toJSON(self):
		return json.dumps(self, default=lambda o: o.__dict__, 
			sort_keys=True, indent=4, ensure_ascii=False)

class IRun(db.Entity):
	dt = orm.Required(datetime.datetime) #default=datetime.datetime.now()
	uid = orm.Required(str) #, default=uuid.uuid4()
	profiles = orm.Set('Profile', cascade_delete=True, reverse='irun')

class Profile(db.Entity):
	irun = orm.Required(IRun, reverse='profiles')
	profID = orm.Required(str) #fb profile ID
	jdata = orm.Optional(orm.Json)
	name = orm.Optional(str)
	cntF = orm.Optional(int)
	cntM = orm.Optional(int)
	profOne = orm.Set('ProfRel', cascade_delete=True, reverse='prof1')
	profTwo = orm.Set('ProfRel', cascade_delete=True, reverse='prof2')
	posts = orm.Set('ProfPost', cascade_delete=True, reverse='prof')
	files = orm.Set('ProfFile', cascade_delete=True, reverse='prof')

class ProfRel(db.Entity):
	prof1 = orm.Required(Profile, reverse='profOne')
	prof2 = orm.Required(Profile, reverse='profTwo')
	ptype = orm.Required(str) # тип связи

class ProfPost(db.Entity):
	prof = orm.Required(Profile, reverse='posts')
	pubProf = orm.Optional(str)
	pubdt = orm.Optional(str)
	title = orm.Optional(str)
	txt = orm.Optional(str)
	cntL = orm.Optional(int)
	cntC = orm.Optional(int)
	cntR = orm.Optional(int)
	jdata = orm.Optional(orm.Json)

class ProfFile(db.Entity):
	prof = orm.Required(Profile, reverse='files') 
	flname = orm.Required(str)
	fltype = orm.Required(str)


PTYPE = {'FRIEND_REQ': 'Запрос в друзья', }
FLTYPE = {'FRCARDS': {'title': 'Карточки друзей',
					  'litera': 'f', }, 
		  'LENTA': {'title': 'Посты, лента постов',
					'litera': 'p', }
		 }

db.generate_mapping(create_tables=True)

class ProfDB:
	rID = 0 #runID
	uid = ''
	pID = 0
	def __init__(self, ppID, puid=None, flname=None):
		# pID - user profile ID in FB
		# uid - UUID to run one time
		ir = None

		with orm.db_session():
			
			if not flname is None:
				pf = ProfFile.get(flname=flname)
				if not pf is None:
					puid = pf.prof.irun.uid

			if not puid is None:
				# получить текущий идентификатор запуска
				ir = IRun.get(uid=puid)

			if ir is None:
				# получить новый  ид запуска
				ir = IRun(dt=datetime.datetime.now(), uid=str(uuid.uuid4()))
				p = Profile(irun=ir, profID=ppID)
			else:
				p = Profile.get(irun=ir, profID=ppID)
				if p is None:
					p = Profile(irun=ir, profID=ppID)
			orm.commit()
			self.rID = ir.id
			self.uid = ir.uid
			self.pID = p.id
			logging.info('{}, {}, {}'.format(self.rID, self.uid, self.pID))
	
	def saveFriend(self, jdata):
		with orm.db_session():
			p = Profile.get(id=self.pID)
			for j in jdata:
				pr = Profile(irun=self.rID, profID=j["frID"] if len(j['frID']) > 0 else 'not Active' , cntF=j['cntFriends'], cntM=j['cntFriendsM'], jdata=j, name=j['name'])
				fr = ProfRel(prof1=p, prof2=pr, ptype='FRIEND')
				#sf = Friend(irun=ir, data=j, name=j['name'], cntF=j['cntFriends'], cntM=j['cntFriendsM'], cntT=j['txtFriends'], frID=j['frID'])
			orm.flush()

	def saveProfile(self, profobj):
		with orm.db_session():
			#logging.info(self.pID)
			p = Profile.get(id=self.pID)
			p.name = profobj.name
			p.cntF = profobj.friends.cntF
			p.cntM = profobj.friends.cntM
			p.jdata = json.loads(profobj.toJSON())
			orm.flush()
	
	def saveProfFile(self, flname, fltype):
		with orm.db_session():
			pf = ProfFile(prof=self.pID, flname=flname, fltype=fltype)
			orm.flush()

	async def save2ProfPost(self, crd):
		with orm.db_session():
			pst = ProfPost(prof=self.pID, 
						   pubProf=crd.title if crd.title is not None else '-',
						   pubdt=crd.pubdt if crd.pubdt is not None else '-',
						   txt=crd.content if crd.content is not None else '-',
						   jdata=json.loads(crd.toJSON()))
		


	def saveFriendReq(self, frRequests):
		with orm.db_session():
			p = Profile.get(id=self.pID)
			for r in frRequests:
				pr = Profile(irun=self.rID, profID=r)
				fr = ProfRel(prof1=p, prof2=pr, ptype='FRIEND_REQ')
	@property
	def curUID(self):
		return self.uid
	@property
	def curID(self):
		return self.rID

	