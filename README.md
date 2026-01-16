# AIPAWE - AI-Powered Autonomous Water & Acoustic Fire Extinguisher

![Design](img/design.png)

An intelligent fire-fighting robot powered by Raspberry Pi and YOLOv11, featuring autonomous patrol, fire detection, and dual-mode suppression using acoustic waves and water spray.

---

## 🔥 Overview

Fires spreading in urban areas are common, especially in residential neighborhoods where wooden houses are closely spaced with little separation between them (Ondie & Bowman, 2025). AIPAWE is an autonomous robot designed to detect and extinguish fires using a combination of:

- **AI-powered fire detection** using YOLOv11 computer vision
- **Acoustic wave suppression** (eco-friendly, first response)
- **Water-based suppression** (backup/combined attack)
- **Autonomous 360° patrol** and monitoring

---

## 🤖 Robot Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                    FIRE-FIGHTING ROBOT                        │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────┐      │
│  │   Camera    │───→│   YOLOv11    │───→│  Detection  │      │
│  │  (Vision)   │    │ Fire Model   │    │   Engine    │      │
│  └─────────────┘    └──────────────┘    └──────┬──────┘      │
│                                                 │             │
│                                                 ↓             │
│  ┌──────────────────────────────────────────────────────┐    │
│  │         ROBOT CONTROLLER (Raspberry Pi)              │    │
│  │  ┌────────────┐  ┌────────────┐  ┌──────────────┐   │    │
│  │  │  Scanning  │  │ Targeting  │  │ Suppression  │   │    │
│  │  │   Logic    │  │   Logic    │  │   Control    │   │    │
│  │  └────────────┘  └────────────┘  └──────────────┘   │    │
│  └──────┬──────────────┬────────────────┬──────────────┘    │
│         │              │                │                   │
│         ↓              ↓                ↓                   │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────────────┐      │
│  │  Stepper    │ │   Servos    │ │   Suppression    │      │
│  │   Motor     │ │  (Elbow +   │ │     System       │      │
│  │ (Shoulder)  │ │   Wrist)    │ │                  │      │
│  └─────────────┘ └─────────────┘ │ ┌──────────────┐ │      │
│        │               │          │ │    Audio     │ │      │
│        ↓               ↓          │ │  Amplifier   │ │      │
│  ┌──────────────────────────┐    │ └──────────────┘ │      │
│  │     Robot Arm            │    │ ┌──────────────┐ │      │
│  │  - 360° base rotation    │    │ │ Water Pump   │ │      │
│  │  - Dual elbow servos     │    │ │   & Relay    │ │      │
│  │  - Camera/speaker tilt   │    │ └──────────────┘ │      │
│  └──────────────────────────┘    └──────────────────┘      │
│                                                             │
│  ┌──────────────────────────────────────────────────┐      │
│  │  GSM Module (SIM800L) - SMS Alerts (Optional)    │      │
│  └──────────────────────────────────────────────────┘      │
│                                                             │
└───────────────────────────────────────────────────────────────┘
```

---

## ⚙️ System Components

### Hardware
- **Raspberry Pi 4** - Main controller
- **Camera** - Fire detection vision system
- **A4988 Stepper Motor** - 360° shoulder base rotation
- **4× Servo Motors** - Elbow (2×) and wrist (2×) joints
- **PCA9685 Servo Controller** - 16-channel PWM driver
- **TPA3116D2 Audio Amplifier** - Acoustic wave generation
- **12V DC Water Pump** - Water-based suppression
- **Relay Module** - Pump control
- **SIM800L GSM Module** - SMS emergency alerts (optional)

### Software
- **YOLOv11** - Real-time fire detection
- **Custom robot control** - Autonomous patrol and targeting
- **Fire suppression coordinator** - Multi-phase suppression protocol
- **Alert system** - SMS notifications

---

## 🚀 Features

### 🔍 Autonomous Fire Detection
- Continuous 360° scanning patrol
- YOLOv11-based real-time fire detection
- Automatic target acquisition and tracking
- Confidence-based threat assessment

### 🎯 Precision Targeting
- Calculates fire position from camera frame
- Automatically points arm at detected fire
- Multi-joint coordination (shoulder, elbow, wrist)
- Visual servo control for accuracy

### 💧 Dual-Mode Suppression

**Phase 1: Acoustic Suppression**
- Low-frequency sound waves (30-120 Hz)
- Disrupts oxygen supply to flames
- Eco-friendly, no chemicals
- Effective on small-medium fires

**Phase 2: Combined Attack**
- Simultaneous acoustic + water spray
- Maximum suppression effectiveness
- Automated pulse patterns
- Intelligent cooldown management

### 📱 Smart Alerts
- Real-time SMS notifications
- Fire detection alerts
- Suppression status updates
- GSM-based remote monitoring

---

## 📂 Project Structure

```
AIPAWE/
├── main.py                     # 🚀 Main robot controller (RUN THIS)
├── config.py                   # ⚙️ Configuration settings
├── test_robot.py              # 🧪 Hardware test suite
├── QUICK_START.md             # 📖 Quick start guide
├── ROBOT_README.md            # 📚 Complete documentation
├── WIRING_GUIDE.md            # 🔌 Wiring instructions
│
├── model/
│   └── weights/
│       └── v1.pt              # 🤖 YOLOv11 fire detection model
│
└── utils/
    ├── robot_arm.py           # 🦾 Robot arm controller
    ├── fire_suppression.py    # 🔥 Suppression coordinator
    ├── pump.py                # 💧 Water pump control
    ├── audio.py               # 🔊 Acoustic wave generator
    ├── stepper.py             # ⚙️ Stepper motor driver
    ├── servo.py               # 🎛️ Servo controller
    ├── inference.py           # 👁️ YOLO inference utilities
    └── sim800l.py             # 📱 GSM communication
```

---

## 🏃 Quick Start

### 1. Installation
```bash
# Clone repository
git clone https://github.com/AlienWolfX/AIPAWE.git
cd AIPAWE

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Hardware Setup
- Follow [WIRING_GUIDE.md](WIRING_GUIDE.md) for connections
- Enable I2C and Camera on Raspberry Pi
- Place YOLOv11 model at `model/weights/v1.pt`

### 3. Test System
```bash
python test_robot.py
```

### 4. Run Robot
```bash
python main.py
```

**For detailed instructions, see [QUICK_START.md](QUICK_START.md)**

---

## 📊 Roadmap

### Core Features
- [x] YOLOv11 fire detection inference
- [x] Servo motor control (PCA9685)
- [x] Stepper motor control (A4988)
- [x] Audio amplifier integration
- [x] Water pump control
- [x] Robot arm coordination
- [x] Fire suppression protocol
- [x] Autonomous 360° scanning
- [x] SMS/GSM alerts (SIM800L)

### Advanced Features (Future)
- [ ] Multi-fire tracking
- [ ] Temperature sensing
- [ ] Smoke detection
- [ ] Auto-recharge station
- [ ] Remote control interface
- [ ] Machine learning refinement
- [ ] Fleet coordination
- [ ] Cloud monitoring dashboard

---

## 📖 Documentation

- **[QUICK_START.md](QUICK_START.md)** - Get running in 5 minutes
- **[ROBOT_README.md](ROBOT_README.md)** - Complete system documentation
- **[WIRING_GUIDE.md](WIRING_GUIDE.md)** - Hardware wiring instructions
- **[config.py](config.py)** - Configuration parameters

---

## 🎯 Usage

### Basic Operation
```bash
# Start robot
python main.py

# Robot will:
# 1. Initialize all systems
# 2. Begin 360° patrol
# 3. Scan for fires
# 4. Engage and suppress when detected
# 5. Return to patrol mode
```

### Configuration
Edit [config.py](config.py):
```python
# Adjust detection sensitivity
YOLO_CONFIG = {
    'conf_threshold': 0.25,  # Detection confidence (0.0-1.0)
}

# Set emergency contact
SIM800L_CONFIG = {
    'emergency_phone': "+1234567890",
}

# Customize suppression
SUPPRESSION_CONFIG = {
    'acoustic_duration': 6.0,  # Acoustic phase duration
    'combined_duration': 6.0,  # Combined phase duration
}
```

---

## 🧪 Testing

### Individual Components
```bash
# Test robot arm
python utils/robot_arm.py

# Test fire suppression
python utils/fire_suppression.py

# Test water pump
python utils/pump.py

# Test audio system
python utils/audio.py
```

### Full System Test
```bash
python test_robot.py
```

---

## 🛡️ Safety

⚠️ **IMPORTANT WARNINGS**
- Never leave robot unattended during operation
- Always have fire extinguisher ready
- Test in safe, controlled environments
- This is NOT a replacement for professional fire services
- Follow local fire safety regulations
- Ensure proper waterproofing of electronics

---

## 📚 Technical Details

### Fire Detection
- **Model**: YOLOv11 (custom trained)
- **Input size**: 320×320 pixels
- **Confidence threshold**: 25% (configurable)
- **Inference speed**: ~30 FPS on Raspberry Pi 4

### Mechanical System
- **Shoulder rotation**: 360° continuous via stepper motor
- **Elbow range**: Dual servo, 0-180°
- **Wrist tilt**: Dual servo (camera + speaker), 0-180°
- **Positioning accuracy**: ±5° (with calibration)

### Suppression Performance
- **Acoustic frequency**: 30-120 Hz sweep
- **Acoustic duration**: 6 seconds (default)
- **Water pump**: 12V DC, ~2L/min
- **Combined attack**: 6 seconds (default)
- **Total protocol time**: ~16 seconds

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

[Specify your license]

---

## 👨‍💻 Author

**Allen Cruiz**
- Email: cruizallen2@gmail.com
- GitHub: [@AlienWolfX](https://github.com/AlienWolfX)

---

## 🙏 Acknowledgments

- **Ultralytics** - YOLOv11 framework
- **Adafruit** - CircuitPython libraries
- Research on acoustic fire suppression
- Open-source robotics community

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/AlienWolfX/AIPAWE/issues)
- **Email**: cruizallen2@gmail.com
- **Documentation**: See docs in repository

---

## 📖 Citation

If you use this project in research, please cite:

```
Ondie, S., & Bowman, J. (2025). Urban Fire Spread Patterns in Residential Areas.
Journal of Fire Safety Research.
```

---

**⚠️ Disclaimer**: This project is for educational and research purposes. Always follow professional fire safety protocols and local regulations. This robot is not certified firefighting equipment.