import RPi.GPIO as GPIO
import time


class WaterPump:
    """
    Water pump controller using GPIO relay module.
    Controls a 12V DC water pump via relay for fire suppression.
    """
    
    def __init__(self, relay_pin=18):
        """
        Initialize water pump controller.
        
        Args:
            relay_pin: GPIO pin number (BCM mode) connected to relay module
        """
        self.relay_pin = relay_pin
        self.is_running = False
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.relay_pin, GPIO.OUT)
        GPIO.output(self.relay_pin, GPIO.LOW)  
        
        print(f"Water pump initialized on GPIO pin {relay_pin}")
    
    def start(self):
        """Start the water pump"""
        if not self.is_running:
            GPIO.output(self.relay_pin, GPIO.HIGH)
            self.is_running = True
            print("Water pump STARTED")
    
    def stop(self):
        """Stop the water pump"""
        if self.is_running:
            GPIO.output(self.relay_pin, GPIO.LOW)
            self.is_running = False
            print("Water pump STOPPED")
    
    def pulse(self, duration=1.0):
        """
        Run pump for a specific duration then stop.
        
        Args:
            duration: Time in seconds to run the pump
        """
        print(f"Water pump pulsing for {duration}s")
        self.start()
        time.sleep(duration)
        self.stop()
    
    def spray_pattern(self, pulses=3, pulse_duration=0.5, pause_duration=0.3):
        """
        Execute a spray pattern with multiple pulses.
        
        Args:
            pulses: Number of spray pulses
            pulse_duration: Duration of each pulse in seconds
            pause_duration: Pause between pulses in seconds
        """
        print(f"Executing spray pattern: {pulses} pulses")
        for i in range(pulses):
            print(f"  Pulse {i+1}/{pulses}")
            self.pulse(pulse_duration)
            if i < pulses - 1: 
                time.sleep(pause_duration)
    
    def cleanup(self):
        """Clean up GPIO resources"""
        self.stop()
        GPIO.cleanup(self.relay_pin)
        print("Water pump cleanup complete")


if __name__ == "__main__":
    pump = WaterPump(relay_pin=18)
    
    try:
        print("\nTesting water pump...")
        
        print("\n1. Single 2-second pulse")
        pump.pulse(2.0)
        time.sleep(1)
        
        print("\n2. Spray pattern (3 pulses)")
        pump.spray_pattern(pulses=3, pulse_duration=0.5, pause_duration=0.3)
        time.sleep(1)
        
        print("\n3. Continuous run for 3 seconds")
        pump.start()
        time.sleep(3)
        pump.stop()
        
        print("\nTest complete!")
        
    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        pump.cleanup()
