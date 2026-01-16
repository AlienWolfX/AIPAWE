from utils.servo import PCA9685ServoController
from utils.stepper import A4988Stepper
import time


class RobotArm:
    """
    Robot arm controller for fire-fighting robot.
    
    Mechanical structure:
    - Shoulder base: Stepper motor (7-inch tube rotation)
    - Elbow joint: 2 servo motors (arm movement)
    - Wrist joint: 2 servo motors (speaker and camera tilt control)
    """
    
    def __init__(self):
        """Initialize robot arm with stepper and servo controllers"""
        
        self.stepper = A4988Stepper(
            step_pin=24, 
            dir_pin=23, 
            enable_pin=25,
            ms1_pin=17, 
            ms2_pin=22, 
            ms3_pin=27
        )
        self.stepper.set_microstepping('1/16') 
        self.stepper.enable()
        
        self.servo_controller = PCA9685ServoController(channels=16)
        
        self.ELBOW_SERVO_1 = 0  
        self.ELBOW_SERVO_2 = 1  
        self.WRIST_SERVO_1 = 2  
        self.WRIST_SERVO_2 = 3  
        
        self.shoulder_angle = 0  
        self.elbow_angle_1 = 90
        self.elbow_angle_2 = 90
        self.wrist_angle_1 = 90
        self.wrist_angle_2 = 90
        
        print("Robot arm initialized")
        self.home_position()
    
    def home_position(self):
        """Move all joints to home/neutral position"""
        print("Moving to home position...")
        self.servo_controller.center(self.ELBOW_SERVO_1)
        self.servo_controller.center(self.ELBOW_SERVO_2)
        self.servo_controller.center(self.WRIST_SERVO_1)
        self.servo_controller.center(self.WRIST_SERVO_2)
        
        self.shoulder_angle = 0
        self.elbow_angle_1 = 90
        self.elbow_angle_2 = 90
        self.wrist_angle_1 = 90
        self.wrist_angle_2 = 90
        
        time.sleep(1)
        print("Home position reached")
    
    def rotate_shoulder(self, degrees, clockwise=True, speed=0.015):
        """
        Rotate shoulder base using stepper motor.
        
        Args:
            degrees: Degrees to rotate
            clockwise: Direction of rotation
            speed: Rotation speed (delay between steps)
        """
        print(f"Rotating shoulder {degrees}° {'CW' if clockwise else 'CCW'}")
        self.stepper.rotate_degrees(degrees, clockwise=clockwise, delay=speed)
        
        if clockwise:
            self.shoulder_angle = (self.shoulder_angle + degrees) % 360
        else:
            self.shoulder_angle = (self.shoulder_angle - degrees) % 360
    
    def rotate_360_scan(self, speed=0.02, stop_callback=None):
        """
        Perform a full 360° rotation for scanning.
        
        Args:
            speed: Rotation speed
            stop_callback: Function that returns True to stop scanning
        """
        print("Starting 360° scan...")
        steps_per_degree = 200 * 16 / 360  
        total_steps = int(360 * steps_per_degree)
        
        self.stepper.set_direction(clockwise=True)
        
        for step in range(total_steps):
            if stop_callback and stop_callback():
                print("Scan interrupted - fire detected!")
                return True  
            
            self.stepper.step(delay=speed)
            
            if step % 10 == 0:
                self.shoulder_angle = (step / steps_per_degree) % 360
        
        self.shoulder_angle = 0
        print("360° scan complete")
        return False  
    
    def set_elbow_position(self, angle1, angle2=None):
        """
        Set elbow joint position.
        
        Args:
            angle1: Angle for elbow servo 1 (0-180)
            angle2: Angle for elbow servo 2 (0-180), defaults to angle1
        """
        if angle2 is None:
            angle2 = angle1
        
        self.servo_controller.set_angle(self.ELBOW_SERVO_1, angle1)
        self.servo_controller.set_angle(self.ELBOW_SERVO_2, angle2)
        
        self.elbow_angle_1 = angle1
        self.elbow_angle_2 = angle2
        
        print(f"Elbow position: [{angle1}°, {angle2}°]")
    
    def set_wrist_position(self, camera_angle, speaker_angle=None):
        """
        Set wrist tilt for camera and speaker.
        
        Args:
            camera_angle: Tilt angle for camera (0-180)
            speaker_angle: Tilt angle for speaker (0-180), defaults to camera_angle
        """
        if speaker_angle is None:
            speaker_angle = camera_angle
        
        self.servo_controller.set_angle(self.WRIST_SERVO_1, camera_angle)
        self.servo_controller.set_angle(self.WRIST_SERVO_2, speaker_angle)
        
        self.wrist_angle_1 = camera_angle
        self.wrist_angle_2 = speaker_angle
        
        print(f"Wrist position: Camera={camera_angle}°, Speaker={speaker_angle}°")
    
    def point_at_target(self, shoulder_angle, elbow_angle, wrist_angle):
        """
        Point the arm at a specific target.
        
        Args:
            shoulder_angle: Target shoulder rotation (degrees from current)
            elbow_angle: Target elbow angle (0-180)
            wrist_angle: Target wrist angle (0-180)
        """
        print(f"Pointing at target: Shoulder={shoulder_angle}°, Elbow={elbow_angle}°, Wrist={wrist_angle}°")
        
        angle_diff = shoulder_angle - self.shoulder_angle
        if angle_diff != 0:
            clockwise = angle_diff > 0
            self.rotate_shoulder(abs(angle_diff), clockwise=clockwise)
            time.sleep(0.5)
        
        self.set_elbow_position(elbow_angle)
        time.sleep(0.3)
        
        self.set_wrist_position(wrist_angle)
        time.sleep(0.3)
        
        print("Target acquired")
    
    def sweep_area(self, start_angle, end_angle, step=5):
        """
        Sweep the arm across an area.
        
        Args:
            start_angle: Starting shoulder angle
            end_angle: Ending shoulder angle
            step: Step size in degrees
        """
        current = self.shoulder_angle
        target = start_angle
        
        diff = target - current
        if diff != 0:
            self.rotate_shoulder(abs(diff), clockwise=(diff > 0))
        
        total_sweep = abs(end_angle - start_angle)
        direction = end_angle > start_angle
        
        print(f"Sweeping from {start_angle}° to {end_angle}°")
        for _ in range(0, int(total_sweep), step):
            self.rotate_shoulder(step, clockwise=direction, speed=0.02)
            time.sleep(0.1)
    
    def cleanup(self):
        """Clean up resources"""
        print("Cleaning up robot arm...")
        self.home_position()
        self.servo_controller.disable_all()
        self.servo_controller.deinit()
        self.stepper.disable()
        self.stepper.cleanup()
        print("Robot arm cleanup complete")


if __name__ == "__main__":
    arm = RobotArm()
    
    try:
        print("\n=== Testing Robot Arm ===")
        
        print("\n1. Home position")
        arm.home_position()
        time.sleep(2)
        
        print("\n2. Elbow movement test")
        arm.set_elbow_position(45)
        time.sleep(1)
        arm.set_elbow_position(135)
        time.sleep(1)
        arm.set_elbow_position(90)
        time.sleep(1)
        
        print("\n3. Wrist tilt test")
        arm.set_wrist_position(camera_angle=45, speaker_angle=50)
        time.sleep(1)
        arm.set_wrist_position(camera_angle=135, speaker_angle=130)
        time.sleep(1)
        arm.set_wrist_position(camera_angle=90, speaker_angle=90)
        time.sleep(1)
        
        print("\n4. Shoulder rotation test (90°)")
        arm.rotate_shoulder(90, clockwise=True)
        time.sleep(1)
        arm.rotate_shoulder(90, clockwise=False)
        time.sleep(1)
        
        print("\n5. Point at target test")
        arm.point_at_target(shoulder_angle=45, elbow_angle=60, wrist_angle=45)
        time.sleep(2)
        arm.home_position()
        time.sleep(1)
        
        print("\n6. Area sweep test")
        arm.sweep_area(start_angle=0, end_angle=90, step=10)
        time.sleep(1)
        arm.home_position()
        
        print("\nTests complete!")
        
    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        arm.cleanup()
