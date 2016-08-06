"""
Car horn based wakeup alarm, for heavy sleepers.

Requires a local Gateway to send tm(h,m,s) reports periodically - at least once per minute. 
For timely, reliable alarm, send tm() every 10sec from gateway.

25ms pulse is relatively quiet. 250ms is loud. 1000ms is extreme.


"""

from synapse.platforms import *

SILENT_DEBUG = False

ALARM_OUT = GPIO_10

LED_GRN = GPIO_1
LED_YLW = GPIO_2

HRS_0 = GPIO_4
HRS_1 = GPIO_5
HRS_2 = GPIO_6
HRS_3 = GPIO_7
HRS_4 = GPIO_8
HOURS = (HRS_0, HRS_1, HRS_2, HRS_3, HRS_4)

MIN_0 = GPIO_11
MIN_1 = GPIO_12
MIN_2 = GPIO_13
MIN_3 = GPIO_14
MIN_4 = GPIO_15
MIN_5 = GPIO_16
MINUTES = (MIN_0, MIN_1, MIN_2, MIN_3, MIN_4, MIN_5)

MASTER_TIMEOUT = 300
master_tm_timeout = MASTER_TIMEOUT


ENABLE = GPIO_17

WAKEUP_SEQ1 = [ 25, 25, 25, 25, 25, 25, 25, 25, 25, 25,
               100,100,100,100,100,100,100,100,100,100,
               255,255,255,255,255,255,255,255,255,255]

# Alarm sequence tracking
idx_active_alarm_seq = 0
active_alarm_seq = []

# Inputs
hr_set = 0
min_set = 0
enable = False

# No re-trigger if re-enabled in same minute
trigger_min = -1  # No trigger

@setHook(HOOK_STARTUP)
def start():
    # Init protoboard LEDS
    setPinDir(LED_GRN, True)
    pulsePin(LED_GRN, 100, True)
    setPinDir(LED_YLW, True)
    pulsePin(LED_YLW, 500, True)
    
    # Init alarm output
    writePin(ALARM_OUT, False)
    setPinDir(ALARM_OUT, True)

    # Init switch inputs
    init_sw_input(ENABLE)
    for pin in HOURS:
        init_sw_input(pin)
    for pin in MINUTES:
        init_sw_input(pin)
        
    read_inputs()

def init_sw_input(pin):
    setPinDir(pin, False)
    setPinPullup(pin, True)
    monitorPin(pin, True)
    
def short_beep():
    pulsePin(ALARM_OUT, 250, True)

def start_wakeup_seq():
    start_alarm_seq(WAKEUP_SEQ1)

def start_alarm_seq(seq):
    global active_alarm_seq, idx_active_alarm_seq
    active_alarm_seq = seq
    idx_active_alarm_seq = 0
    print "len(seq)=", len(seq)

def silence_alarm():
    global active_alarm_seq, idx_active_alarm_seq
    active_alarm_seq = []
    idx_active_alarm_seq = 0
    writePin(ALARM_OUT, False)

def tm(hrs, min, sec):
    """RPC broadcast periodically by local gateway, sends time in local timezone"""
    global trigger_min, master_tm_timeout
    master_tm_timeout = MASTER_TIMEOUT

    if hrs == hr_set and min == min_set:
        if min != trigger_min:
            # Haven't already triggered alarm in this minute
            if enable:
                start_wakeup_seq()
                trigger_min = min
            else:
                print "Alarm start NOW! ...but not currently enabled :/"
    else:
        trigger_min = -1  # No trigger

@setHook(HOOK_1S)
def alarm_sequence():
    global active_alarm_seq, idx_active_alarm_seq, master_tm_timeout
    
    master_tm_timeout -= 1
    if master_tm_timeout == 0:
        #short_beep()   # Alert! We have no time source - alarm will not sound as scheduled!
        master_tm_timeout = MASTER_TIMEOUT
    
    if active_alarm_seq:
        if SILENT_DEBUG:
            print "beep! seq=", idx_active_alarm_seq, ", dur=", active_alarm_seq[idx_active_alarm_seq]
        else:
            pulsePin(ALARM_OUT, active_alarm_seq[idx_active_alarm_seq], True)
        idx_active_alarm_seq += 1
        if idx_active_alarm_seq == len(active_alarm_seq):
            idx_active_alarm_seq = 0
            active_alarm_seq = []
        

@setHook(HOOK_GPIN)
def pin_event(pin, is_set):
    read_inputs()
    
def read_sw_bank(bank):
    val = 0
    for i in xrange(len(bank)):
        b = not readPin(bank[i])
        val |= (b << i)
        
    return val
    
def read_inputs():
    global hr_set, min_set, enable
    hr_set = read_sw_bank(HOURS)
    min_set = read_sw_bank(MINUTES)
    enable = not readPin(ENABLE)
    if not enable:
        silence_alarm()
    
    print "Set HR=", hr_set, ", MIN=", min_set, ", EN=", enable
    
    
