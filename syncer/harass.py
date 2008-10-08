import utils, random, Queue, threading, time

NO_ACTIONS = 100000
NO_WORKERS = 40

plist = utils.PList("test.lst")

#print plist

inputs = (dict(a = 9), [1,3,5,7,9], "A String", 90348721, 88.9991, "foo", (dict(), [], (3,2,1)))

def put():
    return plist.put(random.choice(inputs))

def get():
    if plist:
        plist.pop()
    return True

actions = (put, get, plist.dump)

def action():
    return random.choice(actions)

def worker(i):
    time.sleep(1)
    while not work_q.empty():
        action = work_q.get()
        #print "worker # %d: executing %s" % (i, action)
        if action():
            print "worker # %d: %s" % (i, action.func_name)
        else:
            print "FAILED FAILED worker # %d: %s" % (i, action.func_name)
        #print "worker # %d: done executing %s" % (i, action)
        work_q.task_done()

work_q = Queue.Queue()

for i in range(NO_ACTIONS):
    work_q.put(action())
#print work_q.queue

for i in range(NO_WORKERS):
    print i
    threading.Thread(target=worker, args=(i,)).start()

work_q.join()
plist.dump()
