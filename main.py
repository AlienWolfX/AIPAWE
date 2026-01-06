from utils.inference import infer_camera
from utils.servo import PCA9685ServoController
import time


def test_servos():
	"""Test servo motors on channels 0 to 3"""
	print("Initializing PCA9685 servo controller...")
	servo = PCA9685ServoController(channels=16)
	
	try:
		print("\nMoving servos 0-3 in sequence...")
		
		for channel in range(4):
			print(f"\n--- Testing Servo {channel} ---")
			
			print(f"Servo {channel}: Moving to 0°")
			servo.set_angle(channel, 0)
			time.sleep(1)
			
			print(f"Servo {channel}: Moving to 90°")
			servo.set_angle(channel, 90)
			time.sleep(1)
			
			print(f"Servo {channel}: Moving to 180°")
			servo.set_angle(channel, 180)
			time.sleep(1)
			
			print(f"Servo {channel}: Returning to center (90°)")
			servo.set_angle(channel, 90)
			time.sleep(1)
		
		print("\n✓ All servos tested successfully")
		
	except KeyboardInterrupt:
		print("\nStopped by user")
	except Exception as e:
		print(f"Error: {e}")
	finally:
		print("\nCentering and disabling all servos...")
		for channel in range(4):
			servo.set_angle(channel, 90)
		time.sleep(0.5)
		servo.disable_all()
		servo.deinit()
		print("Servos disabled and cleaned up")


def main():
	test_servos()
	
	# Uncomment to run camera inference
	# infer_camera(imgsz=320, conf=0.25, show_preview=True)


if __name__ == "__main__":
	main()
