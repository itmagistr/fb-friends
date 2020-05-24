import asyncio
#from aiodebug import log_slow_callbacks
import random
from bs4 import BeautifulSoup as bs
from fb_parser import getFriendID, getNumFriends
import time
import logging
#logging.basicConfig()
#logging.getLogger().setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO)
logging.getLogger("asyncio").setLevel(logging.INFO)
logging.getLogger().addHandler(logging.FileHandler("fb_friends.log"))


async def worker(name, queue, uid):
	print(f'starts {name}')
	#raise Exception(f"Could not consume {uid}")
	htmlstr = '7656'
	p=0
	while len(htmlstr) > 0:
		await asyncio.sleep(0.1) #
		p+=1
		# Get a "work item" out of the queue.
		try:
			htmlstr = queue.get_nowait()
		except asyncio.QueueEmpty:
			htmlstr = ''
		
		if len(htmlstr) > 0:
			suop = bs(htmlstr, 'html.parser') #soup.select("#link1 + .sister")

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

			# Notify the queue that the "work item" has been processed.
			queue.task_done()
			# Sleep for the "sleep_for" seconds.

async def monitor_tasks():
    while True:
        tasks = [
            t for t in asyncio.all_tasks() 
            if t is not asyncio.current_task()
        ]
        [t.print_stack(limit=5) for t in tasks]
        await asyncio.sleep(2)		

def exct_handler(loop, data):
        print("except handler")
        print(data["message"])
        print(data["exception"])

async def main():
	#loop = asyncio.get_event_loop()
	#loop.set_exception_handler(exct_handler)
	#log_slow_callbacks.enable(0.5)
	#fl = 'C:/Users/User/Downloads/x_fbfriends_200523_0223.html'  file:///C:/Users/User/Downloads/x_fbfriends_200523_0223.html
	fl = 'x_fbfriends_200522_1451.html'
	currunuid = '2938348b-fdcb-469b-b04a-86ccd611cd2e'

	queue = asyncio.Queue()
	resT=[]
	for n in range(1,31):
		cnt=0
		with open(fl, 'r', encoding='utf-8') as fp:
			soup = bs(fp, 'html.parser')
		for el in soup.find_all('li', class_="_698"):
			#print(str(el)[0:30])
			queue.put_nowait(str(el))
			cnt+=1
		logging.info('q elements: {}'.format(cnt))
		print(f'Create {n} worker tasks to process the queue concurrently.')
		
		tasks = [] #[asyncio.create_task(monitor_tasks())]
	
		
		started_at = time.monotonic()
		for i in range(n):
			task = asyncio.create_task(worker(f'worker-{i}', queue, currunuid))
			tasks.append(task)
		
		
		# Wait until the queue is fully processed.
		#started_at = time.monotonic()
		#await queue.join()
		#total_slept_for = time.monotonic() - started_at
		#print(f'spent time: {total_slept_for}')
		
		# Cancel our worker tasks.
		# for task in tasks:
		# 	task.cancel()
		# Wait until all worker tasks are cancelled.
		await asyncio.gather(*tasks, return_exceptions=False)
		total_slept_for = time.monotonic() - started_at
		logging.info('threads {}, time {:07.2f}'.format(n, total_slept_for))
		resT.append({'n':n, 't': total_slept_for})
	
	for r in resT:
		logging.info('{:02d};{:07d}'.format(r['n'], round(r['t']*1000)))
	return 0

if __name__ == '__main__':
	asyncio.run(main(), debug=False)