from time import sleep
from picamera import PiCamera
from RPi import GPIO  # General Purpose Input/Output
# Пины ввода/вывода общего назначения
import logging
import threading
import os

# l298n h-bridge module

ena_pin = 19 # чёрный # enable channel a
in3_pin = 26 # белый 
in4_pin = 21 # серый
in1_pin = 20 # фиолетовый 
in2_pin = 16 # синий
enb_pin = 12 # зелёный # enable channel b

"""
ena_pin = 19 # чёрный # enable channel a
in1_pin = 26 # белый 
in2_pin = 21 # серый
in3_pin = 20 # фиолетовый 
in4_pin = 16 # синий
enb_pin = 12 # зелёный # enable channel b
"""
class CarController:
    pwm_a, pwm_b = None, None  # Широтно-импульсная модуляция
    t = None  # таймер для остановки машинки если не пришел новый сигнал

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
        # Настраиваем пины для вывода информации из разбери
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
        self.pwm_b.start(100) # эта руль

    def go_forward(self):
        logging.info("goForward")
        self._stop_later("fwd")
        GPIO.output(in3_pin, GPIO.LOW)
        GPIO.output(in4_pin, GPIO.HIGH)
        
    def go_back(self):
        self._stop_later("back")
        GPIO.output(in3_pin, GPIO.HIGH)
        GPIO.output(in4_pin, GPIO.LOW)

    def turn_left(self):
        GPIO.output(in1_pin, GPIO.LOW)
        GPIO.output(in2_pin, GPIO.HIGH)
        
    def turn_right(self):
        GPIO.output(in1_pin, GPIO.HIGH)
        GPIO.output(in2_pin, GPIO.LOW)
        
    def turn_straight(self):
        GPIO.output(in1_pin, GPIO.LOW)
        GPIO.output(in2_pin, GPIO.LOW)
            
    def _stop_all(self):
        logging.info("in _stop_all")
        # Записываем нолик в пины, т.е. останавливаем и выприм руль
        GPIO.output(in1_pin, GPIO.LOW)
        GPIO.output(in2_pin, GPIO.LOW)
        GPIO.output(in3_pin, GPIO.LOW)
        GPIO.output(in4_pin, GPIO.LOW)
        
    def _stop_later(self,name):
        if not self.t is None:
            self.t.cancel()
        self.t = threading.Timer(2.0, self._do_stop, {name})
        logging.info("in stop_later %s", name)
        self.t.start()

    def _do_stop(self,name):
        self._stop_all();
        logging.info("stopped after %s", name)
        
    def ride(self, angle, strength):
        logging.info("ride: angle=%s; strength=%s", angle, strength)
        if strength < 50:
            self.turn_straight()
            self._stop_all()
        elif 0 <= angle <= 59:  # TODO: forward-right
            self.turn_right()
            self.go_forward()
        elif 60 <= angle <= 119:  # TODO: forward
            self.turn_straight()
            self.go_forward()
        elif 120 <= angle <= 179:  # TODO: forward-left
            self.turn_left()
            self.go_forward()
        elif 180 <= angle <= 239:  # TODO: back-left
            self.turn_left()
            self.go_back()
        elif 240 <= angle <= 299:  # TODO: back
            self.turn_straight()
            self.go_back()
        elif 300 <= angle <= 360:  # TODO: back-right
            self.turn_right()
            self.go_back()
    

if __name__ == "__main__":
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO ) # , datefmt="%H:%M:%S,%03d" )
    with CarController() as c:
#        c.go_forward()
#        sleep(1)
        c.ride(0,51)
        sleep(4)
        c.ride(60,51)
        sleep(4)
        c.ride(120,51)
        sleep(4)
        c.ride(180,51)
        sleep(4)
        c.ride(240,51)
        sleep(4)
        c.ride(300,51)
        sleep(4)
        c.ride(300,40)
        sleep(4)
        
        sleep(1)
        #c._stop_all()
        #c.go_back()
        
        #c.t.cancel()
        #c.t.cancel()
    
        #sleep(3)
        
    logging.info("main quit")
    
