from adafruit_servokit import ServoKit
import board
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo
import time


class PCA9685ServoController:
    """
    PCA9685 16-Channel PWM Servo Controller.
    
    Controls up to 16 servo motors using I2C communication.
    Supports both ServoKit and manual PCA9685 control methods.
    """
    
    def __init__(self, channels=16, i2c_address=0x40, frequency=50):
        """
        Initialize PCA9685 servo controller.
        
        Args:
            channels: Number of channels (default: 16)
            i2c_address: I2C address of PCA9685 (default: 0x40)
            frequency: PWM frequency in Hz (default: 50 for servos)
        """
        try:
            self.kit = ServoKit(channels=channels, address=i2c_address, frequency=frequency)
            self.channels = channels
            self.using_servokit = True
            print(f"PCA9685 initialized with ServoKit on I2C address 0x{i2c_address:02X}")
        except Exception as e:
            print(f"ServoKit initialization failed: {e}")
            print("Trying alternative method...")
            
            try:
                i2c = busio.I2C(board.SCL, board.SDA)
                self.pca = PCA9685(i2c, address=i2c_address)
                self.pca.frequency = frequency
                self.channels = channels
                self.servos = {}
                self.using_servokit = False
                print(f"PCA9685 initialized manually on I2C address 0x{i2c_address:02X}")
            except Exception as e2:
                raise RuntimeError(f"Failed to initialize PCA9685: {e2}")
    
    
    def set_angle(self, channel, angle):
        """
        Set servo angle.
        
        Args:
            channel: Servo channel (0-15)
            angle: Target angle (0-180 degrees)
        """
        if channel >= self.channels:
            raise ValueError(f"Channel {channel} out of range (0-{self.channels-1})")
        
        # Clamp angle to valid range
        angle = max(0, min(180, angle))
        
        if self.using_servokit:
            self.kit.servo[channel].angle = angle
        else:
            if channel not in self.servos:
                self.servos[channel] = servo.Servo(self.pca.channels[channel])
            self.servos[channel].angle = angle
    
    def set_pulse_width(self, channel, pulse_width_us):
        if channel >= self.channels:
            raise ValueError(f"Channel {channel} out of range (0-{self.channels-1})")
        
        if self.using_servokit:
            pulse_width_us = max(500, min(2500, pulse_width_us))
            duty_cycle = int((pulse_width_us / 20000.0) * 0xFFFF)
            self.kit._pca.channels[channel].duty_cycle = duty_cycle
        else:
            if channel not in self.servos:
                self.servos[channel] = servo.Servo(self.pca.channels[channel])
            angle = ((pulse_width_us - 500) / 2000.0) * 180
            self.servos[channel].angle = max(0, min(180, angle))
    
    def set_actuation_range(self, channel, min_pulse=500, max_pulse=2500):
        if channel >= self.channels:
            raise ValueError(f"Channel {channel} out of range (0-{self.channels-1})")
        
        if self.using_servokit:
            self.kit.servo[channel].actuation_range = 180
            self.kit.servo[channel].set_pulse_width_range(min_pulse, max_pulse)
        else:
            if channel not in self.servos:
                self.servos[channel] = servo.Servo(
                    self.pca.channels[channel],
                    min_pulse=min_pulse,
                    max_pulse=max_pulse
                )
    
    def sweep(self, channel, start_angle=0, end_angle=180, step=1, delay=0.01):
        if start_angle < end_angle:
            for angle in range(int(start_angle), int(end_angle) + 1, step):
                self.set_angle(channel, angle)
                time.sleep(delay)
        else:
            for angle in range(int(start_angle), int(end_angle) - 1, -step):
                self.set_angle(channel, angle)
                time.sleep(delay)
    
    
    def center(self, channel):
        """Center servo to 90 degrees."""
        self.set_angle(channel, 90)
    
    def disable(self, channel):
        """Disable PWM signal on channel."""
        if self.using_servokit:
            self.kit._pca.channels[channel].duty_cycle = 0
        else:
            self.pca.channels[channel].duty_cycle = 0
    
    def disable_all(self):
        """Disable all servo channels."""
        for channel in range(self.channels):
            self.disable(channel)
    
    def deinit(self):
        """Deinitialize controller and release resources."""
        self.disable_all()
        if not self.using_servokit and hasattr(self, 'pca'):
            self.pca.deinit()


class MultiServoController:
    
    def __init__(self, channels=16, i2c_address=0x40):
        self.controller = PCA9685ServoController(channels=channels, i2c_address=i2c_address)
        self.servo_positions = {}
    
    def add_servo(self, name, channel, min_angle=0, max_angle=180):
        self.servo_positions[name] = {
            'channel': channel,
            'min_angle': min_angle,
            'max_angle': max_angle,
            'current_angle': 90
        }
    
    def move(self, name, angle):
        if name not in self.servo_positions:
            raise ValueError(f"Servo '{name}' not registered")
        
        servo_info = self.servo_positions[name]
        angle = max(servo_info['min_angle'], min(servo_info['max_angle'], angle))
        
        self.controller.set_angle(servo_info['channel'], angle)
        servo_info['current_angle'] = angle
    
    def get_angle(self, name):
        if name not in self.servo_positions:
            raise ValueError(f"Servo '{name}' not registered")
        return self.servo_positions[name]['current_angle']
    
    def center_all(self):
        for name in self.servo_positions:
            self.move(name, 90)
    
    def cleanup(self):
        self.controller.deinit()


if __name__ == "__main__":
    servo_controller = PCA9685ServoController(channels=16)
    
    try:
        print("Testing servos on channels 0-3...\n")
        
        for channel in range(4):
            print(f"\n=== Testing Channel {channel} ===")
            
            print("Moving to center (90°)")
            servo_controller.set_angle(channel, 90)
            time.sleep(1)
            
            print("Moving to 0°")
            servo_controller.set_angle(channel, 0)
            time.sleep(1)
            
            print("Moving to 180°")
            servo_controller.set_angle(channel, 180)
            time.sleep(1)
            
            print("Sweeping from 0 to 180")
            servo_controller.sweep(channel, 0, 180, step=5, delay=0.02)
            time.sleep(0.5)
            
            print("Sweeping from 180 to 0")
            servo_controller.sweep(channel, 180, 0, step=5, delay=0.02)
            
            servo_controller.center(channel)
            time.sleep(1)
            
            print(f"Channel {channel} test complete")
        
        print("\nAll tests complete!")
        
    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        servo_controller.disable_all()
        servo_controller.deinit()
        print("Servos disabled and cleaned up")
