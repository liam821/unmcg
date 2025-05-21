'''

unmcg: Unique Number MultiCast Generator

An overly complicated unique number generator that sends messages to each other via multicast

Thread-safe, multiple instances, and multiple host safe

        # 9223372036854775808 max number
        # 2405301200000000045
        # YYMMDDXXXNNNNNNNNNN
        # ^ ^ ^ ^  ^- seq number (0+=1...9999999999) (9.9b max in 24 hours)
        # | | | |---- thread id 1...999 (unique threadid using multicast discovery)
        # | | |------ day
        # | |-------- month
        # |---------- year  
        #
        # example number 2405301200001342768L

'''

import socket, sys, threading, traceback, time, uuid, datetime, random, struct, Queue, platform, json, os

if platform.python_implementation() == "Jython":
    # socket stuff
    from org.python.core.util import StringUtil
    from java.net import MulticastSocket, InetAddress, DatagramPacket, DatagramSocket

DEBUG = False

class unmcg:
    def __init__(self):
        self.other_dont_use_id_path = "/var/tmp/unmcg.json"
        self.other_dont_use_id = {}
        self.running = True
        self.threadid = uuid.uuid4().hex # generate a random threadid
        self.id = False
        self.discovery_id = False
        self.multicast_group = '224.1.2.3'
        self.multicast_port = 31173
        self.heartbeat_interval = 5
        self.number = 0
        self.lock = threading.Lock()
        self.queue = Queue.Queue()
        self.queue_watching = False
        self.cur_date = datetime.datetime.now().strftime("%y%m%d")
        self.listener_thread = threading.Thread(target=self.recv_multicast_listener)
        self.listener_thread.daemon = True
        self.listener_thread.start()

    def send_multicast_msg(self,msg):
        if platform.python_implementation() == "Jython":
            return self.jython_send_multicast_message(msg)
        else:
            return self.cpython_send_multicast_msg(msg)

    def cpython_send_multicast_msg(self,msg):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        print("INFO [%s]: sending multicast message: \"%s\" to: %s:%s" % (time.ctime(),msg,self.multicast_group,self.multicast_port))
        sock.sendto(msg.encode(), (self.multicast_group, self.multicast_port))
        sock.close()

    def jython_send_multicast_message(self,msg):
        sock = MulticastSocket()
        sock.setTimeToLive(2)
        group = InetAddress.getByName(self.multicast_group)
        data = msg.encode('utf-8')
        packet = DatagramPacket(data, len(data), group, self.multicast_port)
        print("INFO [%s]: sending multicast message: \"%s\" to: %s:%s" % (time.ctime(), msg, self.multicast_group, self.multicast_port))
        sock.send(packet)
        sock.close()

    def recv_multicast_listener(self):
        if platform.python_implementation() == "Jython":
            return self.jython_recv_multicast_listener()
        else:
            return self.cpython_recv_multicast_listener()
        
    def jython_recv_multicast_listener(self):
        sock = MulticastSocket(self.multicast_port)
        sock.setReuseAddress(True)
        group = InetAddress.getByName(self.multicast_group)
        sock.joinGroup(group)
        sock.setSoTimeout(1000)

        print("INFO [%s]: listening for multicast data on %s:%s" % (time.ctime(),self.multicast_group,self.multicast_port))
        while True and self.running:
            try:
                buffer = bytearray(1024)
                packet = DatagramPacket(buffer, len(buffer))
                sock.receive(packet)
                data = packet.getData()
                if DEBUG:
                    print(f"Received message: {data.decode('utf-8')}")

                data = data.tostring()
                msg = data.rstrip('\x00')
            except:
                if DEBUG:
                    traceback.print_exc()
            else:
                try:
                    msg = msg.split(" ")
                    if msg[1] != self.threadid:
                        print("INFO [%s]: received multicast message bytes: %s msg: %s" % (time.ctime(),len(msg),msg))
                        if self.queue_watching:
                            self.queue.put(msg)
                        if msg[0] == "discovery":
                            # don't send a response to ourselves
                            self.send_multicast_msg("id %s %s %s" % (self.threadid,self.discovery_time,self.discovery_id))
                            for id in self.other_dont_use_id.keys():
                                self.send_multicast_msg("id %s-oduid %s %s" % (self.threadid,self.other_dont_use_id[id],id))
                        if msg[0] == "id" and DEBUG:
                            print("INFO [%s]: thread: %s has id: %s with timestamp: %s" % (time.ctime(),msg[1],msg[3],msg[2]))
                except:
                    print("ERROR [%s]: something went wrong in recv_mutlicast!" % (time.ctime()))
                    traceback.print_exc()
        print("INFO [%s]: stopping jython_recv_multicast_listener thread" % (time.ctime()))
        sock.leaveGroup(group)
        sock.close()

    def cpython_recv_multicast_listener(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.multicast_group, self.multicast_port))
        #mreq = struct.pack('4sl', socket.inet_aton(self.multicast_group), socket.INADDR_ANY)
        mreq = struct.pack('4sl', socket.inet_aton(self.multicast_group), 0)

        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        sock.settimeout(1)

        print("INFO [%s]: listening for multicast data on %s:%s" % (time.ctime(),self.multicast_group,self.multicast_port))

        while True and self.running:
            try:
                msg = sock.recv(10240)
            except:
                pass
            else:
                #print 'received', len(msg), 'bytes:', msg
                try:
                    msg = msg.split(" ")
                    if msg[1] != self.threadid:
                        print("INFO [%s]: received multicast message bytes: %s msg: %s" % (time.ctime(),len(msg),msg))
                        if self.queue_watching:
                            self.queue.put(msg)
                        if msg[0] == "discovery":
                            # don't send a response to ourselves
                            self.send_multicast_msg("id %s %s %s" % (self.threadid,self.discovery_time,self.discovery_id))
                            for id in self.other_dont_use_id.keys():
                                self.send_multicast_msg("id %s-oduid %s %s" % (self.threadid,self.other_dont_use_id[id],id))
                        if msg[0] == "id" and DEBUG:
                            print("INFO [%s]: thread: %s has id: %s with timestamp: %s" % (time.ctime(),msg[1],msg[3],msg[2]))
                except:
                    print("ERROR [%s]: something went wrong in recv_mutlicast!" % (time.ctime()))
                    traceback.print_exc()
        print("INFO [%s]: stopping recv_multicast_listener thread" % (time.ctime()))

    def empty_Queue(self):
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except Queue.Empty:
                break

    def lockfile(self):
        # create lock file
        lock_file = self.other_dont_use_id_path + ".lock"
        while True:
            if not os.path.isfile(lock_file):
                with open(lock_file,"w") as f:
                    f.write("lockfile")
                return True
            else:
                print("INFO [%s]: Waiting on lockfile..." % (time.ctime()))
                time.sleep(1)
    
    def delLockfile(self):
        lock_file = self.other_dont_use_id_path + ".lock"
        try:
            os.remove(lock_file)
        except:
            print("ERROR [%s]: Got error trying to delete a file?" % (time.ctime()))
            traceback.print_exc()
    
    def readOtherIds(self):
        with self.lock:
            if not os.path.isfile(self.other_dont_use_id_path):
                return {}
            counter = 0
            try:
                self.lockfile()
                with open(self.other_dont_use_id_path,"r") as f:
                    json_blob = f.read()
                self.delLockfile()
                j = json.loads(json_blob)
                _json = {}
                # fix ID
                for _date in j.keys():
                    _json[_date] = {}
                    for id in j[_date]:
                        _json[_date][int(id)] = j[_date][id]
                return(_json)
            except:
                print("ERROR [%s]: Unable to load json other_dont_use_id: %s" % (time.ctime(),self.other_dont_use_id_path))
                traceback.print_exc()
                return {}
            
        
    def writeOtherIds(self):
        json_others_write = {}
        json_others = self.readOtherIds()
        with self.lock:
            self.lockfile()
            old_umask = os.umask(000)
            with open(self.other_dont_use_id_path,"w") as f:
                # clear out old data
                date_key = datetime.datetime.now().strftime("%y%m%d")
                if date_key in json_others:
                    json_others_write[date_key] = json_others[date_key]
                else:
                    json_others_write[date_key] = {}
                # rewrite the other_dont_use_id list
                self.other_dont_use_id = json_others_write[date_key]
                json_others_write[date_key][self.discovery_id] = self.discovery_time
                f.write(json.dumps(json_others_write))
            os.umask(old_umask)
            self.delLockfile()

    def id_discovery(self):
        date_key = datetime.datetime.now().strftime("%y%m%d")
        odui = self.readOtherIds()
        if date_key in odui:
            self.other_dont_use_id = odui[date_key]
        self.queue_watching = True
        # generate a random id
        self.discovery_id = random.randint(1,999)
        while True:
            if not self.discovery_id in self.other_dont_use_id:
                break
            else:
                print("INFO [%s]: Found %s in other_dont_use_id" % (time.ctime(),self.discovery_id))
                self.discovery_id = random.randint(1,999) # generate a random id
        while not self.id:
            discovery_end_time = int(time.time()) + 5
            #self.discovery_id = 0
            self.discovery_time = int(time.time() * 1000000)
            print("INFO [%s]: discovery picked id: %s time: %s" % (time.ctime(),self.discovery_id,self.discovery_time))
            self.send_multicast_msg("discovery %s %s %s" % (self.threadid,self.discovery_time,self.discovery_id))
            second = int(time.time())
            successful = True
            while time.time()<=discovery_end_time:
                if int(time.time()) > second:
                    self.send_multicast_msg("discovery %s %s %s" % (self.threadid,self.discovery_time,self.discovery_id))
                    second = int(time.time())
                try:
                    msg = self.queue.get(timeout=1)
                except:
                    pass
                else:
                    try:
                        if DEBUG:
                            print("msg0: %s msg1: %s msg2: %s msg3: %s" % (msg[0],msg[1],msg[2],msg[3]))
                        if msg[0] == "id":
                            if int(msg[3]) == self.discovery_id:
                                if int(msg[2]) < self.discovery_time:
                                    self.discovery_id = random.randint(0,999)
                                    print("INFO [%s]: threadid %s got to my ID first, picking something else %s" % (time.ctime(),msg[1],self.discovery_id))
                                    successful = False
                                    break
                    except:
                        print("ERROR [%s]: something went wrong in discovery!" % time.ctime())
                        traceback.print_exc()
            if successful:
                # great!
                self.id = self.discovery_id
                self.id_ljust = str(self.id).ljust(3,'0')
                print("INFO [%s]: ID discovery successful, my id is %s" % (time.ctime(),self.id))
        self.queue_watching = False
        self.empty_Queue()
        self.writeOtherIds()

    def get_number(self):
        # 9223372036854775808 max bigint number
        # 2405301200000000045
        # YYMMDDXXXNNNNNNNNNN
        # ^ ^ ^ ^  ^- seq number (0+=1...9999999999) (9.9b max in 24 hours)
        # | | | |---- thread id 1...999 (unique threadid using multicast discovery)
        # | | |------ day
        # | |-------- month
        # |---------- year  
        #
        # example number 2405301200001342768L
        # self.lock = make it thread safe
        while not self.id:
            print("INFO [%s]: waiting on id discovery...")
            time.sleep(1)
        date_key = datetime.datetime.now().strftime("%y%m%d")
        if date_key != self.cur_date:
            self.writeOtherIds()
        with self.lock:
            if date_key != self.cur_date:
                print("INFO [%s]: resetting sequence number because date change" % (time.ctime()))
                # reset the seq number at midnight
                self.cur_date = date_key
                self.number = 1
            else:
                self.number += 1
            return long(str(date_key + self.id_ljust + '%010d' % self.number))

print("INFO [%s]: Starting unmcg threads" % (time.ctime()))
_unmcg = unmcg()
print("INFO [%s]: Starting id discovery" % (time.ctime()))
_unmcg.id_discovery()

def get_number():
    global _unmcg
    return _unmcg.get_number()

def get_threadid():
    global _unmcg
    return _unmcg.threadid

def get_id():
    global _unmcg
    return _unmcg.id