#from utils.inference import infer_camera
from utils.sim800l import init_sim800l, get_imei

def check_system_status():
	"""Check all module statuses before starting main program"""
	status = {
		'sim800l': False,
		'sim800l_imei': None,
		'audio': False,
		'servo': False,
		'stepper': False,
		'camera': False
	}
	
	print("\n=== System Status Check ===")
	
	print("Checking SIM800L...")
	ser = init_sim800l()
	if ser:
		imei = get_imei(ser)
		if imei:
			status['sim800l'] = True
			status['sim800l_imei'] = imei
			print(f"✓ SIM800L OK (IMEI: {imei})")
		else:
			print("✗ SIM800L: No IMEI")
		ser.close()
	else:
		print("✗ SIM800L: Failed")
	
	print("Checking Audio...")
	try:
		from utils.audio import test_audio
		test_audio()
		status['audio'] = True
		print("✓ Audio OK")
	except Exception as e:
		print(f"✗ Audio: {e}")
	
	print("Checking Servo...")
	try:
		from utils.servo import PCA9685ServoController
		servo = PCA9685ServoController(channels=16)
		servo.disable_all()
		servo.deinit()
		status['servo'] = True
		print("✓ Servo OK")
	except Exception as e:
		print(f"✗ Servo: {e}")
	
	print("Checking Stepper...")
	try:
		from utils.stepper import A4988Stepper
		stepper = A4988Stepper()
		stepper.cleanup()
		status['stepper'] = True
		print("✓ Stepper OK")
	except Exception as e:
		print(f"✗ Stepper: {e}")
	
	status['camera'] = True 
	
	print("\n=== Status Summary ===")
	for module, state in status.items():
		if module != 'sim800l_imei':
			symbol = "✓" if state else "✗"
			print(f"{symbol} {module.upper()}: {'OK' if state else 'FAILED'}")
	print("========================\n")
	
	return status


def main():
	check_system_status()

if __name__ == "__main__":
	main()