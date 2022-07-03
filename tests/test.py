from airtouch2 import AT2Client
from airtouch2 import ACFanSpeed, ACMode
# For testing the client
# type:
#    ac power on/off
#    ac temp [value in deg C]
#    get (get a response message and update the local AC object's state)
client  = AT2Client("192.168.1.21")
client.start()
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
            client.aircons[0].set_fan_speed(ACFanSpeed[rem])
        if rem.startswith("mode"):
            rem = rem[4:].strip()
            client.aircons[0].set_mode(ACMode[rem])
    if inp.startswith("get"):
        client.update_state()
client.stop()