"""
AIPAWE - GPIO Adapter
Abstraction layer supporting both RPi.GPIO (Pi 1-4) and lgpio (Pi 5)
"""

import platform
import time

# Detect which GPIO library to use
GPIO_LIB = None
gpio_chip = None

try:
    # Try lgpio first (for Raspberry Pi 5)
    import lgpio
    GPIO_LIB = 'lgpio'
    # Open GPIO chip (typically /dev/gpiochip4 on Pi 5)
    try:
        gpio_chip = lgpio.gpiochip_open(4)  # Pi 5 uses gpiochip4
    except:
        try:
            gpio_chip = lgpio.gpiochip_open(0)  # Fallback to gpiochip0
        except:
            pass
except ImportError:
    try:
        # Fall back to RPi.GPIO (for Pi 1-4)
        import RPi.GPIO as GPIO
        GPIO_LIB = 'RPi.GPIO'
    except ImportError:
        # Neither available - use mock
        GPIO_LIB = 'mock'


class GPIOAdapter:
    """
    Unified GPIO interface supporting both RPi.GPIO and lgpio
    """
    
    # Mode constants
    BCM = "BCM"
    BOARD = "BOARD"
    
    # Pin direction constants
    IN = "IN"
    OUT = "OUT"
    
    # Pin state constants
    HIGH = 1
    LOW = 0
    
    # Pull up/down constants
    PUD_OFF = 0
    PUD_DOWN = 1
    PUD_UP = 2
    
    def __init__(self):
        self.lib = GPIO_LIB
        self.mode_set = False
        self.setup_pins = set()
        
    def get_library_name(self):
        """Get the name of the GPIO library being used"""
        return self.lib
    
    def setmode(self, mode):
        """Set pin numbering mode"""
        if self.lib == 'RPi.GPIO':
            GPIO.setmode(GPIO.BCM if mode == self.BCM else GPIO.BOARD)
        # lgpio always uses BCM numbering
        self.mode_set = True
    
    def setup(self, pin, direction, pull_up_down=PUD_OFF, initial=LOW):
        """Setup a GPIO pin"""
        if self.lib == 'RPi.GPIO':
            pud_map = {
                self.PUD_OFF: GPIO.PUD_OFF,
                self.PUD_DOWN: GPIO.PUD_DOWN,
                self.PUD_UP: GPIO.PUD_UP
            }
            GPIO.setup(pin, GPIO.OUT if direction == self.OUT else GPIO.IN,
                      pull_up_down=pud_map.get(pull_up_down, GPIO.PUD_OFF))
            if direction == self.OUT and initial is not None:
                GPIO.output(pin, initial)
                
        elif self.lib == 'lgpio':
            if gpio_chip is not None:
                if direction == self.OUT:
                    lgpio.gpio_claim_output(gpio_chip, pin, initial)
                else:
                    # Input mode
                    flags = 0
                    if pull_up_down == self.PUD_UP:
                        flags = lgpio.SET_PULL_UP
                    elif pull_up_down == self.PUD_DOWN:
                        flags = lgpio.SET_PULL_DOWN
                    lgpio.gpio_claim_input(gpio_chip, pin, flags)
        
        self.setup_pins.add(pin)
    
    def output(self, pin, state):
        """Set output state of a GPIO pin"""
        if self.lib == 'RPi.GPIO':
            GPIO.output(pin, state)
        elif self.lib == 'lgpio':
            if gpio_chip is not None:
                lgpio.gpio_write(gpio_chip, pin, state)
    
    def input(self, pin):
        """Read input state of a GPIO pin"""
        if self.lib == 'RPi.GPIO':
            return GPIO.input(pin)
        elif self.lib == 'lgpio':
            if gpio_chip is not None:
                return lgpio.gpio_read(gpio_chip, pin)
        return 0
    
    def cleanup(self, pins=None):
        """Cleanup GPIO pins"""
        if self.lib == 'RPi.GPIO':
            if pins is None:
                GPIO.cleanup()
            else:
                GPIO.cleanup(pins)
        elif self.lib == 'lgpio':
            if gpio_chip is not None:
                # Free claimed pins
                pins_to_free = pins if pins is not None else list(self.setup_pins)
                if isinstance(pins_to_free, int):
                    pins_to_free = [pins_to_free]
                for pin in pins_to_free:
                    try:
                        lgpio.gpio_free(gpio_chip, pin)
                    except:
                        pass
                
                # If cleaning up all, close chip
                if pins is None:
                    try:
                        lgpio.gpiochip_close(gpio_chip)
                    except:
                        pass
        
        if pins is None:
            self.setup_pins.clear()
        else:
            if isinstance(pins, int):
                pins = [pins]
            for pin in pins:
                self.setup_pins.discard(pin)
    
    def pwm(self, pin, frequency):
        """
        Create PWM instance
        Note: This is a simple software PWM implementation for lgpio
        """
        if self.lib == 'RPi.GPIO':
            return GPIO.PWM(pin, frequency)
        elif self.lib == 'lgpio':
            # Return a software PWM wrapper for lgpio
            return LgpioPWM(pin, frequency, gpio_chip)
        else:
            return MockPWM(pin, frequency)
    
    def add_event_detect(self, pin, edge, callback=None, bouncetime=None):
        """Add event detection"""
        if self.lib == 'RPi.GPIO':
            edge_map = {
                'RISING': GPIO.RISING,
                'FALLING': GPIO.FALLING,
                'BOTH': GPIO.BOTH
            }
            if bouncetime:
                GPIO.add_event_detect(pin, edge_map.get(edge, GPIO.BOTH),
                                    callback=callback, bouncetime=bouncetime)
            else:
                GPIO.add_event_detect(pin, edge_map.get(edge, GPIO.BOTH),
                                    callback=callback)
        elif self.lib == 'lgpio':
            # lgpio event detection is different - would need callback wrapper
            pass
    
    def remove_event_detect(self, pin):
        """Remove event detection"""
        if self.lib == 'RPi.GPIO':
            GPIO.remove_event_detect(pin)


class LgpioPWM:
    """Software PWM implementation for lgpio"""
    
    def __init__(self, pin, frequency, chip):
        self.pin = pin
        self.frequency = frequency
        self.chip = chip
        self.duty_cycle = 0
        self.running = False
        self._thread = None
    
    def start(self, duty_cycle):
        """Start PWM with given duty cycle"""
        self.duty_cycle = duty_cycle
        self.running = True
        # Note: For production, implement proper threading PWM
        # For now, just set the pin state based on duty cycle
        if self.chip is not None:
            if duty_cycle > 50:
                lgpio.gpio_write(self.chip, self.pin, 1)
            else:
                lgpio.gpio_write(self.chip, self.pin, 0)
    
    def ChangeDutyCycle(self, duty_cycle):
        """Change PWM duty cycle"""
        self.duty_cycle = duty_cycle
        if self.chip is not None and self.running:
            if duty_cycle > 50:
                lgpio.gpio_write(self.chip, self.pin, 1)
            else:
                lgpio.gpio_write(self.chip, self.pin, 0)
    
    def stop(self):
        """Stop PWM"""
        self.running = False
        if self.chip is not None:
            lgpio.gpio_write(self.chip, self.pin, 0)


class MockPWM:
    """Mock PWM for development"""
    def __init__(self, pin, frequency):
        self.pin = pin
        self.frequency = frequency
        self.duty_cycle = 0
    
    def start(self, duty_cycle):
        self.duty_cycle = duty_cycle
    
    def ChangeDutyCycle(self, duty_cycle):
        self.duty_cycle = duty_cycle
    
    def stop(self):
        pass


# Create global instance
gpio = GPIOAdapter()
