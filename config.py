"""
Configuration file for Fire-Fighting Robot
Adjust these parameters to customize robot behavior
"""

# ============================================================================
# HARDWARE CONFIGURATION
# ============================================================================

# Stepper Motor (A4988) - Shoulder Base
STEPPER_CONFIG = {
    'step_pin': 24,
    'dir_pin': 23,
    'enable_pin': 25,
    'ms1_pin': 17,
    'ms2_pin': 22,
    'ms3_pin': 27,
    'microstepping': '1/16',  # Options: 'full', '1/2', '1/4', '1/8', '1/16'
    'steps_per_rev': 200,
}

# Water Pump Relay
PUMP_CONFIG = {
    'relay_pin': 18,
}

# PCA9685 Servo Controller
SERVO_CONFIG = {
    'i2c_address': 0x40,
    'frequency': 50,  # Hz
    'channels': 16,
    # Channel assignments
    'elbow_servo_1': 0,
    'elbow_servo_2': 1,
    'wrist_servo_1': 2,  # Camera tilt
    'wrist_servo_2': 3,  # Speaker tilt
}

# Audio System (TPA3116D2)
AUDIO_CONFIG = {
    'sample_rate': 44100,
    'channels': 2,
    'device_index': None,  # None = use default device
}

# Camera
CAMERA_CONFIG = {
    'source': 0,  # 0 = default camera, or path to video file
    'width': 640,
    'height': 480,
    'fps': 30,
}

# SIM800L GSM Module
SIM800L_CONFIG = {
    'port': '/dev/ttyAMA0',  # None = auto-detect, or '/dev/ttyAMA0' on RPi
    'baudrate': 9600,
    'timeout': 1,
    'emergency_phone': None,  # Set to "+1234567890" to enable SMS alerts
    'sms_cooldown': 10,  # Minimum seconds between SMS (prevent spam)
    'location_name': 'De La Salle John Bosco',  # Location for SMS alerts
}

# ============================================================================
# AI/DETECTION CONFIGURATION
# ============================================================================

YOLO_CONFIG = {
    'model_path': 'model/weights/v1.pt',
    'imgsz': 320,  # Input image size (320, 416, 640, etc.)
    'conf_threshold': 0.25,  # Confidence threshold (0.0 - 1.0)
    'device': 'auto',  # 'auto', 'cpu', 'cuda:0'
}

# Fire detection thresholds
DETECTION_CONFIG = {
    'min_confidence': 0.25,  # Minimum confidence to trigger action
    'camera_fov': 60,  # Camera field of view in degrees
}

# ============================================================================
# ROBOT BEHAVIOR CONFIGURATION
# ============================================================================

# Scanning behavior (idle mode)
SCAN_CONFIG = {
    'rotation_speed': 0.03,  # Delay between steps (lower = faster)
    'pause_between_scans': 1.0,  # Seconds to pause between 360° scans
}

# Fire engagement positioning
POSITIONING_CONFIG = {
    'elbow_engage_angle': 70,  # Elbow angle when engaging fire (0-180)
    'wrist_engage_angle': 80,  # Wrist angle when engaging fire (0-180)
    'positioning_delay': 1.0,  # Seconds to wait after positioning
}

# Fire suppression protocol
SUPPRESSION_CONFIG = {
    # Phase 1: Acoustic suppression
    'acoustic_duration': 6.0,  # Seconds
    'acoustic_frequency_min': 30,  # Hz - low frequency for fire suppression
    'acoustic_frequency_max': 120,  # Hz
    'acoustic_volume': 0.8,  # 0.0 - 1.0
    
    # Phase 2: Combined suppression
    'combined_duration': 6.0,  # Seconds
    'combined_acoustic_volume': 0.8,
    
    # Water suppression
    'water_pattern': 'continuous',  # 'continuous' or 'pulse'
    'pulse_duration': 0.5,  # Seconds (if pattern='pulse')
    'pulse_pause': 0.3,  # Seconds (if pattern='pulse')
    
    # Assessment
    'assessment_delay': 2.0,  # Seconds to wait between phases
}

# ============================================================================
# OPERATIONAL LIMITS
# ============================================================================

LIMITS_CONFIG = {
    # Servo angle limits (safety)
    'elbow_min_angle': 0,
    'elbow_max_angle': 180,
    'wrist_min_angle': 0,
    'wrist_max_angle': 180,
    
    # Temperature limits (if temperature sensor added)
    'max_operating_temp': 50,  # Celsius
    
    # Continuous operation limits
    'max_continuous_suppression_time': 30,  # Seconds
    'cooldown_period': 10,  # Seconds between suppression attempts
}

# ============================================================================
# NOTIFICATIONS & ALERTS
# ============================================================================

NOTIFICATION_CONFIG = {
    'enable_sms_alerts': False,  # Set True to enable SMS
    'enable_audio_alerts': True,  # Audible alerts
    'enable_console_logging': True,  # Print to console
    
    # Alert messages (use {location} and {confidence} placeholders)
    'fire_detected_msg': "Fire Detected at {location}! Confidence: {confidence:.1%}. Engaging suppression.",
    'suppression_complete_msg': "Fire suppression complete at {location}. Status: {result}",
}

# ============================================================================
# DEBUGGING & TESTING
# ============================================================================

DEBUG_CONFIG = {
    'enable_debug_mode': False,  # Enable verbose logging
    'save_detection_images': False,  # Save images with detections
    'detection_save_dir': 'detections/',  # Where to save images
    'show_camera_preview': False,  # Show live camera preview
    'simulate_fire_detection': False,  # For testing without actual fire
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_config():
    """Get complete configuration dictionary"""
    return {
        'stepper': STEPPER_CONFIG,
        'pump': PUMP_CONFIG,
        'servo': SERVO_CONFIG,
        'audio': AUDIO_CONFIG,
        'camera': CAMERA_CONFIG,
        'sim800l': SIM800L_CONFIG,
        'yolo': YOLO_CONFIG,
        'detection': DETECTION_CONFIG,
        'scan': SCAN_CONFIG,
        'positioning': POSITIONING_CONFIG,
        'suppression': SUPPRESSION_CONFIG,
        'limits': LIMITS_CONFIG,
        'notification': NOTIFICATION_CONFIG,
        'debug': DEBUG_CONFIG,
    }


def print_config():
    """Print current configuration"""
    config = get_config()
    print("\n" + "="*60)
    print(" FIRE-FIGHTING ROBOT CONFIGURATION ")
    print("="*60)
    
    for section, params in config.items():
        print(f"\n[{section.upper()}]")
        for key, value in params.items():
            print(f"  {key}: {value}")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    print_config()
