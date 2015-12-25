from snapconnect import snap
import os
import sys
import simple_ntp
import time


NTP_UPDATE_PERIOD = 12*60*60  # seconds per update
TM_BCAST_PERIOD = 5

def setGreenLed(value):
    if sys.platform.startswith('linux'):
        os.system("echo "+str(value)+" >> /sys/class/leds/greenled/brightness")

def setRedLed(value):
    if sys.platform.startswith('linux'):
        os.system("echo "+str(value)+" >> /sys/class/leds/redled/brightness")

        
def update_sys_time():
    try:
        date_str = simple_ntp.getNTPTime()
        os.system('date %s' % date_str)
    except:
        pass
    return True

def send_time():
    now = time.localtime()
    #print "send_time(%d,%d)" % (now.tm_hour, now.tm_min)
    snapCom.mcast_rpc(1, 2, 'tm', now.tm_hour, now.tm_min)
    return True
        
def main():
    global server, snapCom

    print "Start"
    update_sys_time()
    
    # Create SNAP instance and establish serial (bridge) link
    snapCom = snap.Snap()
    snapCom.open_serial(snap.SERIAL_TYPE_RS232, '/dev/ttyS1')
    #snapCom.accept_tcp()

    # Schedule periodic events
    snapCom.scheduler.schedule(NTP_UPDATE_PERIOD, update_sys_time)
    snapCom.scheduler.schedule(TM_BCAST_PERIOD, send_time)
    
    
if __name__ == '__main__':
    main()
    snapCom.loop()

    
