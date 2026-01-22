"""
AIPAWE - Servo Test Script
Test PCA9685 and servo functionality

Usage:
    python test_servos.py
    
Controls:
    1-6: Preset positions
    Q/A: Elbow up/down
    W/S: Wrist up/down
    N: Return to neutral
    ESC: Quit
"""

import sys
import time
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.utils_common import ConfigLoader
from utils.logger import AIPAWELogger

print("=" * 60)
print("AIPAWE - Servo Test Script")
print("=" * 60)

# Load configuration
config = ConfigLoader("config.yaml")
logger = AIPAWELogger(config)

print("\nChecking PCA9685 availability...")

# Try importing required libraries
try:
    from adafruit_pca9685 import PCA9685
    from board import SCL, SDA
    import busio
    print("✓ Adafruit PCA9685 library available")
    LIBRARIES_AVAILABLE = True
except ImportError as e:
    print(f"✗ Missing libraries: {e}")
    print("\nTo install on Raspberry Pi:")
    print("  pip install adafruit-circuitpython-pca9685")
    LIBRARIES_AVAILABLE = False

if LIBRARIES_AVAILABLE:
    # Try initializing I2C and PCA9685
    try:
        print("\nInitializing I2C bus...")
        i2c = busio.I2C(SCL, SDA)
        print("✓ I2C bus initialized")
        
        i2c_address = config.get('servo', 'i2c_address', default=0x40)
        print(f"\nConnecting to PCA9685 at address 0x{i2c_address:02X}...")
        pca = PCA9685(i2c, address=i2c_address)
        pca.frequency = config.get('servo', 'frequency', default=50)
        print(f"✓ PCA9685 connected at {pca.frequency}Hz")
        
        HARDWARE_AVAILABLE = True
        
    except Exception as e:
        print(f"✗ Failed to initialize PCA9685: {e}")
        print("\nTroubleshooting:")
        print("  1. Check I2C is enabled: sudo raspi-config")
        print("  2. Verify wiring: SDA→GPIO2, SCL→GPIO3")
        print("  3. Check address: i2cdetect -y 1")
        print("  4. Verify 5V power to PCA9685")
        HARDWARE_AVAILABLE = False
        pca = None
else:
    HARDWARE_AVAILABLE = False
    pca = None

print("\n" + "=" * 60)

if not HARDWARE_AVAILABLE:
    print("\nHardware not available - exiting")
    print("Please install required libraries and check hardware connections")
    sys.exit(1)

# Get servo configuration
elbow_channel = config.get('servo', 'elbow', 'channel')
elbow_min_pulse = config.get('servo', 'elbow', 'min_pulse')
elbow_max_pulse = config.get('servo', 'elbow', 'max_pulse')
elbow_min_angle = config.get('servo', 'elbow', 'min_angle')
elbow_max_angle = config.get('servo', 'elbow', 'max_angle')
elbow_neutral = config.get('servo', 'elbow', 'neutral_angle')

wrist_channel = config.get('servo', 'wrist', 'channel')
wrist_min_pulse = config.get('servo', 'wrist', 'min_pulse')
wrist_max_pulse = config.get('servo', 'wrist', 'max_pulse')
wrist_min_angle = config.get('servo', 'wrist', 'min_angle')
wrist_max_angle = config.get('servo', 'wrist', 'max_angle')
wrist_neutral = config.get('servo', 'wrist', 'neutral_angle')

print(f"\nElbow Servo - Channel {elbow_channel}")
print(f"  Range: {elbow_min_angle}° to {elbow_max_angle}° (neutral: {elbow_neutral}°)")
print(f"  Pulse: {elbow_min_pulse}μs to {elbow_max_pulse}μs")

print(f"\nWrist Servo - Channel {wrist_channel}")
print(f"  Range: {wrist_min_angle}° to {wrist_max_angle}° (neutral: {wrist_neutral}°)")
print(f"  Pulse: {wrist_min_pulse}μs to {wrist_max_pulse}μs")

def angle_to_duty_cycle(angle, min_pulse, max_pulse, min_angle, max_angle):
    """Convert angle to PWM duty cycle"""
    # Clamp angle
    angle = max(min_angle, min(max_angle, angle))
    
    # Map angle to pulse width
    pulse_width = min_pulse + (angle - min_angle) * (max_pulse - min_pulse) / (max_angle - min_angle)
    
    # Convert pulse width (microseconds) to duty cycle (0-65535)
    # At 50Hz, period is 20ms = 20000μs
    duty_cycle = int((pulse_width / 20000.0) * 65535)
    
    return duty_cycle

def set_servo(channel, angle, min_pulse, max_pulse, min_angle, max_angle, name):
    """Set servo to angle"""
    duty = angle_to_duty_cycle(angle, min_pulse, max_pulse, min_angle, max_angle)
    pca.channels[channel].duty_cycle = duty
    print(f"{name}: {angle}° (duty: {duty})")

def move_to_neutral():
    """Move both servos to neutral"""
    print("\nMoving to NEUTRAL position...")
    set_servo(elbow_channel, elbow_neutral, elbow_min_pulse, elbow_max_pulse, 
              elbow_min_angle, elbow_max_angle, "Elbow")
    set_servo(wrist_channel, wrist_neutral, wrist_min_pulse, wrist_max_pulse,
              wrist_min_angle, wrist_max_angle, "Wrist")

# Initialize to neutral
print("\n" + "=" * 60)
print("Initializing servos to neutral position...")
move_to_neutral()
time.sleep(1)

print("\n" + "=" * 60)
print("SERVO TEST CONTROLS:")
print("=" * 60)
print("Presets:")
print("  1 - Both minimum (0°)")
print("  2 - Both maximum (180°)")
print("  3 - Elbow 45°, Wrist 45°")
print("  4 - Elbow 90°, Wrist 90°")
print("  5 - Elbow 135°, Wrist 135°")
print("  6 - Sweep test")
print("\nManual Control:")
print("  Q - Elbow UP (+10°)")
print("  A - Elbow DOWN (-10°)")
print("  W - Wrist UP (+10°)")
print("  S - Wrist DOWN (-10°)")
print("\nOther:")
print("  N - Return to NEUTRAL")
print("  ESC - Quit")
print("=" * 60)

current_elbow = elbow_neutral
current_wrist = wrist_neutral

try:
    # Check if running in terminal that supports keyboard input
    try:
        import msvcrt  # Windows
        USE_MSVCRT = True
    except ImportError:
        import tty
        import termios
        USE_MSVCRT = False
        
        # Save terminal settings
        old_settings = termios.tcgetattr(sys.stdin)
    
    print("\nReady! Press keys to control servos...\n")
    
    while True:
        # Get keyboard input
        if USE_MSVCRT:
            if msvcrt.kbhit():
                key = msvcrt.getch().decode('utf-8').lower()
            else:
                time.sleep(0.1)
                continue
        else:
            tty.setcbreak(sys.stdin.fileno())
            key = sys.stdin.read(1).lower()
        
        if key == '\x1b':  # ESC
            print("\nExiting...")
            break
        
        elif key == '1':
            print("\nPreset 1: Both MINIMUM")
            current_elbow = elbow_min_angle
            current_wrist = wrist_min_angle
            set_servo(elbow_channel, current_elbow, elbow_min_pulse, elbow_max_pulse,
                     elbow_min_angle, elbow_max_angle, "Elbow")
            set_servo(wrist_channel, current_wrist, wrist_min_pulse, wrist_max_pulse,
                     wrist_min_angle, wrist_max_angle, "Wrist")
        
        elif key == '2':
            print("\nPreset 2: Both MAXIMUM")
            current_elbow = elbow_max_angle
            current_wrist = wrist_max_angle
            set_servo(elbow_channel, current_elbow, elbow_min_pulse, elbow_max_pulse,
                     elbow_min_angle, elbow_max_angle, "Elbow")
            set_servo(wrist_channel, current_wrist, wrist_min_pulse, wrist_max_pulse,
                     wrist_min_angle, wrist_max_angle, "Wrist")
        
        elif key == '3':
            print("\nPreset 3: Both 45°")
            current_elbow = 45
            current_wrist = 45
            set_servo(elbow_channel, current_elbow, elbow_min_pulse, elbow_max_pulse,
                     elbow_min_angle, elbow_max_angle, "Elbow")
            set_servo(wrist_channel, current_wrist, wrist_min_pulse, wrist_max_pulse,
                     wrist_min_angle, wrist_max_angle, "Wrist")
        
        elif key == '4':
            print("\nPreset 4: Both 90°")
            current_elbow = 90
            current_wrist = 90
            set_servo(elbow_channel, current_elbow, elbow_min_pulse, elbow_max_pulse,
                     elbow_min_angle, elbow_max_angle, "Elbow")
            set_servo(wrist_channel, current_wrist, wrist_min_pulse, wrist_max_pulse,
                     wrist_min_angle, wrist_max_angle, "Wrist")
        
        elif key == '5':
            print("\nPreset 5: Both 135°")
            current_elbow = 135
            current_wrist = 135
            set_servo(elbow_channel, current_elbow, elbow_min_pulse, elbow_max_pulse,
                     elbow_min_angle, elbow_max_angle, "Elbow")
            set_servo(wrist_channel, current_wrist, wrist_min_pulse, wrist_max_pulse,
                     wrist_min_angle, wrist_max_angle, "Wrist")
        
        elif key == '6':
            print("\nPreset 6: SWEEP TEST")
            for angle in range(0, 181, 15):
                print(f"  Sweeping to {angle}°...")
                set_servo(elbow_channel, angle, elbow_min_pulse, elbow_max_pulse,
                         elbow_min_angle, elbow_max_angle, "Elbow")
                set_servo(wrist_channel, angle, wrist_min_pulse, wrist_max_pulse,
                         wrist_min_angle, wrist_max_angle, "Wrist")
                time.sleep(0.5)
            move_to_neutral()
        
        elif key == 'q':
            current_elbow = min(elbow_max_angle, current_elbow + 10)
            set_servo(elbow_channel, current_elbow, elbow_min_pulse, elbow_max_pulse,
                     elbow_min_angle, elbow_max_angle, "Elbow")
        
        elif key == 'a':
            current_elbow = max(elbow_min_angle, current_elbow - 10)
            set_servo(elbow_channel, current_elbow, elbow_min_pulse, elbow_max_pulse,
                     elbow_min_angle, elbow_max_angle, "Elbow")
        
        elif key == 'w':
            current_wrist = min(wrist_max_angle, current_wrist + 10)
            set_servo(wrist_channel, current_wrist, wrist_min_pulse, wrist_max_pulse,
                     wrist_min_angle, wrist_max_angle, "Wrist")
        
        elif key == 's':
            current_wrist = max(wrist_min_angle, current_wrist - 10)
            set_servo(wrist_channel, current_wrist, wrist_min_pulse, wrist_max_pulse,
                     wrist_min_angle, wrist_max_angle, "Wrist")
        
        elif key == 'n':
            current_elbow = elbow_neutral
            current_wrist = wrist_neutral
            move_to_neutral()

except KeyboardInterrupt:
    print("\n\nInterrupted by user")

finally:
    # Restore terminal settings on Linux
    if not USE_MSVCRT:
        try:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        except:
            pass
    
    # Return to neutral before exit
    print("\nReturning to neutral position...")
    move_to_neutral()
    time.sleep(1)
    
    # Cleanup
    try:
        pca.deinit()
    except:
        pass
    
    print("Servo test complete.\n")
