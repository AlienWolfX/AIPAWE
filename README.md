# AIPAWE - AI-Powered Automated Water Extinguisher

A sophisticated ceiling-mounted robotic fire suppression system controlled by Raspberry Pi that autonomously detects, targets, and extinguishes fires using YOLOv11 detection, audio suppression, and water spray.

![System Architecture](img/system_diagram.png)

## 🎯 Overview

AIPAWE is an intelligent fire suppression robot that:
- **Continuously scans 360°** using a NEMA17 stepper motor-driven base
- **Detects fires** in real-time using YOLOv11 computer vision
- **Prioritizes and queues** multiple fire targets
- **Attempts suppression** first with low-frequency audio, then water spray
- **Sends SMS notifications** for fire detection, suppression success/failure
- **Returns to scanning** autonomously after each event

## 🏗️ System Architecture

### State Machine Flow
```
SCAN → DETECT → SOUND → VERIFY → WATER → VERIFY → REPORT → RETURN → SCAN
```

### Hardware Components

| Component | Purpose | Interface |
|-----------|---------|-----------|
| **NEMA17 Stepper Motor** | Base rotation (360°) | A4988 driver |
| **PCA9685 PWM Driver** | Servo control | I2C |
| **2× Servos** | Elbow & wrist joints | PWM |
| **USB Camera** | Fire detection input | USB/V4L2 |
| **ALSA Sound Card** | Audio suppression | USB |
| **Water Pump** | Water spray | Relay |
| **SIM800L GSM Module** | SMS notifications | Serial UART |
| **Raspberry Pi 4** | Main controller | - |

### Software Architecture

```
AIPAWE/
├── main.py                 # Main control loop
├── config.yaml            # Hot-reloadable configuration
├── requirements.txt       # Python dependencies
├── model/
│   └── weights/
│       └── v1.pt         # YOLOv11 model weights
└── utils/
    ├── stepper_base.py   # NEMA17/A4988 control
    ├── servo_arm.py      # PCA9685 servo kinematics
    ├── audio_out.py      # ALSA audio playback
    ├── water_control.py  # Relay pump control
    ├── fire_detector.py  # YOLOv11 detection
    ├── notifier.py       # SIM800L SMS
    ├── state_machine.py  # State orchestration
    ├── logger.py         # Event logging
    └── utils_common.py   # Shared utilities
```

## 🚀 Quick Start

### 1. Hardware Setup

#### Wiring Diagram

**Stepper Motor (A4988):**
```
RPi GPIO 17 → STEP
RPi GPIO 18 → DIR
RPi GPIO 27 → ENABLE
12V Power → VMOT
GND → GND
```

**PCA9685 Servo Driver:**
```
RPi SDA (GPIO 2) → SDA
RPi SCL (GPIO 3) → SCL
5V → VCC
GND → GND
Servo 1 (Elbow) → Channel 0
Servo 2 (Wrist) → Channel 1
```

**Water Pump Relay:**
```
RPi GPIO 22 → Relay IN
5V → Relay VCC
Pump → Relay NO/COM
```

**SIM800L GSM:**
```
RPi TXD (GPIO 14) → RXD
RPi RXD (GPIO 15) → TXD
4V → VCC (use buck converter)
GND → GND
```

### 2. Software Installation

```bash
# Clone repository
git clone https://github.com/AlienWolfX/AIPAWE.git
cd AIPAWE

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# On Raspberry Pi, install additional packages:
pip install RPi.GPIO adafruit-circuitpython-pca9685 pyalsaaudio
```

### 3. Configuration

Edit [config.yaml](config.yaml) to match your hardware setup:

```yaml
# Key settings to customize:
stepper:
  step_pin: 17      # Your GPIO pin
  rpm: 10           # Scanning speed

servo:
  elbow:
    channel: 0      # PCA9685 channel
    neutral_angle: 90
  wrist:
    channel: 1

detection:
  model_path: "model/weights/v1.pt"
  confidence_threshold: 0.65
  camera_index: 0

gsm:
  phone_numbers:
    - "+1234567890"  # Your phone number(s)
```

### 4. Run the System

```bash
# Activate virtual environment
source .venv/bin/activate

# Run AIPAWE
python main.py
```

**Expected Output:**
```
============================================================
AIPAWE - AI-Powered Automated Water Extinguisher
============================================================
System initialized. Press Ctrl+C to stop.
2026-01-22 10:30:00 - INFO - AIPAWE system starting...
2026-01-22 10:30:01 - INFO - StepperBase initialized: 3200 steps/rev, 10 RPM
2026-01-22 10:30:01 - INFO - ServoArm initialized at neutral position
2026-01-22 10:30:02 - INFO - YOLOv11 model loaded: model/weights/v1.pt
2026-01-22 10:30:02 - INFO - Camera initialized: 640x480 @ 15fps
2026-01-22 10:30:03 - INFO - STATE TRANSITION: SCAN → SCAN
```

## 📋 State Machine Details

### States

| State | Description | Next State |
|-------|-------------|------------|
| **SCAN** | Continuous 360° scanning, fire detection active | DETECT (on fire) |
| **DETECT** | Stop scanning, rotate to target, aim arm | SOUND |
| **SOUND** | Play low-frequency audio suppression tone | VERIFY_SOUND |
| **VERIFY_SOUND** | Check if fire extinguished | REPORT (success) / WATER (fail) |
| **WATER** | Activate water pump spray | VERIFY_WATER |
| **VERIFY_WATER** | Check if fire extinguished | REPORT (success) / WATER (retry) |
| **REPORT** | Send SMS notification | RETURN |
| **RETURN** | Return arm to neutral, resume scanning | SCAN / DETECT (if queue) |

### SMS Notifications

The system sends **only 3 message types**:

1. **Fire Detected:**
   ```
   Fire detected at sector 127° - AIPAWE responding
   ```

2. **Fire Suppressed:**
   ```
   Fire suppressed successfully using sound at sector 127°
   Fire suppressed successfully using water at sector 127°
   ```

3. **Suppression Failed:**
   ```
   Suppression failed after 5 attempts at sector 127° - manual intervention required
   ```

## ⚙️ Configuration Reference

### Hot-Reloadable Settings

The system automatically reloads [config.yaml](config.yaml) every 5 seconds. Change settings without restarting:

```yaml
# Scanning parameters
stepper:
  rpm: 10              # Rotation speed (1-60)
  sector_size: 15      # Degrees per scan increment

# Detection thresholds
detection:
  confidence_threshold: 0.65    # Main trigger threshold
safety:
  min_confidence: 0.5           # Absolute minimum

# Suppression attempts
audio:
  max_attempts: 2      # Audio suppression tries
  duration: 5          # Seconds per attempt
water:
  max_attempts: 3      # Water spray tries
  spray_duration: 3    # Seconds per spray
safety:
  max_total_attempts: 5  # Total sound + water
```

### Safety Features

- **Confidence Filtering:** Requires minimum confidence before triggering
- **Attempt Limits:** Prevents infinite suppression loops
- **Interlocks:** 0.5s delay between audio/water to prevent overlap
- **Watchdog Timer:** Forces return to SCAN if stuck (300s default)
- **Emergency Stop:** GPIO pin or Ctrl+C for immediate halt

## 🔧 Module Documentation

### [stepper_base.py](utils/stepper_base.py)
Controls NEMA17 stepper motor via A4988 driver.

**Key Methods:**
- `start_continuous_scan()` - Begin 360° scanning
- `rotate_to_angle(angle)` - Rotate to specific angle
- `get_current_angle()` - Get current base position

### [servo_arm.py](utils/servo_arm.py)
Controls elbow/wrist servos via PCA9685.

**Key Methods:**
- `aim_at_target(azimuth, elevation)` - Aim at fire coordinates
- `move_to_neutral()` - Return to ceiling-mounted neutral
- `set_elbow_angle(angle)`, `set_wrist_angle(angle)` - Direct control

### [fire_detector.py](utils/fire_detector.py)
YOLOv11-based fire detection.

**Key Methods:**
- `detect_fires()` - Return list of FireDetection objects
- `get_highest_confidence_fire()` - Get best detection
- `save_detection_frame(path)` - Save annotated image

### [audio_out.py](utils/audio_out.py)
ALSA-based low-frequency audio suppression.

**Key Methods:**
- `play_suppression_tone()` - Play configured frequency
- `stop()` - Emergency stop playback

### [water_control.py](utils/water_control.py)
Relay-controlled water pump.

**Key Methods:**
- `start_spray(duration)` - Activate pump
- `pulse_spray(pulses, duration)` - Pulsed spray pattern
- `stop()` - Emergency stop

### [notifier.py](utils/notifier.py)
SIM800L GSM SMS notifications.

**Key Methods:**
- `notify_fire_detected(sector)` - Send detection alert
- `notify_fire_suppressed(sector, method)` - Send success
- `notify_suppression_failed(sector, attempts)` - Send failure

### [state_machine.py](utils/state_machine.py)
Main orchestration controller.

**Key Methods:**
- `run_cycle()` - Execute one state machine iteration
- `emergency_stop()` - Halt all operations
- `get_status()` - Return current system state

## 🧪 Testing & Development

### Mock Mode (Non-Raspberry Pi)

The system includes mock GPIO/hardware classes for development:

```python
# Automatically uses mocks when RPi.GPIO not available
python main.py  # Runs on Windows/Linux without hardware
```

### Testing Individual Modules

```python
# Test stepper motor
from utils.stepper_base import StepperBase
from utils.utils_common import ConfigLoader
from utils.logger import AIPAWELogger

config = ConfigLoader("config.yaml")
logger = AIPAWELogger(config)
stepper = StepperBase(config, logger)

stepper.rotate_to_angle(90)
stepper.start_continuous_scan()
```

### Logging

Logs are saved to `logs/aipawe.log` with rotation:

```
2026-01-22 10:30:45 - INFO - STATE TRANSITION: SCAN → DETECT
2026-01-22 10:30:45 - WARNING - FIRE DETECTED: Sector 127.3° | Confidence 78.50%
2026-01-22 10:30:46 - INFO - HARDWARE: StepperBase - ROTATE | 90.0° → 127.3° (2980 steps)
2026-01-22 10:30:48 - INFO - SUPPRESSION: Method=sound | Attempt=1
2026-01-22 10:30:53 - INFO - SUPPRESSION SUCCESS: Method=sound
```

## 🛡️ Safety Considerations

⚠️ **WARNING:** This system controls potentially dangerous equipment (motors, water, high-frequency audio). Follow safety guidelines:

1. **Test in controlled environment** before deployment
2. **Install emergency stop** accessible to operators
3. **Use appropriate power supplies** (12V for stepper, 5V for servos/relay)
4. **Waterproof electronics** in enclosures
5. **Mount securely** to ceiling with proper anchoring
6. **Test fire detection** with controlled test fires
7. **Verify SMS delivery** before relying on notifications
8. **Monitor system logs** regularly

## 🔌 Power Requirements

| Component | Voltage | Current | Notes |
|-----------|---------|---------|-------|
| Raspberry Pi 4 | 5V | 3A | USB-C power supply |
| NEMA17 Stepper | 12V | 1.5A | Via A4988 driver |
| Servos (2×) | 5V | 1A each | Via PCA9685 |
| Water Pump | 12V | 1A | Via relay |
| SIM800L | 3.7-4.2V | 2A peak | Use buck converter |

**Recommended:** Separate 12V and 5V power rails with common ground.

## 📊 Performance Metrics

- **Scan Coverage:** 360° in ~36 seconds @ 10 RPM, 15° sectors
- **Detection Latency:** ~67ms per frame @ 15 FPS
- **Target Acquisition:** <3 seconds (rotate + aim)
- **Audio Suppression:** 5 seconds per attempt
- **Water Spray:** 3 seconds per attempt
- **SMS Delivery:** 2-5 seconds per message

## 🐛 Troubleshooting

### Camera Not Detected
```bash
# List video devices
ls /dev/video*

# Test camera
python -c "import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened())"
```

### SIM800L Not Responding
```bash
# Check serial port
ls -l /dev/ttyS0

# Test AT commands
screen /dev/ttyS0 9600
# Type: AT
# Expected: OK
```

### Stepper Motor Not Moving
- Check 12V power supply
- Verify A4988 wiring (STEP, DIR, ENABLE)
- Test microstep configuration
- Ensure ENABLE pin is LOW

### Audio Not Playing
```bash
# List ALSA devices
aplay -l

# Test audio output
speaker-test -D plughw:1,0 -c 1
```

## 📝 License

MIT License - See [LICENSE](LICENSE) for details.

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Test thoroughly on hardware
4. Submit pull request with detailed description

## 📧 Contact

**Project:** AIPAWE  
**Repository:** https://github.com/AlienWolfX/AIPAWE  
**Issues:** https://github.com/AlienWolfX/AIPAWE/issues

---

**Built with ❤️ for fire safety and autonomous robotics**

![Design](img/design.png)

## Introduction

Fires spreading in urban areas are common, especially in residential neighborhoods where wooden houses are closely spaced with little separation between them (Ondie & Bowman, 2025). This project aims to develop a device that helps extinguish fires using acoustic sound and water.