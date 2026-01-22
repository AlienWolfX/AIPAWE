#from utils.inference import infer_camera
from utils.sim800l import init_sim800l, get_imei


def test_sim800l():
    """Test SIM800L module"""
    print("\n=== Testing SIM800L ===")
    ser = init_sim800l()
    if ser:
        imei = get_imei(ser)
        if imei:
            print(f"✓ SIM800L OK (IMEI: {imei})")
        else:
            print("✗ SIM800L: No IMEI")
        ser.close()
    else:
        print("✗ SIM800L: Failed")
    print("=======================\n")


def test_audio_module():
    """Test Audio module"""
    print("\n=== Testing Audio ===")
    try:
        from utils.audio import test_audio
        test_audio()
        print("✓ Audio OK")
    except Exception as e:
        print(f"✗ Audio: {e}")
    print("=====================\n")


def test_servo_module():
    """Test Servo module"""
    print("\n=== Testing Servo ===")
    try:
        from utils.servo import PCA9685ServoController
        servo = PCA9685ServoController(channels=16)
        servo.disable_all()
        servo.deinit()
        print("✓ Servo OK")
    except NotImplementedError:
        print("⚠ Servo: Not on Raspberry Pi")
    except Exception as e:
        print(f"✗ Servo: {e}")
    print("=====================\n")


def test_stepper_module():
    """Test Stepper module"""
    print("\n=== Testing Stepper ===")
    try:
        from utils.stepper import A4988Stepper
        stepper = A4988Stepper()
        stepper.cleanup()
        print("✓ Stepper OK")
    except NotImplementedError:
        print("⚠ Stepper: Not on Raspberry Pi")
    except Exception as e:
        print(f"✗ Stepper: {e}")
    print("=======================\n")


def test_pump_module():
    """Test Water Pump module"""
    print("\n=== Testing Water Pump ===")
    try:
        from utils.pump import WaterPump
        pump = WaterPump(relay_pin=18)
        print("Testing pump pulse (1 second)...")
        pump.pulse(duration=1.0)
        pump.cleanup()
        print("✓ Water Pump OK")
    except NotImplementedError as e:
        print(f"⚠ Water Pump: Not on Raspberry Pi")
    except Exception as e:
        print(f"✗ Water Pump: {e}")
    print("==========================\n")


def test_camera_module():
    """Test Camera module"""
    print("\n=== Testing Camera ===")
    print("✓ Camera OK (placeholder)")
    print("======================\n")


def test_all():
    """Test all modules"""
    print("\n=== Testing All Modules ===")
    test_sim800l()
    test_audio_module()
    test_servo_module()
    test_stepper_module()
    test_pump_module()
    test_camera_module()
    print("===========================\n")


def display_menu():
    """Display test menu"""
    print("\n╔════════════════════════════════╗")
    print("║   AIPAWE Module Test Menu      ║")
    print("╠════════════════════════════════╣")
    print("║ 1. Test SIM800L                ║")
    print("║ 2. Test Audio                  ║")
    print("║ 3. Test Servo                  ║")
    print("║ 4. Test Stepper                ║")
    print("║ 5. Test Water Pump             ║")
    print("║ 6. Test Camera                 ║")
    print("║ 7. Test All Modules            ║")
    print("║ 0. Exit                        ║")
    print("╚════════════════════════════════╝")


def main():
    """Main test loop"""
    while True:
        display_menu()
        choice = input("\nSelect test option (0-7): ").strip()
        
        if choice == '1':
            test_sim800l()
        elif choice == '2':
            test_audio_module()
        elif choice == '3':
            test_servo_module()
        elif choice == '4':
            test_stepper_module()
        elif choice == '5':
            test_pump_module()
        elif choice == '6':
            test_camera_module()
        elif choice == '7':
            test_all()
        elif choice == '0':
            print("\nExiting test program. Goodbye!")
            break
        else:
            print("\n✗ Invalid option. Please select 0-7.")


if __name__ == "__main__":
    main()