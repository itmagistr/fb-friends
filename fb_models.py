# -*- coding: utf-8 -*-
from pony import orm
import pony.orm.dbproviders.sqlite
import datetime
import uuid
#orm.set_sql_debug(True)

db = orm.Database()


@db.on_connect(provider='sqlite')
def sqlite_case_sensitivity(db, connection):
    cursor = connection.cursor()
    cursor.execute('PRAGMA case_sensitive_like = OFF')

db.bind(provider='sqlite', filename='fbdb.sqlite', create_db=True)


class IRun(db.Entity):
	dt = orm.Required(datetime.datetime) #default=datetime.datetime.now()
	uid = orm.Required(str) #, default=uuid.uuid4()
	pID = orm.Required(str) # profile ID
	cntF = orm.Optional(int)
	friends = orm.Set('Friend', cascade_delete=True, reverse='irun')

class Friend(db.Entity):
	irun = orm.Required(IRun, reverse='friends')
	data = orm.Required(orm.Json)
	name = orm.Required(str)
	cntF = orm.Optional(int)
	cntM = orm.Optional(int)
	cntT = orm.Optional(str)
	frID = orm.Optional(str) #friend profile ID
	
db.generate_mapping(create_tables=True)

class FbDB:
	rID = 0
	uid = ''
	def __init__(self, ppID, puid=None):
		# pID - user profile ID in FB
		# uid - UUID to run one time
		ir = None
		with orm.db_session():
			if not puid is None:
				ir = IRun.get(uid=puid)
			if ir is None:
				ir = IRun(dt=datetime.datetime.now(), uid=str(uuid.uuid4()), pID=ppID)
				orm.commit()
			self.rID = ir.id
			self.uid = ir.uid
	
	def saveFriend(self, jdata):
		with orm.db_session():
			ir = IRun.get(id=self.rID)
			for j in jdata:
				sf = Friend(irun=ir, data=j, name=j['name'], cntF=j['cntFriends'], cntM=j['cntFriendsM'], cntT=j['txtFriends'], frID=j['frID'])
			orm.flush()

	def saveFriendCount(self, cntF):
		with orm.db_session():
			ir = IRun.get(id=self.rID)
			ir.cntF = cntF
			orm.flush()