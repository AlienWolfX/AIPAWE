from pathlib import Path
from typing import Optional
import cv2
import torch
from ultralytics import YOLO
import time
import numpy as np

from utils.sim800l import init_sim800l, get_imei, send_sms

try:
    from utils.robot_arm import RobotArm
    ROBOT_ARM_AVAILABLE = True
except (ImportError, NotImplementedError) as e:
    print(f"⚠ Robot Arm not available: {e}")
    ROBOT_ARM_AVAILABLE = False
    try:
        from utils.fire_suppression import FireSuppressionSystem
        FIRE_SUPPRESSION_AVAILABLE = True
    except (ImportError, NotImplementedError):
        FIRE_SUPPRESSION_AVAILABLE = False


class FireFightingRobot:
    """Main controller for AI-powered fire-fighting robot"""
    
    def __init__(self):
        """Initialize robot with all subsystems"""
        self.robot_arm = None
        self.suppression_system = None
        self.model = None
        self.sim800l = None
        self.emergency_phone = []
        self.location_name = 'De La Salle John Bosco'
        self.sms_cooldown = 10
        self.last_sms_time = 0
        self.detected_fires = []  # Track all detected fires during scan
        self.suppressed_fires = []  # Track fires that have been suppressed
        self.angle_tolerance = 15  # Degrees - consider fires within this angle as same fire
        
        print("\n" + "="*60)
        print(" AI-POWERED FIRE-FIGHTING ROBOT ")
        print("="*60)
        
        self.status = self.check_system_status()
        
    def check_system_status(self):
        """Check all module statuses before starting"""
        status = {
            'sim800l': False,
            'sim800l_imei': None,
            'audio': False,
            'servo': False,
            'stepper': False,
            'pump': False,
            'camera': False,
            'yolo': False
        }
        
        print("\n=== System Status Check ===")
        
        # Check SIM800L
        print("Checking SIM800L...")
        try:
            ser = init_sim800l()
            if ser:
                imei = get_imei(ser)
                if imei:
                    status['sim800l'] = True
                    status['sim800l_imei'] = imei
                    self.sim800l = ser
                    print(f"✓ SIM800L OK (IMEI: {imei})")
                else:
                    print("✗ SIM800L: No IMEI")
                    if ser:
                        ser.close()
            else:
                print("✗ SIM800L: Failed")
        except Exception as e:
            print(f"✗ SIM800L: {e}")
        
        # Check Audio
        print("Checking Audio...")
        try:
            from utils.audio import TPA3116D2Audio
            audio_test = TPA3116D2Audio()
            audio_test.close()
            status['audio'] = True
            print("✓ Audio OK")
        except Exception as e:
            print(f"✗ Audio: {e}")
        
        # Check Servo
        print("Checking Servo...")
        try:
            if ROBOT_ARM_AVAILABLE:
                from utils.servo import PCA9685ServoController
                servo = PCA9685ServoController(channels=16)
                servo.disable_all()
                servo.deinit()
                status['servo'] = True
                print("✓ Servo OK")
            else:
                print("⚠ Servo: Not on Raspberry Pi")
        except Exception as e:
            print(f"✗ Servo: {e}")
        
        # Check Stepper
        print("Checking Stepper...")
        try:
            if ROBOT_ARM_AVAILABLE:
                from utils.stepper import A4988Stepper
                stepper = A4988Stepper()
                stepper.cleanup()
                status['stepper'] = True
                print("✓ Stepper OK")
            else:
                print("⚠ Stepper: Not on Raspberry Pi")
        except Exception as e:
            print(f"✗ Stepper: {e}")
        
        # Check Water Pump
        print("Checking Water Pump...")
        try:
            if FIRE_SUPPRESSION_AVAILABLE:
                from utils.pump import WaterPump
                pump = WaterPump(relay_pin=18)
                pump.cleanup()
                status['pump'] = True
                print("✓ Water Pump OK")
            else:
                print("⚠ Water Pump: Not on Raspberry Pi")
        except Exception as e:
            print(f"✗ Water Pump: {e}")
        
        # Check Camera
        print("Checking Camera...")
        try:
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                status['camera'] = True
                print("✓ Camera OK")
                cap.release()
            else:
                print("✗ Camera: Not accessible")
        except Exception as e:
            print(f"✗ Camera: {e}")
        
        # Check YOLO Model
        print("Checking YOLOv11 Model...")
        try:
            model_path = self._get_model_path()
            if model_path.exists():
                status['yolo'] = True
                print(f"✓ YOLOv11 OK ({model_path})")
            else:
                print(f"✗ YOLOv11: Model not found at {model_path}")
        except Exception as e:
            print(f"✗ YOLOv11: {e}")
        
        print("\n=== Status Summary ===")
        for module, state in status.items():
            if module != 'sim800l_imei':
                symbol = "✓" if state else "✗"
                print(f"{symbol} {module.upper()}: {'OK' if state else 'FAILED'}")
        print("========================\n")
        
        return status
    
    def _get_model_path(self):
        """Get path to YOLOv11 model"""
        current = Path(__file__).resolve()
        for parent in list(current.parents)[:6]:
            candidate = parent / "model" / "weights" / "v1.pt"
            if candidate.exists():
                return candidate
        repo_root = current.parent
        return repo_root / "model" / "weights" / "v1.pt"
    
    def initialize_subsystems(self):
        """Initialize robot arm and suppression system"""
        print("\nInitializing subsystems...")
        
        if ROBOT_ARM_AVAILABLE and self.status['servo'] and self.status['stepper']:
            try:
                self.robot_arm = RobotArm()
                print("✓ Robot arm ready")
            except Exception as e:
                print(f"✗ Robot arm initialization failed: {e}")
        else:
            if not ROBOT_ARM_AVAILABLE:
                print("✗ Robot arm module not available (not on Raspberry Pi)")
            else:
                print("✗ Cannot initialize robot arm - servo/stepper failed")
        
        if FIRE_SUPPRESSION_AVAILABLE and self.status['audio'] and self.status['pump']:
            try:
                self.suppression_system = FireSuppressionSystem()
                print("✓ Fire suppression system ready")
            except Exception as e:
                print(f"✗ Fire suppression initialization failed: {e}")
        else:
            if not FIRE_SUPPRESSION_AVAILABLE:
                print("✗ Fire suppression module not available (not on Raspberry Pi)")
            else:
                print("✗ Cannot initialize suppression system - audio/pump failed")
        
        if self.status['yolo']:
            model_path = self._get_model_path()
            device = "cuda:0" if torch.cuda.is_available() else "cpu"
            self.model = YOLO(str(model_path))
            if hasattr(self.model, 'model') and hasattr(self.model.model, 'names'):
                self.model.model.names = {0: 'fire'}
            print(f"✓ YOLOv11 model loaded on {device}")
        else:
            print("✗ Cannot load YOLO model")
    
    def send_alert(self, message):
        """Send SMS alert if SIM800L is available and cooldown expired"""
        if self.status['sim800l'] and self.sim800l and self.emergency_phone:
            # Check cooldown
            current_time = time.time()
            time_since_last_sms = current_time - self.last_sms_time
            
            if time_since_last_sms < self.sms_cooldown:
                print(f"⚠ SMS cooldown active ({self.sms_cooldown - time_since_last_sms:.1f}s remaining)")
                return
            
            phone_numbers = self.emergency_phone if isinstance(self.emergency_phone, list) else [self.emergency_phone]
            
            for phone in phone_numbers:
                try:
                    send_sms(self.sim800l, phone, message)
                    print(f"✓ SMS sent to {phone}")
                except Exception as e:
                    print(f"✗ SMS failed for {phone}: {e}")
            
            self.last_sms_time = current_time
    
    def detect_fire(self, frame, return_all=False):
        """
        Detect fire in frame using YOLOv11.
        
        Args:
            frame: Input frame
            return_all: If True, return all detections. If False, return highest confidence only.
        
        Returns:
            If return_all=False: (fire_detected, confidence, bbox_center_x, bbox_center_y)
            If return_all=True: list of dicts with 'confidence', 'center_x', 'center_y', 'bbox'
        """
        if self.model is None:
            return [] if return_all else (False, 0.0, 0, 0)
        
        results = self.model(frame, imgsz=320, conf=0.25, verbose=False)
        
        if len(results) > 0 and len(results[0].boxes) > 0:
            boxes = results[0].boxes
            confidences = boxes.conf.cpu().numpy()
            bboxes_xyxy = boxes.xyxy.cpu().numpy()
            
            if return_all:
                detections = []
                for i in range(len(confidences)):
                    bbox = bboxes_xyxy[i]
                    center_x = int((bbox[0] + bbox[2]) / 2)
                    center_y = int((bbox[1] + bbox[3]) / 2)
                    detections.append({
                        'confidence': float(confidences[i]),
                        'center_x': center_x,
                        'center_y': center_y,
                        'bbox': bbox
                    })
                return detections
            else:
                # Return highest confidence detection only
                max_idx = np.argmax(confidences)
                confidence = confidences[max_idx]
                bbox = bboxes_xyxy[max_idx]
                
                center_x = int((bbox[0] + bbox[2]) / 2)
                center_y = int((bbox[1] + bbox[3]) / 2)
                
                return True, float(confidence), center_x, center_y
        
        return [] if return_all else (False, 0.0, 0, 0)
    
    def calculate_target_angle(self, center_x, frame_width):
        """
        Calculate shoulder angle needed to point at fire.
        
        Args:
            center_x: X coordinate of fire center in frame
            frame_width: Width of camera frame
        
        Returns:
            float: Angle offset from current position
        """
        fov = 60
        image_center = frame_width / 2
        pixel_offset = center_x - image_center
        angle_offset = (pixel_offset / image_center) * (fov / 2)
        
        return angle_offset
    
    def is_fire_already_suppressed(self, angle):
        """
        Check if a fire at this angle has already been suppressed.
        
        Args:
            angle: Target angle to check
        
        Returns:
            bool: True if fire at this angle was already suppressed
        """
        for suppressed_angle in self.suppressed_fires:
            angle_diff = abs(angle - suppressed_angle)
            # Handle wraparound (e.g., 5° and 355° are only 10° apart)
            if angle_diff > 180:
                angle_diff = 360 - angle_diff
            
            if angle_diff <= self.angle_tolerance:
                return True
        
        return False
    
    def idle_scan_mode(self):
        """
        Idle mode: Continuously rotate 360° and scan for fire.
        Collects ALL fires detected during the scan.
        
        Returns:
            list: List of detected fires with angle, confidence info
        """
        print("\n--- IDLE MODE: Scanning for Fire ---")
        
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("✗ Cannot access camera")
            return []
        
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.detected_fires = []  
        def check_for_fire():
            """Callback function to check for fire during rotation"""
            ret, frame = cap.read()
            if ret:
                all_detections = self.detect_fire(frame, return_all=True)
                
                for detection in all_detections:
                    if detection['confidence'] > 0.25:
                        current_angle = self.robot_arm.shoulder_angle if self.robot_arm else 0
                        angle_offset = self.calculate_target_angle(detection['center_x'], frame_width)
                        target_angle = (current_angle + angle_offset) % 360
                        
                        if not self.is_fire_already_suppressed(target_angle):
                            already_detected = False
                            for existing_fire in self.detected_fires:
                                angle_diff = abs(target_angle - existing_fire['angle'])
                                if angle_diff > 180:
                                    angle_diff = 360 - angle_diff
                                
                                if angle_diff <= self.angle_tolerance:
                                    if detection['confidence'] > existing_fire['confidence']:
                                        existing_fire['confidence'] = detection['confidence']
                                        existing_fire['angle'] = target_angle
                                    already_detected = True
                                    break
                            
                            if not already_detected:
                                self.detected_fires.append({
                                    'angle': target_angle,
                                    'confidence': detection['confidence']
                                })
                                print(f"🔥 Fire #{len(self.detected_fires)} detected at {target_angle:.1f}° (conf: {detection['confidence']:.2%})")
            return False 
        
        if self.robot_arm:
            self.robot_arm.rotate_360_scan(
                speed=0.03, 
                stop_callback=check_for_fire
            )
        else:
            print("  (Simulation mode - checking camera frames)")
            for _ in range(30): 
                check_for_fire()
                time.sleep(0.1)
        
        cap.release()
        
        self.detected_fires.sort(key=lambda x: x['confidence'], reverse=True)
        
        if self.detected_fires:
            print(f"\n📊 Scan complete: {len(self.detected_fires)} fire(s) detected")
            for i, fire in enumerate(self.detected_fires, 1):
                print(f"   Fire #{i}: {fire['angle']:.1f}° (conf: {fire['confidence']:.2%})")
        
        return self.detected_fires
    
    def engage_fire(self, target_angle, confidence):
        """
        Engage detected fire with suppression protocol.
        
        Args:
            target_angle: Shoulder angle to point at fire
            confidence: Detection confidence
        """
        print("\n" + "="*60)
        print(" FIRE ENGAGEMENT INITIATED ")
        print("="*60)
        
        if self.robot_arm:
            print(f"\nPointing at fire (angle: {target_angle:.1f}°)...")
            self.robot_arm.point_at_target(
                shoulder_angle=target_angle,
                elbow_angle=70,  
                wrist_angle=80 
            )
            time.sleep(1)
        else:
            print(f"\n[SIMULATION] Would point at fire (angle: {target_angle:.1f}°)")
        
        self.send_alert(f"Fire Detected at {self.location_name}! Confidence: {confidence:.1%}. Engaging suppression.")
        
        if self.suppression_system:
            result = self.suppression_system.suppression_protocol(
                fire_confidence=confidence
            )
            
            self.send_alert(f"Fire suppression complete at {self.location_name}. Status: {result}")
        else:
            print("\n[SIMULATION] Would execute suppression protocol")
            result = "simulated_success"
            time.sleep(2)
        
        # Mark this fire as suppressed
        self.suppressed_fires.append(target_angle)
        print(f"✓ Fire at {target_angle:.1f}° marked as suppressed")
        
        if self.robot_arm:
            print("\nReturning to home position...")
            self.robot_arm.home_position()
            time.sleep(1)
        else:
            print("\n[SIMULATION] Would return to home position")
        
        print("="*60)
        print(" READY FOR NEXT SCAN ")
        print("="*60 + "\n")
    
    def run(self):
        """Main robot control loop"""
        self.initialize_subsystems()
        
        if not self.model:
            print("\n✗ YOLO model not loaded. Cannot start robot.")
            return
        
        if not ROBOT_ARM_AVAILABLE:
            print("\n⚠ Running in simulation mode (no hardware control)")
            print("  Robot arm and suppression disabled on Windows")
            print("  Only fire detection will work\n")
        elif not (self.robot_arm and self.suppression_system):
            print("\n✗ Critical systems failed. Cannot start robot.")
            return
        
        print("\n" + "="*60)
        print(" FIRE-FIGHTING ROBOT ACTIVE ")
        print(" Press Ctrl+C to stop ")
        print("="*60 + "\n")
        
        try:
            while True:
                detected_fires = self.idle_scan_mode()
                
                if detected_fires:
                    print(f"\n🎯 Engaging {len(detected_fires)} fire(s) in priority order...")
                    
                    # Engage each fire one at a time, highest confidence first
                    for i, fire in enumerate(detected_fires, 1):
                        print(f"\n--- Engaging Fire {i}/{len(detected_fires)} ---")
                        self.engage_fire(fire['angle'], fire['confidence'])
                        time.sleep(1)  # Brief pause between fires
                    
                    print(f"\n✓ All {len(detected_fires)} fire(s) suppressed")
                    
                    # Clear suppressed fires list after a complete cycle
                    # (in case fires re-ignite, we'll detect them again)
                    if len(self.suppressed_fires) > 10:  # Prevent list from growing too large
                        self.suppressed_fires = self.suppressed_fires[-10:]
                    
                    time.sleep(2)
                else:
                    print("No new fires detected. Continuing scan...\n")
                    # Clear old suppressed fires after a clean scan
                    if len(self.suppressed_fires) > 0:
                        print(f"  (Cleared {len(self.suppressed_fires)} suppressed fire location(s))")
                        self.suppressed_fires.clear()
                    time.sleep(1)
        
        except KeyboardInterrupt:
            print("\n\nShutdown initiated by user...")
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up all resources"""
        print("\nCleaning up robot systems...")
        
        if self.robot_arm:
            self.robot_arm.cleanup()
        
        if self.suppression_system:
            self.suppression_system.cleanup()
        
        if self.sim800l:
            self.sim800l.close()
        
        print("Shutdown complete. Stay safe! 🚒\n")


def main():
    robot = FireFightingRobot()
    
    robot.emergency_phone = ["0", "1", "2"]
    
    robot.run()


if __name__ == "__main__":
    main()
