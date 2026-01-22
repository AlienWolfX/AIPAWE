import time

# Try to import GPIO libraries - Raspberry Pi 5 uses lgpio, older models use RPi.GPIO
try:
    import lgpio
    GPIO_LIB = 'lgpio'
    print("Using lgpio for Raspberry Pi 5")
except ImportError:
    try:
        import RPi.GPIO as GPIO
        GPIO_LIB = 'RPi.GPIO'
        print("Using RPi.GPIO for Raspberry Pi 4 or earlier")
    except ImportError:
        raise NotImplementedError("No GPIO library available - must run on Raspberry Pi")


class A4988Stepper:
    """
    A4988 Stepper Motor Driver Controller.
    
    Controls stepper motors via A4988 driver with support for microstepping.
    Compatible with both Raspberry Pi 4 (RPi.GPIO) and Raspberry Pi 5 (lgpio).
    """
    
    def __init__(self, step_pin=24, dir_pin=23, enable_pin=25, 
                 ms1_pin=17, ms2_pin=22, ms3_pin=27):
        """
        Initialize A4988 stepper motor driver.
        
        Args:
            step_pin: GPIO pin for step signal
            dir_pin: GPIO pin for direction signal
            enable_pin: GPIO pin for enable signal
            ms1_pin, ms2_pin, ms3_pin: GPIO pins for microstepping configuration
        """
        self.step_pin = step_pin
        self.dir_pin = dir_pin
        self.enable_pin = enable_pin
        self.ms1_pin = ms1_pin
        self.ms2_pin = ms2_pin
        self.ms3_pin = ms3_pin
        self.microstep_multiplier = 1
        
        if GPIO_LIB == 'lgpio':
            # Raspberry Pi 5 using lgpio
            self.gpio_chip = lgpio.gpiochip_open(4)  # gpiochip4 on Pi 5
            
            # Setup output pins
            lgpio.gpio_claim_output(self.gpio_chip, self.step_pin, 0)
            lgpio.gpio_claim_output(self.gpio_chip, self.dir_pin, 0)
            
            if self.enable_pin is not None:
                lgpio.gpio_claim_output(self.gpio_chip, self.enable_pin, 1)  # Start disabled (HIGH)
            
            # Setup microstepping pins
            if self.ms1_pin is not None:
                lgpio.gpio_claim_output(self.gpio_chip, self.ms1_pin, 0)
            if self.ms2_pin is not None:
                lgpio.gpio_claim_output(self.gpio_chip, self.ms2_pin, 0)
            if self.ms3_pin is not None:
                lgpio.gpio_claim_output(self.gpio_chip, self.ms3_pin, 0)
        else:
            # Raspberry Pi 4 or earlier using RPi.GPIO
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
        """
        Set microstepping mode for smoother operation.
        
        Args:
            mode: Microstepping mode ('full', '1/2', '1/4', '1/8', '1/16')
        """
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
        
        # Set microstepping pins
        for pin, value in [(self.ms1_pin, ms1), (self.ms2_pin, ms2), (self.ms3_pin, ms3)]:
            if pin is not None:
                if GPIO_LIB == 'lgpio':
                    lgpio.gpio_write(self.gpio_chip, pin, 1 if value else 0)
                else:
                    GPIO.output(pin, GPIO.HIGH if value else GPIO.LOW)
    
    def set_direction(self, clockwise=True):
        """Set rotation direction."""
        if GPIO_LIB == 'lgpio':
            lgpio.gpio_write(self.gpio_chip, self.dir_pin, 1 if clockwise else 0)
        else:
            GPIO.output(self.dir_pin, GPIO.HIGH if clockwise else GPIO.LOW)
    
    def step(self, delay=0.0003):
        """Execute a single step."""
        if GPIO_LIB == 'lgpio':
            lgpio.gpio_write(self.gpio_chip, self.step_pin, 1)
            time.sleep(delay)
            lgpio.gpio_write(self.gpio_chip, self.step_pin, 0)
            time.sleep(delay)
        else:
            GPIO.output(self.step_pin, GPIO.HIGH)
            time.sleep(delay)
            GPIO.output(self.step_pin, GPIO.LOW)
            time.sleep(delay)
    
    def rotate(self, steps, clockwise=True, delay=0.0003):
        """
        Rotate a specific number of steps.
        
        Args:
            steps: Number of steps to rotate
            clockwise: Direction of rotation
            delay: Delay between steps (controls speed)
        """
        self.set_direction(clockwise)
        for _ in range(abs(steps)):
            self.step(delay)
    
    def rotate_degrees(self, degrees, clockwise=True, delay=0.0003, steps_per_rev=200):
        """
        Rotate a specific number of degrees.
        
        Args:
            degrees: Degrees to rotate
            clockwise: Direction of rotation
            delay: Speed of rotation
            steps_per_rev: Steps per revolution for your motor (typically 200)
        """
        steps = int((degrees / 360.0) * steps_per_rev * self.microstep_multiplier)
        self.rotate(steps, clockwise, delay)
    
    def enable(self):
        """Enable the stepper motor driver."""
        if self.enable_pin is not None:
            if GPIO_LIB == 'lgpio':
                lgpio.gpio_write(self.gpio_chip, self.enable_pin, 0)
            else:
                GPIO.output(self.enable_pin, GPIO.LOW)
    
    def disable(self):
        """Disable the stepper motor driver."""
        if self.enable_pin is not None:
            if GPIO_LIB == 'lgpio':
                lgpio.gpio_write(self.gpio_chip, self.enable_pin, 1)
            else:
                GPIO.output(self.enable_pin, GPIO.HIGH)
    
    def cleanup(self):
        """Clean up GPIO resources."""
        if GPIO_LIB == 'lgpio':
            # Free all claimed pins
            for pin in [self.step_pin, self.dir_pin, self.enable_pin, 
                       self.ms1_pin, self.ms2_pin, self.ms3_pin]:
                if pin is not None:
                    try:
                        lgpio.gpio_free(self.gpio_chip, pin)
                    except:
                        pass
            lgpio.gpiochip_close(self.gpio_chip)
        else:
            pins_to_cleanup = [self.step_pin, self.dir_pin]
            if self.enable_pin is not None:
                pins_to_cleanup.append(self.enable_pin)
            GPIO.cleanup(pins_to_cleanup)


if __name__ == "__main__":
    motor = A4988Stepper(step_pin=24, dir_pin=23, enable_pin=25, ms1_pin=17, ms2_pin=22, ms3_pin=27)
    
    try:
        print("Setting all GPIO pins to LOW...")
        if GPIO_LIB == 'lgpio':
            lgpio.gpio_write(motor.gpio_chip, motor.step_pin, 0)
            lgpio.gpio_write(motor.gpio_chip, motor.dir_pin, 0)
            if motor.enable_pin is not None:
                lgpio.gpio_write(motor.gpio_chip, motor.enable_pin, 0)
            if motor.ms1_pin is not None:
                lgpio.gpio_write(motor.gpio_chip, motor.ms1_pin, 0)
            if motor.ms2_pin is not None:
                lgpio.gpio_write(motor.gpio_chip, motor.ms2_pin, 0)
            if motor.ms3_pin is not None:
                lgpio.gpio_write(motor.gpio_chip, motor.ms3_pin, 0)
        else:
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
