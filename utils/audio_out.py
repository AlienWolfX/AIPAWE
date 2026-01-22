"""
AIPAWE - Audio Suppression Controller
Low-frequency audio output via ALSA for fire suppression attempts
"""

import numpy as np
import time
import threading
from typing import Optional

try:
    import alsaaudio
    ALSA_AVAILABLE = True
except ImportError:
    ALSA_AVAILABLE = False


class AudioSuppressor:
    """ALSA-based low-frequency audio suppression system"""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        
        # Audio parameters
        self.device = config.get('audio', 'device', default='plughw:1,0')
        self.frequency = config.get('audio', 'frequency', default=30)
        self.duration = config.get('audio', 'duration', default=5)
        self.amplitude = config.get('audio', 'amplitude', default=0.8)
        self.sample_rate = config.get('audio', 'sample_rate', default=44100)
        self.max_attempts = config.get('audio', 'max_attempts', default=2)
        
        # State
        self.is_playing = False
        self.play_thread: Optional[threading.Thread] = None
        self.stop_playback = threading.Event()
        
        # Initialize device
        self.pcm = None
        if ALSA_AVAILABLE:
            try:
                self._init_device()
                self.logger.info(f"AudioSuppressor initialized: {self.frequency}Hz @ {self.sample_rate}Hz")
            except Exception as e:
                self.logger.error(f"Failed to initialize ALSA device: {e}")
        else:
            self.logger.warning("ALSA not available - audio suppression disabled")
    
    def _init_device(self):
        """Initialize ALSA PCM device"""
        if not ALSA_AVAILABLE:
            return
        
        self.pcm = alsaaudio.PCM(
            alsaaudio.PCM_PLAYBACK,
            alsaaudio.PCM_NORMAL,
            device=self.device
        )
        
        # Set parameters
        self.pcm.setchannels(1)  # Mono
        self.pcm.setrate(self.sample_rate)
        self.pcm.setformat(alsaaudio.PCM_FORMAT_S16_LE)
        self.pcm.setperiodsize(1024)
    
    def _generate_tone(self, frequency: float, duration: float, 
                       amplitude: float) -> np.ndarray:
        """Generate low-frequency sine wave tone"""
        samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, samples, False)
        
        # Generate sine wave
        wave = amplitude * np.sin(2 * np.pi * frequency * t)
        
        # Apply envelope to prevent clicks
        envelope_duration = 0.1  # 100ms fade in/out
        envelope_samples = int(self.sample_rate * envelope_duration)
        
        # Fade in
        wave[:envelope_samples] *= np.linspace(0, 1, envelope_samples)
        # Fade out
        wave[-envelope_samples:] *= np.linspace(1, 0, envelope_samples)
        
        # Convert to 16-bit PCM
        wave_int16 = np.int16(wave * 32767)
        
        return wave_int16.tobytes()
    
    def play_suppression_tone(self, blocking: bool = True) -> bool:
        """
        Play low-frequency suppression tone
        
        Args:
            blocking: If True, wait for playback to complete
            
        Returns:
            True if playback started successfully
        """
        if not ALSA_AVAILABLE or self.pcm is None:
            self.logger.warning("Audio playback not available")
            return False
        
        if self.is_playing:
            self.logger.warning("Audio already playing")
            return False
        
        self.logger.log_hardware_action(
            "AudioSuppressor", "PLAY",
            f"{self.frequency}Hz for {self.duration}s"
        )
        
        if blocking:
            self._playback_loop()
        else:
            self.is_playing = True
            self.stop_playback.clear()
            self.play_thread = threading.Thread(target=self._playback_loop, daemon=True)
            self.play_thread.start()
        
        return True
    
    def _playback_loop(self):
        """Internal playback loop"""
        try:
            # Generate tone
            audio_data = self._generate_tone(
                self.frequency,
                self.duration,
                self.amplitude
            )
            
            # Play in chunks
            chunk_size = 4096
            for i in range(0, len(audio_data), chunk_size):
                if self.stop_playback.is_set():
                    break
                
                chunk = audio_data[i:i + chunk_size]
                self.pcm.write(chunk)
            
            self.is_playing = False
            
        except Exception as e:
            self.logger.error(f"Audio playback error: {e}")
            self.is_playing = False
    
    def stop(self):
        """Stop audio playback"""
        if self.is_playing:
            self.stop_playback.set()
            if self.play_thread:
                self.play_thread.join(timeout=1.0)
            self.is_playing = False
            self.logger.log_hardware_action("AudioSuppressor", "STOP")
    
    def wait_for_completion(self, timeout: float = None):
        """Wait for playback to complete"""
        if self.play_thread and self.play_thread.is_alive():
            self.play_thread.join(timeout=timeout)
    
    def is_active(self) -> bool:
        """Check if audio is currently playing"""
        return self.is_playing
    
    def cleanup(self):
        """Cleanup audio resources"""
        self.stop()
        if self.pcm:
            try:
                self.pcm.close()
            except:
                pass
