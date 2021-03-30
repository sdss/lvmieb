#We will not use this code no more. Please just use this code for reference _ CK

"""
import OSU_control as osu
from pymodbus3.client.sync import ModbusTcpClient as mbc
desi=osu.Controller()

print(desi.sensors)

######initialization process########

# Populate the self.sensors data structure 
wago_status1, reply = desi.getWAGOEnv()
if wago_status1:
    print("WAGO sensor values read")

# Populate self.controller_status data structure power values
wago_status2, reply = desi.getWAGOPower()
if wago_status2:
    print("WAGO power values read")

# If both previous steps returned True, set WAGO status to ready 
if wago_status1 and wago_status2:
    desi.controller_status['wago'] = 'READY'
else:
    print("ERROR: Did not read WAGO sensors/powers")

############################################################

print(desi.sensors)
"""
