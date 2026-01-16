# Fire-Fighting Robot - Wiring Guide

## 🔌 Complete Wiring Diagram

### Power Distribution

```
┌─────────────────────────────────────────────────────────────┐
│                     POWER DISTRIBUTION                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  12V Power Supply (5A+)                                     │
│  ├──→ Stepper Motor Driver (A4988)                          │
│  ├──→ Water Pump (via Relay)                                │
│  └──→ DC-DC Buck Converter → 5V (3A+)                       │
│       ├──→ Raspberry Pi                                     │
│       ├──→ PCA9685 Servo Controller                         │
│       ├──→ 4× Servo Motors                                  │
│       └──→ SIM800L GSM Module (optional)                    │
│                                                             │
│  TPA3116D2 Audio Amplifier                                  │
│  └──→ Separate 12-24V Power Supply (2A+)                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📍 Component Connections

### 1. Raspberry Pi GPIO Pinout

```
Raspberry Pi 4 GPIO (BCM numbering)
┌─────────────────────────────────────┐
│                                     │
│  3.3V  [ 1] [ 2]  5V                │
│  SDA   [ 3] [ 4]  5V                │
│  SCL   [ 5] [ 6]  GND               │
│  GPIO4 [ 7] [ 8]  GPIO14 (TX)       │
│  GND   [ 9] [10]  GPIO15 (RX)       │
│  MS1   [11] [12]  GPIO18 (PUMP)     │──→ Relay Module
│  MS2   [13] [14]  GND               │
│  GPIO15[15] [16]  GPIO23 (DIR)      │──→ Stepper DIR
│  3.3V  [17] [18]  GPIO24 (STEP)     │──→ Stepper STEP
│  GPIO10[19] [20]  GND               │
│  GPIO9 [21] [22]  GPIO25 (ENABLE)   │──→ Stepper ENABLE
│  GPIO11[23] [24]  GPIO8             │
│  GND   [25] [26]  GPIO7             │
│  GPIO0 [27] [28]  GPIO1             │
│  GPIO5 [29] [30]  GND               │
│  GPIO6 [31] [32]  GPIO12            │
│  MS3   [33] [34]  GND               │
│  GPIO19[35] [36]  GPIO16            │
│  GPIO26[37] [38]  GPIO20            │
│  GND   [39] [40]  GPIO21            │
│                                     │
└─────────────────────────────────────┘

Pin Assignments:
  GPIO 2  (Pin 3)  → I2C SDA (PCA9685)
  GPIO 3  (Pin 5)  → I2C SCL (PCA9685)
  GPIO 17 (Pin 11) → Stepper MS1
  GPIO 27 (Pin 13) → Stepper MS2
  GPIO 22 (Pin 15) → Stepper MS3
  GPIO 23 (Pin 16) → Stepper DIR
  GPIO 24 (Pin 18) → Stepper STEP
  GPIO 25 (Pin 22) → Stepper ENABLE
  GPIO 18 (Pin 12) → Water Pump Relay
```

---

### 2. A4988 Stepper Motor Driver

```
A4988 Stepper Driver Connections
┌──────────────────────────────────────────┐
│                                          │
│  VMOT  ←─ 12V Power Supply (+)           │
│  GND   ←─ 12V Power Supply (-) & RPi GND │
│  VDD   ←─ 5V (from RPi or Buck)          │
│  GND   ←─ GND (Common)                   │
│                                          │
│  STEP  ←─ GPIO 24                        │
│  DIR   ←─ GPIO 23                        │
│  ENABLE←─ GPIO 25                        │
│  MS1   ←─ GPIO 17                        │
│  MS2   ←─ GPIO 22                        │
│  MS3   ←─ GPIO 27                        │
│                                          │
│  1A    ─→ Stepper Motor Coil A+          │
│  1B    ─→ Stepper Motor Coil A-          │
│  2A    ─→ Stepper Motor Coil B+          │
│  2B    ─→ Stepper Motor Coil B-          │
│                                          │
└──────────────────────────────────────────┘

IMPORTANT: Adjust current limit potentiometer!
  Formula: Vref = Current_Limit × 8 × Rsense
  For 1A: Vref ≈ 0.4V (measure with multimeter)
```

---

### 3. PCA9685 Servo Controller

```
PCA9685 16-Channel Servo Driver
┌──────────────────────────────────────────┐
│                                          │
│  VCC   ←─ 5V (from Buck Converter)       │
│  GND   ←─ GND (Common)                   │
│  SDA   ←─ GPIO 2 (RPi Pin 3)             │
│  SCL   ←─ GPIO 3 (RPi Pin 5)             │
│                                          │
│  V+    ←─ 5V Servo Power (3A+)           │
│  GND   ←─ GND (Common)                   │
│                                          │
│  CH0   ─→ Elbow Servo 1 (Signal)         │
│  CH1   ─→ Elbow Servo 2 (Signal)         │
│  CH2   ─→ Wrist Servo 1 (Camera)         │
│  CH3   ─→ Wrist Servo 2 (Speaker)        │
│                                          │
└──────────────────────────────────────────┘

I2C Address: 0x40 (default)
  - Check with: sudo i2cdetect -y 1
  - Should show "40" in the scan
```

---

### 4. Servo Motor Connections

```
Each Servo Motor (×4)
┌──────────────────────────────────────────┐
│                                          │
│  Brown/Black  ←─ GND                     │
│  Red          ←─ 5V (from PCA9685 V+)    │
│  Orange/White ←─ Signal (from PCA9685)   │
│                                          │
└──────────────────────────────────────────┘

Servo 1 (Elbow) → PCA9685 Channel 0
Servo 2 (Elbow) → PCA9685 Channel 1
Servo 3 (Wrist) → PCA9685 Channel 2
Servo 4 (Wrist) → PCA9685 Channel 3

IMPORTANT: 
  - Use thick wires (18-20 AWG) for power
  - Add 1000μF capacitor across V+ and GND
  - Servos can draw 1-2A each under load
```

---

### 5. Water Pump & Relay Module

```
Relay Module (5V)
┌──────────────────────────────────────────┐
│                                          │
│  VCC   ←─ 5V (from RPi or Buck)          │
│  GND   ←─ GND (Common)                   │
│  IN    ←─ GPIO 18                        │
│                                          │
│  COM   ←─ 12V Power Supply (+)           │
│  NO    ─→ Water Pump (+)                 │
│  NC    (not used)                        │
│                                          │
│  Water Pump (-)  ←─ 12V Power Supply (-) │
│                                          │
└──────────────────────────────────────────┘

Relay Type: SPST or SPDT
  - Coil: 5V DC
  - Contact Rating: 10A @ 250VAC minimum
  - Use flyback diode if not built-in
```

---

### 6. TPA3116D2 Audio Amplifier

```
TPA3116D2 Audio Module
┌──────────────────────────────────────────┐
│                                          │
│  DC+ (12-24V)  ←─ Separate Power Supply  │
│  DC-           ←─ GND (Common)           │
│                                          │
│  Audio L  ←─ RPi 3.5mm Jack (Left)       │
│  Audio R  ←─ RPi 3.5mm Jack (Right)      │
│  GND      ←─ RPi 3.5mm Jack (Ground)     │
│                                          │
│  Speaker L+  ─→ Left Speaker (+)         │
│  Speaker L-  ─→ Left Speaker (-)         │
│  Speaker R+  ─→ Right Speaker (+)        │
│  Speaker R-  ─→ Right Speaker (-)        │
│                                          │
└──────────────────────────────────────────┘

Speakers: 8Ω, 50W recommended
  - Use fire-resistant speaker cone
  - Position near fire (on wrist joint)
```

---

### 7. Camera Connection

```
Camera Options
┌──────────────────────────────────────────┐
│                                          │
│  Option 1: Raspberry Pi Camera Module   │
│  └─ CSI Ribbon Cable → RPi CSI Port     │
│                                          │
│  Option 2: USB Webcam                   │
│  └─ USB Cable → RPi USB Port            │
│                                          │
└──────────────────────────────────────────┘

Position: Mounted on wrist joint
Enable Camera:
  sudo raspi-config → Interface → Camera → Enable
```

---

### 8. SIM800L GSM Module (Optional)

```
SIM800L Module
┌──────────────────────────────────────────┐
│                                          │
│  VCC (4.2V)  ←─ Use dedicated regulator  │
│  GND         ←─ GND (Common)             │
│  TXD         ←─ RPi RX (GPIO 15)         │
│  RXD         ←─ RPi TX (GPIO 14)         │
│                                          │
└──────────────────────────────────────────┘

WARNING: SIM800L is 3.3V logic but needs 4.2V power
  - Use voltage regulator: 5V → 4.2V
  - Current: Can spike to 2A during transmission
  - Add large capacitor (1000μF+) near VCC
```

---

## 🛠️ Assembly Steps

### Step 1: Power Supply Setup

1. **Main 12V Supply** (5A minimum):
   - Connect to stepper driver VMOT
   - Connect to relay COM terminal
   - Connect to DC-DC buck converter input

2. **Buck Converter** (12V → 5V, 3A):
   - Adjust output to exactly 5.0V
   - Connect output to:
     - Raspberry Pi (via GPIO or USB-C)
     - PCA9685 VCC
     - PCA9685 V+ (servo power)
     - Relay module VCC

3. **Audio Amplifier Power** (separate 12-24V, 2A):
   - Use isolated power supply if possible
   - Or use same 12V with proper filtering

### Step 2: Ground Network

**CRITICAL**: All grounds must be connected together:
- Raspberry Pi GND
- Stepper driver GND
- PCA9685 GND
- All servo GND
- Relay module GND
- Water pump GND
- Audio amplifier GND
- Power supply GND

Use thick wire (18 AWG) for ground network.

### Step 3: I2C Bus

1. Enable I2C on Raspberry Pi:
   ```bash
   sudo raspi-config
   # Interface Options → I2C → Enable
   ```

2. Connect PCA9685:
   - SDA → GPIO 2 (Pin 3)
   - SCL → GPIO 3 (Pin 5)
   - Add 4.7kΩ pull-up resistors if needed

3. Verify connection:
   ```bash
   sudo i2cdetect -y 1
   # Should show "40" at address 0x40
   ```

### Step 4: Stepper Motor

1. Wire NEMA 17 motor to A4988:
   - Identify coil pairs with multimeter
   - Coil A → 1A, 1B
   - Coil B → 2A, 2B

2. Adjust current limit:
   - Measure Vref on potentiometer
   - Adjust to 0.4V for 1A limit
   - Use ceramic screwdriver

3. Connect control pins:
   - STEP → GPIO 24
   - DIR → GPIO 23
   - ENABLE → GPIO 25
   - MS1, MS2, MS3 for microstepping

### Step 5: Servos

1. Connect servo signal wires to PCA9685:
   - Channel 0: Elbow Servo 1
   - Channel 1: Elbow Servo 2
   - Channel 2: Wrist Servo 1 (Camera)
   - Channel 3: Wrist Servo 2 (Speaker)

2. **Important**: Add 1000μF capacitor between V+ and GND
   - Place close to PCA9685
   - Prevents voltage dips during servo movement

3. Use separate thick power wires for servos

### Step 6: Water Pump

1. Connect relay module:
   - VCC → 5V
   - GND → GND
   - IN → GPIO 18

2. Wire pump through relay:
   - 12V (+) → Relay COM
   - Relay NO → Pump (+)
   - Pump (-) → 12V (-)

3. Add flyback diode across pump if needed

### Step 7: Audio System

1. Connect RPi audio output to TPA3116D2:
   - Use 3.5mm cable
   - Left → Audio L
   - Right → Audio R
   - Ground → GND

2. Connect speakers:
   - 8Ω speakers recommended
   - Mount speaker on wrist joint

3. Set RPi audio output:
   ```bash
   amixer cset numid=3 1  # Force 3.5mm jack
   ```

### Step 8: Camera

- **Pi Camera**: Connect ribbon cable to CSI port
- **USB Webcam**: Connect to USB port
- Mount on wrist joint for fire detection

---

## ⚠️ Safety Checklist

Before powering on:

- [ ] All ground connections verified
- [ ] No short circuits (use multimeter)
- [ ] Power supply voltage correct (12V, 5V)
- [ ] Stepper current limit adjusted
- [ ] Servo capacitor installed
- [ ] Relay wiring correct (NO/NC)
- [ ] Water pump properly sealed
- [ ] All wires secured and insulated
- [ ] Emergency stop button accessible
- [ ] Fire extinguisher nearby

---

## 🔧 Testing Sequence

1. **Power only Raspberry Pi** (no motors)
   - Check boot, SSH access

2. **Add PCA9685**
   - Run `i2cdetect -y 1`
   - Should see address 0x40

3. **Add one servo**
   - Test with `python utils/servo.py`
   - Check smooth movement

4. **Add stepper motor**
   - Test with `python utils/stepper.py`
   - Start with small movements

5. **Add water pump**
   - Test relay click
   - Test pump briefly

6. **Full system test**
   - Run `python test_robot.py`

---

## 📏 Mechanical Assembly Notes

### Shoulder Joint
- Stepper motor mounted on base
- 7-inch tube attached to motor shaft
- Use flexible coupling if needed
- Bearing support for tube stability

### Elbow Joint
- Two servos work in parallel
- Mounted at end of 7-inch tube
- Use servo horns and linkages
- Allow 90-180° range of motion

### Wrist Joint
- Two servos for camera and speaker
- Mounted at end of elbow assembly
- Independent tilt control
- Cable management for camera/speaker

---

## 🔌 Wire Gauge Recommendations

| Component          | Wire Gauge | Length     |
|--------------------|------------|------------|
| 12V Power Supply   | 14-16 AWG  | As needed  |
| 5V Power Rails     | 16-18 AWG  | Short      |
| Servo Power        | 18 AWG     | < 1m       |
| Servo Signals      | 22-24 AWG  | As needed  |
| Stepper Motor      | 20-22 AWG  | < 1m       |
| GPIO Control       | 24-26 AWG  | As needed  |
| Ground Network     | 16-18 AWG  | Short      |
| Water Pump         | 18 AWG     | < 2m       |

---

## 📞 Troubleshooting

**Stepper not moving:**
- Check enable pin (should be LOW)
- Verify current limit setting
- Check power supply voltage
- Measure coil resistance

**Servos jittering:**
- Add/increase capacitor value
- Check power supply current rating
- Reduce number of simultaneous movements
- Check signal wire quality

**I2C not detected:**
- Enable I2C in raspi-config
- Check SDA/SCL connections
- Try external pull-up resistors
- Check for address conflicts

**Relay not clicking:**
- Verify GPIO output with multimeter
- Check relay coil voltage
- Test with external 5V source
- Replace relay if faulty

---

## 📐 Recommended Components

**Stepper Motor:**
- NEMA 17, 1.5A, 1.8° step angle
- Holding torque: 40+ N⋅cm

**Servos:**
- MG996R or DS3218 (metal gear)
- Torque: 10+ kg⋅cm
- Continuous rotation not required

**Power Supplies:**
- 12V 5A switching supply (main)
- Buck converter: LM2596 (5V 3A)
- Optional: 12V 2A (audio amplifier)

**Relay:**
- 5V coil, 10A contacts
- SPST or SPDT with flyback diode

**Capacitors:**
- 1000μF 16V electrolytic (servos)
- 100μF 25V electrolytic (stepper)
- 10μF ceramic (noise filtering)
