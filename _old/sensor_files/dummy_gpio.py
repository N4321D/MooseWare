"""
dummy GPIO and bus for testing
"""
from random import randint
import time

class bus():
    def write_byte_date(*args, **kwargs):
        return

    def read_byte_date(*args, **kwargs):
        return randint(0, 0xff)

class PWM():
    def __init__(self, *args, **kwargs):
        pass
    
    def start(self, *args, **kwargs):
        pass
    
    def ChangeFrequency(self, *args, **kwargs):
        pass

    def ChangeDutyCycle(self, *args, **kwargs):
        pass

    def stop(self, *args, **kwargs):
        pass

class GPIO():
    IN = 1
    OUT = 2
    
    PUD_DOWN = 12
    PUD_UP = 11
    PUD_OFF = 0
    BOTH = 5
    
    BCM = None
    BOARD = None

    PWM = PWM

    out_val = 0
    last_change = 0
    change_interval = 0.5

    def setup(self, *args, **kwargs):
        pass
    def setmode(self, *args, **kwargs):
        pass
    def input(self, *args, **kwargs):
        t = time.time()
        if (t - GPIO.last_change) > GPIO.change_interval:
            GPIO.out_val = int(not GPIO.out_val)
            GPIO.last_change = t
            GPIO.change_interval = randint(1, 20)/10
        return GPIO.out_val

    def output(self, *args, **kwargs):
        pass
    def cleanup(self, *args, **kwargs):
        pass
    def add_event_detect(self, *args, **kwargs):
        pass
    def remove_event_detect(self, *args, **kwargs):
        pass
    def wait_for_edge(self, *args, **kwargs):
        pass