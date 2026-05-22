import warnings
# Silence the asyncore warning cleanly
warnings.filterwarnings("ignore", category=DeprecationWarning)

import socket
import asyncore
import random
import pickle

BUFFERSIZE = 8192
print("Server Address: " + socket.gethostbyname(socket.gethostname()))

outgoing = []
minionmap = {}

class Minion:
    def __init__(self, player_id):
        self.x = 50
        self.y = 50
        self.sync_img = None
        self.sync_img_index = None
        self.left_img_index = 0
        self.right_img_index = 0
        self.up_img_index = 0
        self.down_img_index = 0
        self.alive_status = True
        self.player_id = player_id
        self.player_colour = None
        self.tasks_completed = 0
        self.sabotagelights_sync = 0
        self.sabotagereactor_sync = 0
        self.victim_id = 0
        self.imposter = False  
        self.emergency_sync = 0
        self.voted = None
        self.got_votes = 0
        self.emergency_meeting_img_sync = None
        self.emergency_meeting_img_sync_report = None
        self.victim_id_report = 0
        self.got_reported = False
        self.eject_sync = False
        self.eject_img = None

def assign_dynamic_roles():
    player_ids = list(minionmap.keys())
    total_count = len(player_ids)
    if total_count == 0: return
    for p_id in player_ids:
        minionmap[p_id].imposter = False
    if total_count <= 5:
        impostor_quota = 1
    elif total_count < 10:
        impostor_quota = 2
    else:
        impostor_quota = 3
    chosen_impostors = random.sample(player_ids, min(impostor_quota, total_count))
    for imp_id in chosen_impostors:
        minionmap[imp_id].imposter = True
    print(f"[ROLE CONFIG] Players: {total_count} | Assigned Impostors Quota: {impostor_quota}")

def updateWorld(message):
    try:
        arr = pickle.loads(message)
    except Exception:
        return
        
    # Safety checks to prevent empty or broken list items from crashing your server
    if not isinstance(arr, list) or len(arr) < 26: 
        return
        
    player_id = arr[1]
    if player_id == 0:
        return
        
    if player_id not in minionmap:
        minionmap[player_id] = Minion(player_id)
        
    # Restored your correct original array indices here:
    minionmap[player_id].x = arr[2]
    minionmap[player_id].y = arr[3]
    minionmap[player_id].alive_status = arr[4]
    minionmap[player_id].sync_img = arr[5]
    minionmap[player_id].sync_img_index = arr[6]
    minionmap[player_id].left_img_index = arr[7]
    minionmap[player_id].right_img_index = arr[8]
    minionmap[player_id].up_img_index = arr[9]
    minionmap[player_id].down_img_index = arr[10]
    minionmap[player_id].player_colour = arr[11]
    minionmap[player_id].tasks_completed = arr[12]
    minionmap[player_id].sabotagelights_sync = arr[13]
    minionmap[player_id].sabotagereactor_sync = arr[14]
    minionmap[player_id].victim_id = arr[15]
    minionmap[player_id].emergency_sync = arr[17]
    minionmap[player_id].voted = arr[18]
    minionmap[player_id].got_votes = arr[19]
    minionmap[player_id].emergency_meeting_img_sync = arr[20]
    minionmap[player_id].emergency_meeting_img_sync_report = arr[21]
    minionmap[player_id].victim_id_report = arr[22]
    minionmap[player_id].got_reported = arr[23]
    minionmap[player_id].eject_sync = arr[24]
    minionmap[player_id].eject_img = arr[25]
    
    remove = []
    update = ['player locations']
    for key, value in minionmap.items():
        update.append([
            value.player_id, value.x, value.y, value.alive_status, 
            value.sync_img, value.sync_img_index, value.left_img_index, 
            value.right_img_index, value.up_img_index, value.down_img_index, 
            value.player_colour, value.tasks_completed, value.sabotagelights_sync, 
            value.sabotagereactor_sync, value.victim_id, value.imposter, 
            value.emergency_sync, value.voted, value.got_votes, 
            value.emergency_meeting_img_sync, value.emergency_meeting_img_sync_report, 
            value.victim_id_report, value.got_reported, value.eject_sync, value.eject_img
        ])
        
    serialized_data = pickle.dumps(update)
    for i in outgoing:
        try:
            i.send(serialized_data)
        except Exception:
            remove.append(i)
            
    for r in remove:
        if r in outgoing:
            outgoing.remove(r)

class MainServer(asyncore.dispatcher):
    def __init__(self, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind(('', port))
        self.listen(10)
        
    def handle_accept(self):
        try:
            conn, addr = self.accept()
            outgoing.append(conn)
            player_id = random.randint(1000, 1000000)
            playerminion = Minion(player_id)
            minionmap[player_id] = playerminion
            assign_dynamic_roles()
            conn.send(pickle.dumps(['id update', player_id]))
            SecondaryServer(conn)
        except Exception:
            pass

class SecondaryServer(asyncore.dispatcher_with_send):
    def handle_read(self):
        try:
            recievedData = self.recv(BUFFERSIZE)
            if recievedData:
                updateWorld(recievedData)
            else:
                self.close()
        except Exception:
            self.close()
            
    def handle_close(self):
        if self.socket in outgoing:
            outgoing.remove(self.socket)
        self.close()

MainServer(4321)
asyncore.loop()
