from airtouch2 import AT2Client
from airtouch2 import ACFanSpeedReference, ACMode
import logging
import threading
logging.basicConfig(filename='airtouch2.log',filemode='a', level=logging.DEBUG, format='%(asctime)s %(threadName)s %(levelname)s: %(message)s')
LOGGER = logging.getLogger()

# For testing the client
# type:
#    ac power on/off
#    ac temp [value in deg C]
#    get (get a response message and update the local AC object's state)
ip = input('Enter ip address of airtouch2 (e.g. 192.168.1.15): ')
client  = AT2Client(ip, dump=True)

if not client.start():
    LOGGER.warning("Client did not start")
    exit()
inp = '\0'
while inp != 'q':
    inp = input()
    if inp.startswith("ac"):
        rem = inp[2:].strip()
        if rem.startswith("power"):
            rem = rem[5:].strip()
            if rem.startswith("off"):
                client.aircons[0].turn_on_off(False)
            if rem.startswith("on"):
                client.aircons[0].turn_on_off(True)
        if rem.startswith("temp"):
            rem = rem[4:].strip()
            client.aircons[0].set_set_temp(int(rem))
        if rem.startswith("fan"):
            rem = rem[3:].strip()
            client.aircons[0].set_fan_speed(ACFanSpeedReference(int(rem)))
        if rem.startswith("mode"):
            rem = rem[4:].strip()
            client.aircons[0].set_mode(ACMode(int(rem)))
    if inp.startswith("group"):
        rem = inp[5:].strip()
        if rem.startswith("on"):
            rem = rem[2:].strip()
            client.groups[int(rem)].turn_on()
        elif rem.startswith("off"):
            rem = rem[3:].strip()
            client.groups[int(rem)].turn_off()
        else:
            [val, group_no] = rem.split()
            i = int(group_no)
            val = int(val)
            print(f"Setting {i} to {val}")
            client.groups[i].set_damp(val)
    if inp.startswith("get"):
        client.update_state()
    if inp.startswith("lt"):
        for thread in threading.enumerate():
            print(thread.name)
client.stop()