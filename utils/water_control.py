"""
AIPAWE - Water Pump Controller
Relay-controlled water pump for fire suppression
"""

import time
import threading
from utils.gpio_adapter import gpio as GPIO


class WaterPump:
    """Relay-controlled water pump for fire suppression"""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        
        # Relay configuration
        self.relay_pin = config.get('water', 'relay_pin')
        self.spray_duration = config.get('water', 'spray_duration', default=3)
        self.max_attempts = config.get('water', 'max_attempts', default=3)
        self.cooldown = config.get('water', 'cooldown', default=1)
        
        # State
        self.is_spraying = False
        self.spray_thread = None
        self.stop_spray = threading.Event()
        
        # Initialize GPIO
        self._init_gpio()
        
        self.logger.info(f"WaterPump initialized on GPIO {self.relay_pin}")
    
    def _init_gpio(self):
        """Initialize relay GPIO pin"""
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.relay_pin, GPIO.OUT)
        
        # Ensure pump is off initially (relay LOW = off)
        GPIO.output(self.relay_pin, GPIO.LOW)
    
    def start_spray(self, duration: float = None, blocking: bool = True) -> bool:
        """
        Start water spray
        
        Args:
            duration: Override default spray duration
            blocking: If True, wait for spray to complete
            
        Returns:
            True if spray started successfully
        """
        if self.is_spraying:
            self.logger.warning("Pump already spraying")
            return False
        
        spray_time = duration if duration is not None else self.spray_duration
        
        self.logger.log_hardware_action(
            "WaterPump", "SPRAY_START",
            f"{spray_time}s duration"
        )
        
        if blocking:
            self._spray_sequence(spray_time)
        else:
            self.is_spraying = True
            self.stop_spray.clear()
            self.spray_thread = threading.Thread(
                target=self._spray_sequence,
                args=(spray_time,),
                daemon=True
            )
            self.spray_thread.start()
        
        return True
    
    def _spray_sequence(self, duration: float):
        """Internal spray sequence"""
        try:
            # Activate relay (HIGH = on)
            GPIO.output(self.relay_pin, GPIO.HIGH)
            self.is_spraying = True
            
            # Spray for specified duration
            start_time = time.time()
            while time.time() - start_time < duration:
                if self.stop_spray.is_set():
                    break
                time.sleep(0.1)
            
            # Deactivate relay (LOW = off)
            GPIO.output(self.relay_pin, GPIO.LOW)
            self.is_spraying = False
            
            self.logger.log_hardware_action("WaterPump", "SPRAY_STOP")
            
            # Cooldown period
            if not self.stop_spray.is_set():
                time.sleep(self.cooldown)
                
        except Exception as e:
            self.logger.error(f"Water pump error: {e}")
            GPIO.output(self.relay_pin, GPIO.LOW)  # Ensure pump is off
            self.is_spraying = False
    
    def stop(self):
        """Emergency stop of water pump"""
        if self.is_spraying:
            self.stop_spray.set()
            if self.spray_thread:
                self.spray_thread.join(timeout=1.0)
            GPIO.output(self.relay_pin, GPIO.LOW)
            self.is_spraying = False
            self.logger.log_hardware_action("WaterPump", "EMERGENCY_STOP")
    
    def pulse_spray(self, pulses: int = 3, pulse_duration: float = 1.0, 
                    pulse_interval: float = 0.5):
        """
        Execute pulsed spray pattern
        
        Args:
            pulses: Number of spray pulses
            pulse_duration: Duration of each pulse
            pulse_interval: Delay between pulses
        """
        self.logger.log_hardware_action(
            "WaterPump", "PULSE_SPRAY",
            f"{pulses} pulses × {pulse_duration}s"
        )
        
        for i in range(pulses):
            if self.stop_spray.is_set():
                break
            
            GPIO.output(self.relay_pin, GPIO.HIGH)
            time.sleep(pulse_duration)
            GPIO.output(self.relay_pin, GPIO.LOW)
            
            if i < pulses - 1:  # Don't delay after last pulse
                time.sleep(pulse_interval)
        
        self.logger.log_hardware_action("WaterPump", "PULSE_COMPLETE")
    
    def is_active(self) -> bool:
        """Check if pump is currently spraying"""
        return self.is_spraying
    
    def wait_for_completion(self, timeout: float = None):
        """Wait for spray to complete"""
        if self.spray_thread and self.spray_thread.is_alive():
            self.spray_thread.join(timeout=timeout)
    
    def cleanup(self):
        """Cleanup GPIO resources"""
        self.stop()
        GPIO.cleanup([self.relay_pin])
