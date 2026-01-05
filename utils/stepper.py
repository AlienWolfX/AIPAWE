import RPi.GPIO as GPIO
import time


class A4988Stepper:

    def __init__(self, step_pin=24, dir_pin=23, enable_pin=None):
        self.step_pin = step_pin
        self.dir_pin = dir_pin
        self.enable_pin = enable_pin
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        GPIO.setup(self.step_pin, GPIO.OUT)
        GPIO.setup(self.dir_pin, GPIO.OUT)
        
        if self.enable_pin is not None:
            GPIO.setup(self.enable_pin, GPIO.OUT)
            GPIO.output(self.enable_pin, GPIO.LOW) 
        
        GPIO.output(self.dir_pin, GPIO.LOW)
    
    def set_direction(self, clockwise=True):
        GPIO.output(self.dir_pin, GPIO.HIGH if clockwise else GPIO.LOW)
    
    def step(self, delay=0.001):
        GPIO.output(self.step_pin, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(self.step_pin, GPIO.LOW)
        time.sleep(delay)
    
    def rotate(self, steps, clockwise=True, delay=0.001):
        self.set_direction(clockwise)
        for _ in range(abs(steps)):
            self.step(delay)
    
    def rotate_degrees(self, degrees, clockwise=True, delay=0.001, steps_per_rev=200):
        steps = int((degrees / 360.0) * steps_per_rev)
        self.rotate(steps, clockwise, delay)
    
    def enable(self):
        if self.enable_pin is not None:
            GPIO.output(self.enable_pin, GPIO.LOW)
    
    def disable(self):
        if self.enable_pin is not None:
            GPIO.output(self.enable_pin, GPIO.HIGH)
    
    def cleanup(self):
        GPIO.cleanup([self.step_pin, self.dir_pin])
        if self.enable_pin is not None:
            GPIO.cleanup(self.enable_pin)


if __name__ == "__main__":
    motor = A4988Stepper(step_pin=24, dir_pin=23)
    
    try:
        print("Rotating 200 steps clockwise...")
        motor.rotate(200, clockwise=True, delay=0.002)
        
        time.sleep(1)
        
        print("Rotating 200 steps counter-clockwise...")
        motor.rotate(200, clockwise=False, delay=0.002)
        
        time.sleep(1)
        
        print("Rotating 180 degrees clockwise...")
        motor.rotate_degrees(180, clockwise=True, delay=0.002)
        
    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        motor.cleanup()
        print("GPIO cleaned up")
