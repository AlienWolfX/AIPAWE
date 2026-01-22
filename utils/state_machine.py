"""
AIPAWE - State Machine Controller
Orchestrates fire suppression workflow: SCAN → DETECT → SOUND → VERIFY → WATER → VERIFY → REPORT → RETURN
"""

import time
from enum import Enum, auto
from typing import Optional, List
from collections import deque
from dataclasses import dataclass

from utils.fire_detector import FireDetection


class State(Enum):
    """System states"""
    SCAN = auto()
    DETECT = auto()
    SOUND = auto()
    VERIFY_SOUND = auto()
    WATER = auto()
    VERIFY_WATER = auto()
    REPORT = auto()
    RETURN = auto()
    ERROR = auto()
    EMERGENCY_STOP = auto()


@dataclass
class SuppressionTarget:
    """Target for suppression"""
    sector: float
    azimuth: float
    elevation: float
    confidence: float
    detection: FireDetection
    attempts_sound: int = 0
    attempts_water: int = 0
    timestamp: float = 0.0


class StateMachine:
    """Main state machine controller for fire suppression system"""
    
    def __init__(self, config, logger, stepper, servo, audio, water, detector, notifier):
        self.config = config
        self.logger = logger
        
        # Hardware components
        self.stepper = stepper
        self.servo = servo
        self.audio = audio
        self.water = water
        self.detector = detector
        self.notifier = notifier
        
        # State
        self.current_state = State.SCAN
        self.previous_state = State.SCAN
        
        # Target queue
        self.target_queue: deque[SuppressionTarget] = deque(
            maxlen=config.get('state_machine', 'max_queue_size', default=10)
        )
        self.current_target: Optional[SuppressionTarget] = None
        
        # Configuration
        self.verify_delay = config.get('state_machine', 'verify_delay', default=2)
        self.return_delay = config.get('state_machine', 'return_delay', default=1)
        self.watchdog_timeout = config.get('state_machine', 'watchdog_timeout', default=300)
        
        self.max_sound_attempts = config.get('audio', 'max_attempts', default=2)
        self.max_water_attempts = config.get('water', 'max_attempts', default=3)
        self.max_total_attempts = config.get('safety', 'max_total_attempts', default=5)
        self.interlock_delay = config.get('safety', 'interlock_delay', default=0.5)
        
        # Watchdog
        self.last_state_change = time.time()
        
        # Results
        self.suppression_method = None
        self.suppression_success = False
    
    def transition_to(self, new_state: State):
        """Transition to new state"""
        self.previous_state = self.current_state
        self.current_state = new_state
        self.last_state_change = time.time()
        
        self.logger.log_state_transition(self.previous_state.name, new_state.name)
    
    def run_cycle(self) -> bool:
        """
        Execute one state machine cycle
        
        Returns:
            True to continue running, False to exit
        """
        # Watchdog check
        if time.time() - self.last_state_change > self.watchdog_timeout:
            self.logger.error(f"Watchdog timeout in state {self.current_state.name}")
            self.transition_to(State.RETURN)
        
        # Execute state
        try:
            if self.current_state == State.SCAN:
                self._state_scan()
            elif self.current_state == State.DETECT:
                self._state_detect()
            elif self.current_state == State.SOUND:
                self._state_sound()
            elif self.current_state == State.VERIFY_SOUND:
                self._state_verify_sound()
            elif self.current_state == State.WATER:
                self._state_water()
            elif self.current_state == State.VERIFY_WATER:
                self._state_verify_water()
            elif self.current_state == State.REPORT:
                self._state_report()
            elif self.current_state == State.RETURN:
                self._state_return()
            elif self.current_state == State.ERROR:
                self._state_error()
            elif self.current_state == State.EMERGENCY_STOP:
                return False
        
        except Exception as e:
            self.logger.log_error_with_recovery(e, "Transition to ERROR state")
            self.transition_to(State.ERROR)
        
        return True
    
    def _state_scan(self):
        """SCAN state: Continuous 360° scanning for fires"""
        # Start scanning if not already
        if not self.stepper.is_scanning:
            self.stepper.start_continuous_scan()
        
        # Capture and analyze frame
        detections = self.detector.detect_fires()
        
        if detections:
            # Fire detected!
            self.logger.log_fire_detected(
                self.stepper.get_current_angle(),
                detections[0].confidence
            )
            
            # Add to queue
            for detection in detections:
                target = SuppressionTarget(
                    sector=self.stepper.get_current_angle(),
                    azimuth=detection.azimuth,
                    elevation=detection.elevation,
                    confidence=detection.confidence,
                    detection=detection,
                    timestamp=time.time()
                )
                self.target_queue.append(target)
            
            # Transition to DETECT
            self.transition_to(State.DETECT)
        
        time.sleep(0.1)  # Small delay between scans
    
    def _state_detect(self):
        """DETECT state: Stop scanning and acquire target"""
        # Stop scanning
        self.stepper.stop_scanning()
        
        # Get highest priority target
        if not self.target_queue:
            # No targets, return to scanning
            self.transition_to(State.RETURN)
            return
        
        self.current_target = self.target_queue.popleft()
        
        self.logger.info(f"Target acquired: Sector={self.current_target.sector:.1f}° Az={self.current_target.azimuth:.1f}° El={self.current_target.elevation:.1f}° Conf={self.current_target.confidence:.2%}")
        
        # Calculate absolute azimuth (base angle + relative azimuth)
        target_azimuth = (self.current_target.sector + self.current_target.azimuth) % 360
        
        # Rotate base to target
        self.logger.info(f"Rotating base to {target_azimuth:.1f}°")
        self.stepper.rotate_to_angle(target_azimuth)
        
        # Aim arm at elevation
        self.logger.info(f"Aiming arm: azimuth={self.current_target.azimuth:.1f}° elevation={self.current_target.elevation:.1f}°")
        self.servo.aim_at_target(
            self.current_target.azimuth,
            self.current_target.elevation,
            smooth=True
        )
        
        # Send notification
        self.notifier.notify_fire_detected(self.current_target.sector)
        
        # Proceed to sound suppression
        self.transition_to(State.SOUND)
    
    def _state_sound(self):
        """SOUND state: Attempt audio suppression"""
        if self.current_target.attempts_sound >= self.max_sound_attempts:
            # Max sound attempts reached, try water
            self.transition_to(State.WATER)
            return
        
        self.current_target.attempts_sound += 1
        
        self.logger.log_suppression_attempt("SOUND", self.current_target.attempts_sound)
        
        # Play suppression tone
        self.audio.play_suppression_tone(blocking=True)
        
        # Interlock delay
        time.sleep(self.interlock_delay)
        
        # Proceed to verification
        self.transition_to(State.VERIFY_SOUND)
    
    def _state_verify_sound(self):
        """VERIFY_SOUND state: Check if sound suppression worked"""
        time.sleep(self.verify_delay)
        
        # Check for fire
        detections = self.detector.detect_fires()
        
        fire_still_present = False
        for det in detections:
            # Check if detection is near our target
            if abs(det.azimuth - self.current_target.azimuth) < 10.0:
                fire_still_present = True
                break
        
        if not fire_still_present:
            # Success!
            self.suppression_method = "sound"
            self.suppression_success = True
            self.logger.log_suppression_result(True, "SOUND")
            self.transition_to(State.REPORT)
        else:
            # Still burning
            self.logger.log_suppression_result(False, "SOUND")
            
            total_attempts = (self.current_target.attempts_sound + 
                            self.current_target.attempts_water)
            
            if total_attempts >= self.max_total_attempts:
                # Max attempts reached
                self.suppression_method = "sound"
                self.suppression_success = False
                self.transition_to(State.REPORT)
            elif self.current_target.attempts_sound >= self.max_sound_attempts:
                # Try water
                self.transition_to(State.WATER)
            else:
                # Retry sound
                self.transition_to(State.SOUND)
    
    def _state_water(self):
        """WATER state: Attempt water suppression"""
        if self.current_target.attempts_water >= self.max_water_attempts:
            # Max water attempts reached
            self.suppression_method = "water"
            self.suppression_success = False
            self.transition_to(State.REPORT)
            return
        
        self.current_target.attempts_water += 1
        
        self.logger.log_suppression_attempt("WATER", self.current_target.attempts_water)
        
        # Activate water pump
        self.water.start_spray(blocking=True)
        
        # Interlock delay
        time.sleep(self.interlock_delay)
        
        # Proceed to verification
        self.transition_to(State.VERIFY_WATER)
    
    def _state_verify_water(self):
        """VERIFY_WATER state: Check if water suppression worked"""
        time.sleep(self.verify_delay)
        
        # Check for fire
        detections = self.detector.detect_fires()
        
        fire_still_present = False
        for det in detections:
            if abs(det.azimuth - self.current_target.azimuth) < 10.0:
                fire_still_present = True
                break
        
        if not fire_still_present:
            # Success!
            self.suppression_method = "water"
            self.suppression_success = True
            self.logger.log_suppression_result(True, "WATER")
            self.transition_to(State.REPORT)
        else:
            # Still burning
            self.logger.log_suppression_result(False, "WATER")
            
            total_attempts = (self.current_target.attempts_sound + 
                            self.current_target.attempts_water)
            
            if total_attempts >= self.max_total_attempts:
                # Max attempts reached
                self.suppression_method = "water"
                self.suppression_success = False
                self.transition_to(State.REPORT)
            else:
                # Retry water
                self.transition_to(State.WATER)
    
    def _state_report(self):
        """REPORT state: Send SMS notification of result"""
        if self.suppression_success:
            # Fire suppressed
            self.notifier.notify_fire_suppressed(
                self.current_target.sector,
                self.suppression_method
            )
        else:
            # Suppression failed
            total_attempts = (self.current_target.attempts_sound + 
                            self.current_target.attempts_water)
            self.notifier.notify_suppression_failed(
                self.current_target.sector,
                total_attempts
            )
        
        # Proceed to return
        self.transition_to(State.RETURN)
    
    def _state_return(self):
        """RETURN state: Return to neutral and resume scanning"""
        time.sleep(self.return_delay)
        
        # Return arm to neutral
        self.servo.move_to_neutral()
        
        # Reset target
        self.current_target = None
        self.suppression_method = None
        self.suppression_success = False
        
        # Check if more targets in queue
        if self.target_queue:
            # Process next target
            self.transition_to(State.DETECT)
        else:
            # Resume scanning
            self.transition_to(State.SCAN)
    
    def _state_error(self):
        """ERROR state: Handle errors and attempt recovery"""
        self.logger.error("System in ERROR state, attempting recovery")
        
        # Stop all active components
        self.stepper.stop_scanning()
        self.audio.stop()
        self.water.stop()
        
        # Wait a moment
        time.sleep(2)
        
        # Return to scanning
        self.transition_to(State.RETURN)
    
    def emergency_stop(self):
        """Emergency stop - halt all operations"""
        self.logger.critical("EMERGENCY STOP ACTIVATED")
        
        self.stepper.stop_scanning()
        self.stepper.disable()
        self.audio.stop()
        self.water.stop()
        
        self.transition_to(State.EMERGENCY_STOP)
    
    def get_status(self) -> dict:
        """Get current system status"""
        return {
            'state': self.current_state.name,
            'scanning': self.stepper.is_scanning,
            'current_angle': self.stepper.get_current_angle(),
            'queue_size': len(self.target_queue),
            'current_target': self.current_target is not None,
            'audio_active': self.audio.is_active(),
            'water_active': self.water.is_active()
        }
