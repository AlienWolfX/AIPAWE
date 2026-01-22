"""
AIPAWE - Stepper Motor Base Controller
Controls NEMA17 stepper motor via A4988 driver for 360° base rotation
"""

import time
import threading
from typing import Optional
from utils.gpio_adapter import gpio as GPIO


class StepperBase:
    """NEMA17 stepper motor controller for base rotation"""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        
        # GPIO pins
        self.step_pin = config.get('stepper', 'step_pin')
        self.dir_pin = config.get('stepper', 'dir_pin')
        self.enable_pin = config.get('stepper', 'enable_pin')
        
        # Motor parameters
        self.steps_per_rev = config.get('stepper', 'steps_per_revolution', default=200)
        self.microsteps = config.get('stepper', 'microsteps', default=16)
        self.total_steps = self.steps_per_rev * self.microsteps
        self.rpm = config.get('stepper', 'rpm', default=10)
        
        # State
        self.current_angle = 0.0
        self.is_enabled = False
        self.is_scanning = False
        self.scan_thread: Optional[threading.Thread] = None
        self.stop_scan = threading.Event()
        
        # Initialize GPIO
        self._init_gpio()
        
        self.logger.info(f"StepperBase initialized: {self.total_steps} steps/rev, {self.rpm} RPM")
    
    def _init_gpio(self):
        """Initialize GPIO pins"""
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.step_pin, GPIO.OUT)
        GPIO.setup(self.dir_pin, GPIO.OUT)
        GPIO.setup(self.enable_pin, GPIO.OUT)
        
        # Disable motor initially
        GPIO.output(self.enable_pin, GPIO.HIGH)
    
    def enable(self):
        """Enable stepper motor"""
        GPIO.output(self.enable_pin, GPIO.LOW)
        self.is_enabled = True
        self.logger.log_hardware_action("StepperBase", "ENABLED")
    
    def disable(self):
        """Disable stepper motor"""
        GPIO.output(self.enable_pin, GPIO.HIGH)
        self.is_enabled = False
        self.logger.log_hardware_action("StepperBase", "DISABLED")
    
    def _calculate_delay(self) -> float:
        """Calculate delay between steps based on RPM"""
        steps_per_second = (self.rpm / 60.0) * self.total_steps
        return 1.0 / steps_per_second / 2.0  # Divide by 2 for HIGH/LOW toggle
    
    def step(self, steps: int, clockwise: bool = True):
        """Execute specified number of steps"""
        if not self.is_enabled:
            self.enable()
        
        # Set direction
        GPIO.output(self.dir_pin, GPIO.HIGH if clockwise else GPIO.LOW)
        
        delay = self._calculate_delay()
        
        for _ in range(abs(steps)):
            GPIO.output(self.step_pin, GPIO.HIGH)
            time.sleep(delay)
            GPIO.output(self.step_pin, GPIO.LOW)
            time.sleep(delay)
        
        # Update angle
        degrees = (steps / self.total_steps) * 360
        self.current_angle = (self.current_angle + degrees) % 360
    
    def rotate_to_angle(self, target_angle: float):
        """Rotate to specific angle (0-360)"""
        target_angle = target_angle % 360
        
        # Calculate shortest path
        diff = (target_angle - self.current_angle) % 360
        if diff > 180:
            diff -= 360
        
        steps = int((abs(diff) / 360) * self.total_steps)
        clockwise = diff >= 0
        
        self.logger.log_hardware_action(
            "StepperBase", 
            "ROTATE", 
            f"{self.current_angle:.1f}° → {target_angle:.1f}° ({steps} steps)"
        )
        
        self.step(steps, clockwise)
    
    def start_continuous_scan(self):
        """Start continuous 360° scanning in background thread"""
        if self.is_scanning:
            return
        
        self.is_scanning = True
        self.stop_scan.clear()
        self.scan_thread = threading.Thread(target=self._scan_loop, daemon=True)
        self.scan_thread.start()
        
        self.logger.log_hardware_action("StepperBase", "SCAN_START", f"{self.rpm} RPM")
    
    def _scan_loop(self):
        """Continuous scanning loop"""
        sector_size = self.config.get('stepper', 'sector_size', default=15)
        
        while not self.stop_scan.is_set():
            # Rotate by one sector
            steps_per_sector = int((sector_size / 360) * self.total_steps)
            
            if not self.is_enabled:
                self.enable()
            
            GPIO.output(self.dir_pin, GPIO.HIGH)  # Clockwise
            delay = self._calculate_delay()
            
            for _ in range(steps_per_sector):
                if self.stop_scan.is_set():
                    break
                GPIO.output(self.step_pin, GPIO.HIGH)
                time.sleep(delay)
                GPIO.output(self.step_pin, GPIO.LOW)
                time.sleep(delay)
            
            # Update angle
            self.current_angle = (self.current_angle + sector_size) % 360
    
    def stop_scanning(self):
        """Stop continuous scanning"""
        if self.is_scanning:
            self.stop_scan.set()
            if self.scan_thread:
                self.scan_thread.join(timeout=2.0)
            self.is_scanning = False
            self.logger.log_hardware_action("StepperBase", "SCAN_STOP")
    
    def get_current_angle(self) -> float:
        """Get current base angle"""
        return self.current_angle
    
    def cleanup(self):
        """Cleanup GPIO resources"""
        self.stop_scanning()
        self.disable()
        GPIO.cleanup([self.step_pin, self.dir_pin, self.enable_pin])
