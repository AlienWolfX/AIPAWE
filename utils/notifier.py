"""
AIPAWE - SMS Notifier Module
SIM800L GSM module interface for SMS notifications
"""

import serial
import time
from typing import List, Optional


class SMSNotifier:
    """SIM800L GSM module SMS notification system"""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        
        # Serial configuration
        self.serial_port = config.get('gsm', 'serial_port', default='/dev/ttyS0')
        self.baud_rate = config.get('gsm', 'baud_rate', default=9600)
        self.timeout = config.get('gsm', 'timeout', default=5)
        
        # Recipients
        self.phone_numbers = config.get('gsm', 'phone_numbers', default=[])
        
        # Message templates
        self.msg_fire_detected = config.get('gsm', 'messages', 'fire_detected')
        self.msg_fire_suppressed = config.get('gsm', 'messages', 'fire_suppressed')
        self.msg_suppression_failed = config.get('gsm', 'messages', 'suppression_failed')
        
        # Serial connection
        self.serial = None
        self._init_serial()
    
    def _init_serial(self):
        """Initialize serial connection to SIM800L"""
        try:
            self.serial = serial.Serial(
                port=self.serial_port,
                baudrate=self.baud_rate,
                timeout=self.timeout
            )
            time.sleep(2)  # Wait for module to initialize
            
            # Test connection
            if self._send_at_command("AT"):
                self.logger.info(f"SIM800L initialized on {self.serial_port}")
                
                # Set SMS text mode
                self._send_at_command("AT+CMGF=1")
                
                # Get and display IMEI
                imei = self.get_imei()
                if imei:
                    self.logger.info(f"SIM800L IMEI: {imei}")
                    print(f"SIM800L IMEI: {imei}")
                else:
                    self.logger.warning("Could not retrieve IMEI")
            else:
                self.logger.error("SIM800L not responding")
                self.serial = None
                
        except Exception as e:
            self.logger.error(f"Failed to initialize SIM800L: {e}")
            self.serial = None
    
    def _send_at_command(self, command: str, wait_time: float = 1.0) -> bool:
        """Send AT command and wait for OK response"""
        if self.serial is None:
            return False
        
        try:
            self.serial.write((command + '\r\n').encode())
            time.sleep(wait_time)
            
            response = self.serial.read(self.serial.in_waiting).decode('utf-8', errors='ignore')
            
            return 'OK' in response
            
        except Exception as e:
            self.logger.error(f"AT command error: {e}")
            return False
    
    def send_sms(self, phone_number: str, message: str) -> bool:
        """
        Send SMS to single recipient
        
        Args:
            phone_number: Recipient phone number with country code
            message: Message content
            
        Returns:
            True if SMS sent successfully
        """
        if self.serial is None:
            self.logger.warning("SIM800L not available - SMS not sent")
            return False
        
        try:
            # Set recipient
            cmd = f'AT+CMGS="{phone_number}"'
            self.serial.write((cmd + '\r\n').encode())
            time.sleep(0.5)
            
            # Send message
            self.serial.write((message + chr(26)).encode())  # chr(26) is Ctrl+Z
            time.sleep(2.0)
            
            # Read response
            response = self.serial.read(self.serial.in_waiting).decode('utf-8', errors='ignore')
            
            if '+CMGS' in response:
                self.logger.info(f"SMS sent to {phone_number}: '{message}'")
                return True
            else:
                self.logger.warning(f"SMS send failed to {phone_number}")
                return False
                
        except Exception as e:
            self.logger.error(f"SMS send error: {e}")
            return False
    
    def send_sms_to_all(self, message: str) -> int:
        """
        Send SMS to all configured recipients
        
        Args:
            message: Message content
            
        Returns:
            Number of successful sends
        """
        if not self.phone_numbers:
            self.logger.warning("No phone numbers configured")
            return 0
        
        success_count = 0
        
        for number in self.phone_numbers:
            if self.send_sms(number, message):
                success_count += 1
            time.sleep(1)  # Delay between messages
        
        self.logger.log_notification_sent(message, self.phone_numbers)
        
        return success_count
    
    def notify_fire_detected(self, sector: float) -> bool:
        """Send 'fire detected' notification"""
        message = self.msg_fire_detected.format(sector=sector)
        count = self.send_sms_to_all(message)
        return count > 0
    
    def notify_fire_suppressed(self, sector: float, method: str) -> bool:
        """Send 'fire suppressed' notification"""
        message = self.msg_fire_suppressed.format(sector=sector, method=method)
        count = self.send_sms_to_all(message)
        return count > 0
    
    def notify_suppression_failed(self, sector: float, attempts: int) -> bool:
        """Send 'suppression failed' notification"""
        message = self.msg_suppression_failed.format(sector=sector, attempts=attempts)
        count = self.send_sms_to_all(message)
        return count > 0
    
    def check_signal_strength(self) -> Optional[int]:
        """Check GSM signal strength (0-31)"""
        if self.serial is None:
            return None
        
        try:
            self.serial.write(b'AT+CSQ\r\n')
            time.sleep(0.5)
            
            response = self.serial.read(self.serial.in_waiting).decode('utf-8', errors='ignore')
            
            # Parse response: +CSQ: <rssi>,<ber>
            if '+CSQ:' in response:
                parts = response.split('+CSQ:')[1].split(',')
                rssi = int(parts[0].strip())
                return rssi
                
        except Exception as e:
            self.logger.error(f"Signal check error: {e}")
        
        return None
    
    def get_imei(self) -> Optional[str]:
        """Get SIM800L IMEI number"""
        if self.serial is None:
            return None
        
        try:
            self.serial.write(b'AT+GSN\r\n')
            time.sleep(0.5)
            
            response = self.serial.read(self.serial.in_waiting).decode('utf-8', errors='ignore')
            
            # Parse IMEI from response
            lines = response.strip().split('\n')
            for line in lines:
                line = line.strip()
                # IMEI is 15 digits
                if line.isdigit() and len(line) == 15:
                    return line
            
            # Alternative: sometimes IMEI comes after AT+GSN
            for line in lines:
                if 'AT+GSN' not in line and line.strip().isdigit():
                    return line.strip()
                    
        except Exception as e:
            self.logger.error(f"IMEI retrieval error: {e}")
        
        return None
    
    def cleanup(self):
        """Close serial connection"""
        if self.serial is not None:
            try:
                self.serial.close()
            except:
                pass
