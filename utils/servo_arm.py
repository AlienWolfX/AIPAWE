"""
AIPAWE - Servo Arm Controller
Controls elbow and wrist servos via PCA9685 PWM driver for precise aiming
"""

import time
from typing import Tuple
try:
    from adafruit_pca9685 import PCA9685
    from board import SCL, SDA
    import busio
except ImportError:
    # Mock for development
    class PCA9685:
        def __init__(self, i2c, address=0x40):
            self.frequency = 50
            self.channels = [type('obj', (object,), {'duty_cycle': 0})() for _ in range(16)]
    
    class MockBusio:
        @staticmethod
        def I2C(scl, sda): return None
    
    busio = MockBusio()
    SCL = SDA = None

from utils.utils_common import clamp, map_range


class ServoArm:
    """PCA9685-based servo arm controller for elbow and wrist"""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        
        # Initialize PCA9685
        i2c_address = config.get('servo', 'i2c_address', default=0x40)
        try:
            i2c = busio.I2C(SCL, SDA)
            self.pca = PCA9685(i2c, address=i2c_address)
            self.pca.frequency = config.get('servo', 'frequency', default=50)
        except:
            self.pca = PCA9685(None, address=i2c_address)
        
        # Elbow servo config
        self.elbow_channel = config.get('servo', 'elbow', 'channel')
        self.elbow_min_pulse = config.get('servo', 'elbow', 'min_pulse')
        self.elbow_max_pulse = config.get('servo', 'elbow', 'max_pulse')
        self.elbow_min_angle = config.get('servo', 'elbow', 'min_angle')
        self.elbow_max_angle = config.get('servo', 'elbow', 'max_angle')
        self.elbow_neutral = config.get('servo', 'elbow', 'neutral_angle')
        
        # Wrist servo config
        self.wrist_channel = config.get('servo', 'wrist', 'channel')
        self.wrist_min_pulse = config.get('servo', 'wrist', 'min_pulse')
        self.wrist_max_pulse = config.get('servo', 'wrist', 'max_pulse')
        self.wrist_min_angle = config.get('servo', 'wrist', 'min_angle')
        self.wrist_max_angle = config.get('servo', 'wrist', 'max_angle')
        self.wrist_neutral = config.get('servo', 'wrist', 'neutral_angle')
        
        # Current positions
        self.elbow_angle = self.elbow_neutral
        self.wrist_angle = self.wrist_neutral
        
        # Move to neutral
        self.move_to_neutral()
        
        self.logger.info("ServoArm initialized at neutral position")
    
    def _angle_to_duty_cycle(self, angle: float, min_pulse: int, max_pulse: int,
                            min_angle: float, max_angle: float) -> int:
        """Convert angle to PWM duty cycle"""
        # Clamp angle
        angle = clamp(angle, min_angle, max_angle)
        
        # Map angle to pulse width
        pulse_width = map_range(angle, min_angle, max_angle, min_pulse, max_pulse)
        
        # Convert pulse width (microseconds) to duty cycle (0-65535)
        # At 50Hz, period is 20ms = 20000μs
        duty_cycle = int((pulse_width / 20000.0) * 65535)
        
        return duty_cycle
    
    def set_elbow_angle(self, angle: float, smooth: bool = False):
        """Set elbow servo angle"""
        angle = clamp(angle, self.elbow_min_angle, self.elbow_max_angle)
        
        if smooth:
            self._smooth_move(
                self.elbow_angle, angle,
                lambda a: self._set_elbow_immediate(a)
            )
        else:
            self._set_elbow_immediate(angle)
        
        self.logger.log_hardware_action("ServoArm", "ELBOW", f"{angle:.1f}°")
    
    def _set_elbow_immediate(self, angle: float):
        """Set elbow immediately without smoothing"""
        duty = self._angle_to_duty_cycle(
            angle, self.elbow_min_pulse, self.elbow_max_pulse,
            self.elbow_min_angle, self.elbow_max_angle
        )
        self.pca.channels[self.elbow_channel].duty_cycle = duty
        self.elbow_angle = angle
    
    def set_wrist_angle(self, angle: float, smooth: bool = False):
        """Set wrist servo angle"""
        angle = clamp(angle, self.wrist_min_angle, self.wrist_max_angle)
        
        if smooth:
            self._smooth_move(
                self.wrist_angle, angle,
                lambda a: self._set_wrist_immediate(a)
            )
        else:
            self._set_wrist_immediate(angle)
        
        self.logger.log_hardware_action("ServoArm", "WRIST", f"{angle:.1f}°")
    
    def _set_wrist_immediate(self, angle: float):
        """Set wrist immediately without smoothing"""
        duty = self._angle_to_duty_cycle(
            angle, self.wrist_min_pulse, self.wrist_max_pulse,
            self.wrist_min_angle, self.wrist_max_angle
        )
        self.pca.channels[self.wrist_channel].duty_cycle = duty
        self.wrist_angle = angle
    
    def _smooth_move(self, start: float, end: float, set_func, steps: int = 20):
        """Smooth movement between angles"""
        for i in range(steps + 1):
            progress = i / steps
            angle = start + (end - start) * progress
            set_func(angle)
            time.sleep(0.02)  # 20ms delay between steps
    
    def aim_at_target(self, azimuth: float, elevation: float, smooth: bool = True):
        """
        Aim arm at target coordinates
        
        Args:
            azimuth: Horizontal angle (handled by stepper base)
            elevation: Vertical angle (mapped to elbow/wrist)
            smooth: Use smooth movement
        """
        # Simple inverse kinematics - distribute elevation between elbow and wrist
        # This is a simplified model; adjust based on actual arm geometry
        elbow_target = self.elbow_neutral - (elevation * 0.6)
        wrist_target = self.wrist_neutral - (elevation * 0.4)
        
        # Clamp to safe limits
        elbow_target = clamp(elbow_target, self.elbow_min_angle, self.elbow_max_angle)
        wrist_target = clamp(wrist_target, self.wrist_min_angle, self.wrist_max_angle)
        
        self.set_elbow_angle(elbow_target, smooth)
        self.set_wrist_angle(wrist_target, smooth)
        
        self.logger.log_hardware_action(
            "ServoArm", "AIM",
            f"Elevation {elevation:.1f}° (E:{elbow_target:.1f}° W:{wrist_target:.1f}°)"
        )
    
    def move_to_neutral(self):
        """Return arm to neutral ceiling-mounted position"""
        self._set_elbow_immediate(self.elbow_neutral)
        self._set_wrist_immediate(self.wrist_neutral)
        self.logger.log_hardware_action("ServoArm", "NEUTRAL")
    
    def get_current_position(self) -> Tuple[float, float]:
        """Get current elbow and wrist angles"""
        return (self.elbow_angle, self.wrist_angle)
    
    def cleanup(self):
        """Cleanup - return to neutral and deinitialize"""
        self.move_to_neutral()
        try:
            self.pca.deinit()
        except:
            pass
