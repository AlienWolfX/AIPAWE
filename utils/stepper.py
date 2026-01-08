import RPi.GPIO as GPIO
import time

class A4988Stepper:

    def __init__(self, step_pin=24, dir_pin=23, enable_pin=None, ms1_pin=None, ms2_pin=None, ms3_pin=None):
        self.step_pin = step_pin
        self.dir_pin = dir_pin
        self.enable_pin = enable_pin
        self.ms1_pin = ms1_pin
        self.ms2_pin = ms2_pin
        self.ms3_pin = ms3_pin
        self.microstep_multiplier = 1  
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        GPIO.setup(self.step_pin, GPIO.OUT)
        GPIO.setup(self.dir_pin, GPIO.OUT)
        
        GPIO.output(self.step_pin, GPIO.LOW)
        GPIO.output(self.dir_pin, GPIO.LOW)
        
        if self.enable_pin is not None:
            GPIO.setup(self.enable_pin, GPIO.OUT)
            GPIO.output(self.enable_pin, GPIO.HIGH)  
        
        # Setup microstepping pins
        if self.ms1_pin is not None:
            GPIO.setup(self.ms1_pin, GPIO.OUT)
            GPIO.output(self.ms1_pin, GPIO.LOW)
        if self.ms2_pin is not None:
            GPIO.setup(self.ms2_pin, GPIO.OUT)
            GPIO.output(self.ms2_pin, GPIO.LOW)
        if self.ms3_pin is not None:
            GPIO.setup(self.ms3_pin, GPIO.OUT)
            GPIO.output(self.ms3_pin, GPIO.LOW)
    
    def set_microstepping(self, mode='1/16'):
        """Set microstepping mode. Options: 'full', '1/2', '1/4', '1/8', '1/16'"""
        modes = {
            'full': (False, False, False, 1),
            '1/2': (True, False, False, 2),
            '1/4': (False, True, False, 4),
            '1/8': (True, True, False, 8),
            '1/16': (True, True, True, 16)
        }
        
        if mode not in modes:
            raise ValueError(f"Invalid mode. Choose from: {list(modes.keys())}")
        
        ms1, ms2, ms3, multiplier = modes[mode]
        self.microstep_multiplier = multiplier
        
        if self.ms1_pin is not None:
            GPIO.output(self.ms1_pin, GPIO.HIGH if ms1 else GPIO.LOW)
        if self.ms2_pin is not None:
            GPIO.output(self.ms2_pin, GPIO.HIGH if ms2 else GPIO.LOW)
        if self.ms3_pin is not None:
            GPIO.output(self.ms3_pin, GPIO.HIGH if ms3 else GPIO.LOW)
    
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
        steps = int((degrees / 360.0) * steps_per_rev * self.microstep_multiplier)
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
    motor = A4988Stepper(step_pin=24, dir_pin=23, enable_pin=25, ms1_pin=17, ms2_pin=22, ms3_pin=27)
    
    try:
        print("Setting all GPIO pins to LOW...")
        GPIO.output(motor.step_pin, GPIO.LOW)
        GPIO.output(motor.dir_pin, GPIO.LOW)
        if motor.enable_pin is not None:
            GPIO.output(motor.enable_pin, GPIO.LOW)
        if motor.ms1_pin is not None:
            GPIO.output(motor.ms1_pin, GPIO.LOW)
        if motor.ms2_pin is not None:
            GPIO.output(motor.ms2_pin, GPIO.LOW)
        if motor.ms3_pin is not None:
            GPIO.output(motor.ms3_pin, GPIO.LOW)
        
        print("Waiting 10 seconds for stabilization...")
        for i in range(10, 0, -1):
            print(f"{i}...", end=" ", flush=True)
            time.sleep(1)
        print("\n")
        
        motor.set_microstepping('1/16')  
        motor.enable() 
        print("Starting continuous 360-degree rotation (1/16 microstepping - smooth & quiet)...")
        print("Press Ctrl+C to stop")
        
        rotation_count = 0
        while True:
            rotation_count += 1
            print(f"Rotation #{rotation_count} - 360 degrees...")
            motor.rotate_degrees(360, clockwise=True, delay=0.015)
            time.sleep(0.5)  
        
    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        motor.disable()
        motor.cleanup()
        print("GPIO cleaned up")
