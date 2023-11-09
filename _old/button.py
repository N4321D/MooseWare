"""
Driver for led button on RPi
"""
# logger
try:
    from subs.log import create_logger
except:
    def create_logger():
        class Logger():
            def __init__(self) -> None: 
                f = lambda *x: print("SETTINGS IO: ", *x)  # change messenger in whatever script you are importing
                self.warning = self.info = self.critical = self.debug = self.error = f
        return Logger()

logger = create_logger()

def log(message, level="info"):
    getattr(logger, level)("LED BUTTON: {}".format(message))  # change RECORDER SAVER IN CLASS NAME


# imports
try:
    import RPi.GPIO as GPIO

except Exception as e:
    log(f"GPIO module import error: {e}", "warning")

import time

class LedButton():
    button_ch = 16
    p_up_p_down = GPIO.PUD_UP  # GPIO.PUD_DOWN, GPIO.PUD_UP for pull up or GPIO.PUD_OFF for no pulldown
    bouncetime = 1             # inteval between button detections in ms (should not be smaller than 1)
    button_mode = GPIO.BOTH    # use GPIO.FALLING or GPIO.RISING as alternatives
    led_ch = 19
    pwm_f = 100                # pwm frequency
    pwm_dc = 10                # pwm Duty cycle

    led = None                 # placeholder for LED pwm module

    presstime = 0    # 
    releasetime = 0  # 

    def __init__(self, button_channel=16, led_channel=19) -> None:
        self.button_ch = button_channel
        self.led_ch = led_channel
        self.setup_GPIO()

    def setup_GPIO(self):
        # LED:
        GPIO.setup(self.led_ch, GPIO.OUT)
        self.led = GPIO.PWM(self.led_ch, self.pwm_f)
        self.led.start(0)

        # Button
        GPIO.setup(self.button_ch, GPIO.IN, 
                   pull_up_down=self.p_up_p_down)
    
    def clear_GPIO(self):
        GPIO.cleanup(self.led_ch)
        GPIO.cleanup(self.button_ch)

    def start_detection(self, *args):
        """
        binds press and release events to 
        on_press and on_release methods
        """
        self.remove_detection()
        # add new
        GPIO.add_event_detect(self.button_ch,
                              self.button_mode, 
                              callback=self.run, 
                              bouncetime=self.bouncetime)
    
    def remove_detection(self):
        # remove old callbacks
        GPIO.remove_event_detect(self.button_ch)
    
    def wait_for_button(self):
        return GPIO.wait_for_edge(self.button_ch, self.button_mode)
    
    def led_f(self, f):
        """
        sets led pwm frequency
        """
        if not self.led:
            return
        self.pwm_f = f
        self.led.ChangeFrequency(self.pwm_f)
    
    def led_dc(self, dc):
        """
        0 <= dc <= 100
        """
        if not self.led:
            return
        self.pwm_dc = dc
        self.led.ChangeDutyCycle(self.pwm_dc)
    
    def led_f_dc(self, f, dc):
        """
        sets led f and dc
        """
        self.led_f(f), self.led_dc(dc)
    
    def run(self, channel):
        mode = 0 if self.p_up_p_down is GPIO.PUD_UP else 1

        if GPIO.input(self.button_ch) == mode:
            self.presstime = time.time()
            self.on_press((self.presstime - self.releasetime)
                           if self.releasetime != 0 else 0)
        
        else:
            self.releasetime = time.time()
            touchduration = self.releasetime - self.presstime
            self.presstime = self.releasetime   # reset presstime in case of double release detection
            self.on_release(touchduration)
    
    def on_press(self, lastpresstime):
        """
        is called when button is pressed
        can be overwritten to add extra functions 
        such as blinking acknowledgement

        lastpress time is the time since the last release
        """
        return

    def on_release(self, touchduration):
        """
        is called when button is pressed
        can be overwritten to add extra functions 
        such as blinking acknowledgement

        touchduration can be used to discriminate 
        between short and longer presses
        """
        return
    


if __name__ == "__main__":
    b = LedButton()
    b.led_dc(1)
    b.led_f(20)
    log("\n\nPRESS BUTTON", "debug")
    print('press button to test, it will print hold and release time')
    def p(t):
        b.led_f_dc(10, 1)
        print("pressed, last press {:.3f}".format(t))
    
    def r(t):
        b.led_f_dc(1, 0.1)
        print("released after {:.3f} seconds".format(t))
    
    b.on_press, b.on_release = p, r
    b.start_detection()
