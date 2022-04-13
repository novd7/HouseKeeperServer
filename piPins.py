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
        self.pwm_a.start(50)  # эта тяга двигателя
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
        
    def go_stop(self):
        GPIO.output(in3_pin, GPIO.LOW)
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
        self.turn_straight()
        self.go_stop()
        
    def _stop_later(self,name="nd"):
        if not self.t is None:
            self.t.cancel()
        self.t = threading.Timer(0.25, self._do_stop, {name})
        logging.info("in stop_later %s", name)
        self.t.start()

    def _do_stop(self,name):
        self._stop_all();
        logging.info("stopped after %s", name)
        
    def ride(self, angle, strength):
        logging.info("ride: angle=%s; strength=%s", angle, strength)
        if 80 <= angle <= 100 or 260 <= angle <= 280:
            self.turn_straight()
        elif 100 <= angle <= 260:
            self.turn_left()
        else:
            self.turn_right()
            
        if strength < 33:
            self._stop_all()
        elif 10 <= angle <= 170:
            self.go_forward()
        elif 190 <= angle <= 350:
            self.go_back()
        else:
            self.go_stop()
            
        self._stop_later("ride")
    

if __name__ == "__main__":
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO )
    with CarController() as c:
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
        
        sleep(2)
        #c._stop_all()
        #c.go_back()
        
        #c.t.cancel()
        #c.t.cancel()
    
        #sleep(3)
        
    logging.info("main quit")
    
