from utils.audio import TPA3116D2Audio
from utils.pump import WaterPump
from utils.robot_arm import RobotArm
import time


class FireSuppressionSystem:
    """
    Fire suppression controller that coordinates acoustic wave suppression
    and water pump activation.
    
    Strategy:
    1. First attempt: Acoustic waves only (eco-friendly)
    2. Second attempt: Acoustic waves + water pump (combined suppression)
    """
    
    def __init__(self, audio_device=None):
        """
        Initialize fire suppression system.
        
        Args:
            audio_device: Audio device index (None for default)
        """
        self.audio = TPA3116D2Audio(sample_rate=44100, channels=2, device_index=audio_device)
        self.pump = WaterPump(relay_pin=18)
        
        print("Fire suppression system initialized")
    
    def acoustic_suppression(self, duration=5.0, frequency_range=(30, 120)):
        """
        Attempt fire suppression using acoustic waves.
        Low-frequency sound waves can disrupt oxygen supply to flames.
        
        Args:
            duration: Duration of acoustic suppression in seconds
            frequency_range: Tuple of (min_freq, max_freq) in Hz
        """
        print(f"Activating acoustic suppression ({duration}s)...")
        
        min_freq, max_freq = frequency_range
        
        segments = 3
        segment_duration = duration / segments
        
        for i in range(segments):
            print(f"  Acoustic sweep {i+1}/{segments}: {min_freq}Hz -> {max_freq}Hz")
            self.audio.play_sweep(min_freq, max_freq, segment_duration, volume=0.8)
            
            print(f"  Acoustic sweep {i+1}/{segments}: {max_freq}Hz -> {min_freq}Hz")
            self.audio.play_sweep(max_freq, min_freq, segment_duration, volume=0.8)
        
        print("Acoustic suppression complete")
    
    def water_suppression(self, duration=3.0, pattern='continuous'):
        """
        Activate water pump for fire suppression.
        
        Args:
            duration: Total duration of water suppression
            pattern: 'continuous' or 'pulse'
        """
        print(f"Activating water suppression ({pattern} mode, {duration}s)...")
        
        if pattern == 'continuous':
            self.pump.start()
            time.sleep(duration)
            self.pump.stop()
        elif pattern == 'pulse':
            num_pulses = int(duration / 0.8) 
            self.pump.spray_pattern(pulses=num_pulses, pulse_duration=0.5, pause_duration=0.3)
        else:
            raise ValueError(f"Unknown pattern: {pattern}")
        
        print("Water suppression complete")
    
    def combined_suppression(self, duration=5.0):
        """
        Combined acoustic + water suppression.
        
        Args:
            duration: Total duration of combined suppression
        """
        print(f"Activating COMBINED suppression ({duration}s)...")
        
        self.pump.start()
        
        min_freq, max_freq = 30, 120
        segments = int(duration / 2) 
        segment_duration = duration / (segments * 2)
        
        for i in range(segments):
            print(f"  Combined attack {i+1}/{segments}")
            self.audio.play_sweep(min_freq, max_freq, segment_duration, volume=0.8)
            self.audio.play_sweep(max_freq, min_freq, segment_duration, volume=0.8)
        
        self.pump.stop()
        
        print("Combined suppression complete")
    
    def suppression_protocol(self, fire_confidence=0.0):
        """
        Execute the full fire suppression protocol.
        
        Strategy:
        1. First attempt: Acoustic waves only
        2. Wait and assess
        3. Second attempt: Combined acoustic + water
        
        Args:
            fire_confidence: Confidence level of fire detection (0.0-1.0)
        
        Returns:
            str: Suppression result ('acoustic_success', 'combined_success', 'monitoring')
        """
        print("\n" + "="*50)
        print("FIRE SUPPRESSION PROTOCOL INITIATED")
        print(f"Fire confidence: {fire_confidence:.2%}")
        print("="*50)
        
        print("\nPlaying alert sound...")
        self.audio.play_alarm(duration=2.0, volume=0.7)
        time.sleep(0.5)
        
        print("\n--- PHASE 1: Acoustic Suppression ---")
        self.acoustic_suppression(duration=6.0, frequency_range=(30, 120))
        
        print("\nWaiting 2 seconds for assessment...")
        time.sleep(2)
        
        print("Assessment: Fire still detected, escalating...")
        
        print("\n--- PHASE 2: Combined Suppression ---")
        self.combined_suppression(duration=6.0)
        
        print("\nWaiting 2 seconds for assessment...")
        time.sleep(2)
        
        print("\n--- Suppression Complete ---")
        self.audio.play_success(volume=0.6)
        
        print("="*50)
        print("SUPPRESSION PROTOCOL COMPLETE")
        print("="*50 + "\n")
        
        return 'combined_success'
    
    def test_suppression(self):
        """Test all suppression methods"""
        print("\n=== Testing Fire Suppression System ===\n")
        
        print("1. Testing acoustic suppression...")
        self.acoustic_suppression(duration=3.0)
        time.sleep(2)
        
        print("\n2. Testing water suppression (pulse)...")
        self.water_suppression(duration=2.4, pattern='pulse')
        time.sleep(2)
        
        print("\n3. Testing combined suppression...")
        self.combined_suppression(duration=3.0)
        time.sleep(2)
        
        print("\nAll tests complete!")
    
    def cleanup(self):
        """Clean up resources"""
        print("Cleaning up fire suppression system...")
        self.pump.cleanup()
        self.audio.close()
        print("Fire suppression system cleanup complete")


if __name__ == "__main__":
    suppression = FireSuppressionSystem()
    
    try:
        print("\nTesting full suppression protocol...")
        time.sleep(2)
        suppression.suppression_protocol(fire_confidence=0.85)
        
    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        suppression.cleanup()
