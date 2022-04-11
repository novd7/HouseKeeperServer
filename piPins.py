from time import sleep
from picamera import PiCamera
from RPi import GPIO
import logging
import threading
import os

# l298n h-bridge module

ena_pin = 19 # чёрный
in1_pin = 26 # белый 
in2_pin = 21 # серый
in3_pin = 20 # фиолетовый 
in4_pin = 16 # синий
enb_pin = 12 # зелёный 

class CarController():
    pwm_a, pwm_b = None, None
    t = None

    def __init__(self):
        logging.info('CarController pid %s', os.getpid())
        self._init_pins()

    def __enter__(self):
         return self

    def __exit__(self, exc_type, exc_value, traceback):
        if(not self.t is None):
            self.t.cancel()
        self._stop_all()
        GPIO.cleanup()
        logging.info("CarController gpio cleared.")
    
    def _init_pins(self):
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(in1_pin, GPIO.OUT)
        GPIO.setup(in2_pin, GPIO.OUT)
        GPIO.setup(ena_pin, GPIO.OUT)

        GPIO.setup(in3_pin, GPIO.OUT)
        GPIO.setup(in4_pin, GPIO.OUT)
        GPIO.setup(enb_pin, GPIO.OUT)

        self._stop_all()

        self.pwm_a = GPIO.PWM(ena_pin,1000)
        self.pwm_a.start(100)
        self.pwm_b = GPIO.PWM(enb_pin,1000)
        self.pwm_b.start(50)

    def go_forward(self):
        logging.info("goForward")
        self._stop_later("fwd")
        GPIO.output(in3_pin, GPIO.LOW)
        GPIO.output(in4_pin, GPIO.HIGH)
        
        
    def go_back(self):
        GPIO.output(in3_pin, GPIO.HIGH)
        GPIO.output(in4_pin, GPIO.LOW)

    def turn_left(self):
        GPIO.output(in1_pin, GPIO.LOW)
        GPIO.output(in2_pin, GPIO.HIGH)
        
    def turn_right(self):
        GPIO.output(in1_pin, GPIO.HIGH)
        GPIO.output(in2_pin, GPIO.LOW)
        
    def turn_forward(self):
        GPIO.output(in1_pin, GPIO.LOW)
        GPIO.output(in2_pin, GPIO.LOW)
            
    def _stop_all(self):
        logging.info("in _stop_all")
        GPIO.output(in1_pin, GPIO.LOW)
        GPIO.output(in2_pin, GPIO.LOW)
        GPIO.output(in3_pin, GPIO.LOW)
        GPIO.output(in4_pin, GPIO.LOW)
        
    def _stop_later(self,name):
        if(not self.t is None):
            self.t.cancel()
        self.t = threading.Timer(2.0, self._do_stop, {name})
        logging.info("in stop_later %s", name)
        self.t.start()

    def _do_stop(self,name):
        self._stop_all();
        logging.info("stopped after %s", name)
    

if __name__ == "__main__":
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO ) # , datefmt="%H:%M:%S,%03d" )
    
    with CarController() as c:
        c.go_forward()
        sleep(0.5)
        c.go_forward()
        #c.t.cancel()
        #c.t.cancel()
    
        sleep(5)
    logging.info("main quit")
    
