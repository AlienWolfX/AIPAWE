"""
AIPAWE - AI-Powered Automated Water Extinguisher
Main control program for ceiling-mounted robotic fire suppression system

State Machine Flow:
    SCAN → DETECT → SOUND → VERIFY → WATER → VERIFY → REPORT → RETURN → SCAN

Features:
    - 360° continuous scanning with NEMA17 stepper motor
    - YOLOv11 fire detection
    - Multi-target queue processing
    - Audio suppression (low-frequency) then water spray
    - SMS notifications via SIM800L
    - Hot-reloadable configuration
    - Safety interlocks and watchdog
"""

import os
import sys
import signal
import time
import atexit
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.utils_common import ConfigLoader, safe_gpio_cleanup, ensure_directory
from utils.logger import AIPAWELogger
from utils.stepper_base import StepperBase
from utils.servo_arm import ServoArm
from utils.audio_out import AudioSuppressor
from utils.water_control import WaterPump
from utils.fire_detector import FireDetector
from utils.notifier import SMSNotifier
from utils.state_machine import StateMachine, State


class AIPAWE:
    """Main AIPAWE system controller"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize AIPAWE system"""
        print("=" * 60)
        print("AIPAWE - AI-Powered Automated Water Extinguisher")
        print("=" * 60)
        
        # Load configuration
        self.config = ConfigLoader(config_path)
        
        # Initialize logger
        ensure_directory('logs')
        self.logger = AIPAWELogger(self.config)
        self.logger.info("AIPAWE system starting...")
        
        # Initialize hardware components
        self.logger.info("Initializing hardware components...")
        
        self.stepper = StepperBase(self.config, self.logger)
        self.servo = ServoArm(self.config, self.logger)
        self.audio = AudioSuppressor(self.config, self.logger)
        self.water = WaterPump(self.config, self.logger)
        self.detector = FireDetector(self.config, self.logger)
        self.notifier = SMSNotifier(self.config, self.logger)
        
        # Initialize state machine
        self.logger.info("Initializing state machine...")
        self.state_machine = StateMachine(
            self.config,
            self.logger,
            self.stepper,
            self.servo,
            self.audio,
            self.water,
            self.detector,
            self.notifier
        )
        
        # System state
        self.running = False
        self.last_config_check = time.time()
        self.config_check_interval = 5.0  # Check config every 5 seconds
        
        self.logger.info("AIPAWE system initialized successfully")
        print("System initialized. Press Ctrl+C to stop.")
    
    def run(self):
        """Main control loop"""
        self.running = True
        
        try:
            while self.running:
                # Check for configuration changes
                if time.time() - self.last_config_check > self.config_check_interval:
                    if self.config.reload_if_changed():
                        self.logger.info("Configuration reloaded")
                        self.logger.reload_config(self.config)
                    self.last_config_check = time.time()
                
                # Run state machine cycle
                continue_running = self.state_machine.run_cycle()
                
                if not continue_running:
                    self.logger.warning("State machine requested shutdown")
                    self.running = False
                
                # Small delay to prevent CPU spinning
                time.sleep(0.05)
                
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
            self.shutdown()
        except Exception as e:
            self.logger.critical(f"Fatal error: {e}")
            self.emergency_shutdown()
    
    def shutdown(self):
        """Graceful shutdown"""
        self.logger.info("Initiating graceful shutdown...")
        self.running = False
        
        # Stop state machine
        self.state_machine.transition_to(State.RETURN)
        time.sleep(1)
        
        # Cleanup hardware
        self.logger.info("Cleaning up hardware components...")
        
        self.stepper.cleanup()
        self.servo.cleanup()
        self.audio.cleanup()
        self.water.cleanup()
        self.detector.cleanup()
        self.notifier.cleanup()
        
        safe_gpio_cleanup()
        
        self.logger.info("AIPAWE system shutdown complete")
        print("\nSystem shutdown complete.")
    
    def emergency_shutdown(self):
        """Emergency shutdown - fastest possible stop"""
        self.logger.critical("EMERGENCY SHUTDOWN")
        
        try:
            self.state_machine.emergency_stop()
        except:
            pass
        
        try:
            self.stepper.stop_scanning()
            self.stepper.disable()
        except:
            pass
        
        try:
            self.audio.stop()
        except:
            pass
        
        try:
            self.water.stop()
        except:
            pass
        
        safe_gpio_cleanup()
        
        self.logger.critical("Emergency shutdown complete")
    
    def get_status(self) -> dict:
        """Get system status"""
        return {
            'running': self.running,
            'state_machine': self.state_machine.get_status(),
            'config_loaded': self.config.config is not None
        }


def signal_handler(signum, frame):
    """Handle system signals"""
    print("\nSignal received, shutting down...")
    sys.exit(0)


def main():
    """Main entry point"""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Determine config path
    config_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "config.yaml"
    )
    
    # Create and run AIPAWE system
    aipawe = AIPAWE(config_path)
    
    # Register cleanup on exit
    atexit.register(aipawe.shutdown)
    
    # Run main loop
    aipawe.run()


if __name__ == "__main__":
    main()
