#!/usr/bin/env python3
"""
Quick test script for Fire-Fighting Robot subsystems
Tests each component individually before full operation
"""

import sys
import time
from pathlib import Path

print("\n" + "="*60)
print(" FIRE-FIGHTING ROBOT - COMPONENT TEST ")
print("="*60 + "\n")

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    required_modules = [
        ('cv2', 'opencv-python'),
        ('torch', 'torch'),
        ('ultralytics', 'ultralytics'),
        ('numpy', 'numpy'),
        ('serial', 'pyserial'),
        ('pyaudio', 'pyaudio'),
    ]
    
    try:
        import RPi.GPIO as GPIO
        print("  ✓ RPi.GPIO")
    except ImportError:
        print("  ⚠ RPi.GPIO (Not on Raspberry Pi - expected)")
    
    for module_name, package_name in required_modules:
        try:
            __import__(module_name)
            print(f"  ✓ {module_name}")
        except ImportError:
            print(f"  ✗ {module_name} - install with: pip install {package_name}")
            return False
    
    return True


def test_model_exists():
    """Check if YOLO model file exists"""
    print("\nChecking YOLO model...")
    model_path = Path("model/weights/v1.pt")
    
    if model_path.exists():
        size_mb = model_path.stat().st_size / (1024 * 1024)
        print(f"  ✓ Model found: {model_path} ({size_mb:.2f} MB)")
        return True
    else:
        print(f"  ✗ Model not found at {model_path}")
        print(f"    Please place your YOLOv11 fire detection model there")
        return False


def test_camera():
    """Test camera access"""
    print("\nTesting camera...")
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("  ✗ Cannot open camera")
            return False
        
        ret, frame = cap.read()
        if ret:
            h, w = frame.shape[:2]
            print(f"  ✓ Camera OK - Resolution: {w}x{h}")
            cap.release()
            return True
        else:
            print("  ✗ Cannot read from camera")
            cap.release()
            return False
            
    except Exception as e:
        print(f"  ✗ Camera error: {e}")
        return False


def test_audio():
    """Test audio system"""
    print("\nTesting audio system...")
    try:
        from utils.audio import TPA3116D2Audio
        
        audio = TPA3116D2Audio()
        print("  Playing test beep...")
        audio.play_beep(frequency=1000, duration=0.2, volume=0.3)
        print("  ✓ Audio system OK")
        audio.close()
        return True
        
    except Exception as e:
        print(f"  ✗ Audio error: {e}")
        return False


def test_gpio_modules():
    """Test GPIO-based modules (only on Raspberry Pi)"""
    print("\nTesting GPIO modules...")
    
    try:
        import RPi.GPIO as GPIO
    except ImportError:
        print("  ⚠ Not on Raspberry Pi - skipping GPIO tests")
        return True
    
    # Test Stepper
    print("  Testing stepper motor controller...")
    try:
        from utils.stepper import A4988Stepper
        stepper = A4988Stepper()
        print("    Moving 10 steps...")
        stepper.rotate(10, clockwise=True, delay=0.01)
        stepper.cleanup()
        print("  ✓ Stepper motor OK")
    except Exception as e:
        print(f"  ✗ Stepper motor error: {e}")
        return False
    
    # Test Servo
    print("  Testing servo controller...")
    try:
        from utils.servo import PCA9685ServoController
        servo = PCA9685ServoController(channels=16)
        print("    Setting channel 0 to 90°...")
        servo.set_angle(0, 90)
        time.sleep(0.5)
        servo.disable_all()
        servo.deinit()
        print("  ✓ Servo controller OK")
    except Exception as e:
        print(f"  ✗ Servo controller error: {e}")
        return False
    
    # Test Water Pump
    print("  Testing water pump...")
    try:
        from utils.pump import WaterPump
        pump = WaterPump(relay_pin=18)
        print("    Brief pulse test (0.2s)...")
        pump.pulse(0.2)
        pump.cleanup()
        print("  ✓ Water pump OK")
    except Exception as e:
        print(f"  ✗ Water pump error: {e}")
        return False
    
    return True


def test_yolo_inference():
    """Test YOLO model loading and inference"""
    print("\nTesting YOLO inference...")
    
    try:
        import torch
        from ultralytics import YOLO
        import cv2
        import numpy as np
        
        model_path = Path("model/weights/v1.pt")
        if not model_path.exists():
            print("  ⚠ Skipping - model not found")
            return True
        
        print("  Loading model...")
        model = YOLO(str(model_path))
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        print(f"  Using device: {device}")
        
        # Create dummy frame
        print("  Running inference on test frame...")
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        results = model(dummy_frame, imgsz=320, conf=0.25, verbose=False)
        
        print("  ✓ YOLO inference OK")
        return True
        
    except Exception as e:
        print(f"  ✗ YOLO error: {e}")
        return False


def test_robot_arm():
    """Test robot arm controller"""
    print("\nTesting robot arm controller...")
    
    try:
        import RPi.GPIO as GPIO
    except ImportError:
        print("  ⚠ Not on Raspberry Pi - skipping robot arm test")
        return True
    
    try:
        from utils.robot_arm import RobotArm
        
        print("  Initializing robot arm...")
        arm = RobotArm()
        
        print("  Testing shoulder rotation (10°)...")
        arm.rotate_shoulder(10, clockwise=True)
        time.sleep(0.5)
        
        print("  Testing elbow movement...")
        arm.set_elbow_position(100)
        time.sleep(0.5)
        
        print("  Testing wrist movement...")
        arm.set_wrist_position(100)
        time.sleep(0.5)
        
        print("  Returning to home...")
        arm.home_position()
        
        arm.cleanup()
        print("  ✓ Robot arm OK")
        return True
        
    except Exception as e:
        print(f"  ✗ Robot arm error: {e}")
        return False


def test_fire_suppression():
    """Test fire suppression system"""
    print("\nTesting fire suppression system...")
    
    try:
        import RPi.GPIO as GPIO
    except ImportError:
        print("  ⚠ Not on Raspberry Pi - skipping suppression test")
        return True
    
    try:
        from utils.fire_suppression import FireSuppressionSystem
        
        print("  Initializing suppression system...")
        suppression = FireSuppressionSystem()
        
        print("  Testing acoustic suppression (2s)...")
        suppression.acoustic_suppression(duration=2.0)
        
        print("  Testing water pulse...")
        suppression.water_suppression(duration=0.6, pattern='pulse')
        
        suppression.cleanup()
        print("  ✓ Fire suppression OK")
        return True
        
    except Exception as e:
        print(f"  ✗ Fire suppression error: {e}")
        return False


def main():
    """Run all tests"""
    tests = [
        ("Imports", test_imports),
        ("YOLO Model", test_model_exists),
        ("Camera", test_camera),
        ("Audio", test_audio),
        ("GPIO Modules", test_gpio_modules),
        ("YOLO Inference", test_yolo_inference),
        ("Robot Arm", test_robot_arm),
        ("Fire Suppression", test_fire_suppression),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except KeyboardInterrupt:
            print("\n\nTest interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")
            results[test_name] = False
        
        time.sleep(0.5)
    
    # Summary
    print("\n" + "="*60)
    print(" TEST SUMMARY ")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! Robot is ready for operation.")
        print("  Run 'python main.py' to start the robot.")
    else:
        print("\n⚠ Some tests failed. Please fix issues before running robot.")
    
    print("="*60 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest suite interrupted by user\n")
        sys.exit(1)
