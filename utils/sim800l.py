import serial
import time


class SIM800L:

    def __init__(self, port='/dev/serial0', baudrate=9600, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial = None
        
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )
            time.sleep(2) 
            print(f"SIM800L connected on {self.port} at {self.baudrate} baud")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize SIM800L: {e}")
    
    def send_at_command(self, command, timeout=1, expected_response="OK"):
        if not self.serial or not self.serial.is_open:
            return False, "Serial port not open"
        
        self.serial.reset_input_buffer()
        
        cmd = command.strip() + '\r\n'
        self.serial.write(cmd.encode())
        
        start_time = time.time()
        response = ""
        
        while (time.time() - start_time) < timeout:
            if self.serial.in_waiting > 0:
                response += self.serial.read(self.serial.in_waiting).decode('utf-8', errors='ignore')
                
                if expected_response in response:
                    return True, response
                
                if "ERROR" in response:
                    return False, response
            
            time.sleep(0.1)
        
        return False, response
    
    def send_sms(self, phone_number, message):
        success, _ = self.send_at_command("AT+CMGF=1", timeout=2)
        if not success:
            print("Failed to set SMS text mode")
            return False
        
        time.sleep(0.5)
        
        cmd = f'AT+CMGS="{phone_number}"'
        self.serial.write((cmd + '\r\n').encode())
        time.sleep(1)
        
        self.serial.write((message + chr(26)).encode())
        
        start_time = time.time()
        response = ""
        
        while (time.time() - start_time) < 10:
            if self.serial.in_waiting > 0:
                response += self.serial.read(self.serial.in_waiting).decode('utf-8', errors='ignore')
                
                if "+CMGS:" in response or "OK" in response:
                    print(f"SMS sent successfully to {phone_number}")
                    return True
                
                if "ERROR" in response:
                    print(f"Failed to send SMS: {response}")
                    return False
            
            time.sleep(0.1)
        
        print("SMS send timeout")
        return False
    
    def close(self):
        """Close serial connection"""
        if self.serial and self.serial.is_open:
            self.serial.close()
            print("SIM800L connection closed")


if __name__ == "__main__":
    sim = SIM800L(port='/dev/serial0', baudrate=9600)
    
    try:
        phone = "+1234567890" 
        message = "Hello from Raspberry Pi!"
        
        print(f"Sending SMS to {phone}...")
        if sim.send_sms(phone, message):
            print("✓ SMS sent successfully")
        else:
            print("✗ Failed to send SMS")
        
    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        sim.close()
