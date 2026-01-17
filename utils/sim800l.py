import serial
import time
import platform

def init_sim800l(port=None, baudrate=9600, timeout=1):
    """Initialize SIM800L module"""
    if port is None:
        if platform.system() == 'Windows':
            port = 'COM8' # Change
        else:
            port = '/dev/ttyAMA0' 
    
    try:
        ser = serial.Serial(port, baudrate, timeout=timeout)
        time.sleep(2)
        print(f"✓ SIM800L initialized on {port}")
        return ser
    except serial.SerialException as e:
        print(f"✗ Serial Failed: Could not open {port}")
        return None
    except Exception as e:
        print(f"✗ Serial Failed: {e}")
        return None


def send_at_command(ser, command, wait_time=1):
    """Send AT command to SIM800L"""
    ser.write((command + '\r\n').encode())
    time.sleep(wait_time)
    response = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
    return response


def get_imei(ser):
    """Get IMEI number from SIM800L"""
    response = send_at_command(ser, 'AT+GSN')
    lines = response.strip().split('\n')
    for line in lines:
        if line.strip().isdigit() and len(line.strip()) == 15:
            return line.strip()
    return None


def send_sms(ser, phone_number, message):
    """Send SMS message"""
    send_at_command(ser, 'AT+CMGF=1')
    send_at_command(ser, f'AT+CMGS="{phone_number}"', 0.5)
    ser.write((message + chr(26)).encode()) 
    time.sleep(2)
    response = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
    return response
