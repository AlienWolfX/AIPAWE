import numpy as np
import pyaudio
import wave
import time
import math


class TPA3116D2Audio:
    
    def __init__(self, sample_rate=44100, channels=2, device_index=None):
        self.sample_rate = sample_rate
        self.channels = channels
        self.device_index = device_index
        
        self.p = pyaudio.PyAudio()
        
        if device_index is None:
            self.device_index = self._find_audio_device()
        
        print(f"TPA3116D2 Audio initialized - Sample Rate: {sample_rate}Hz, Channels: {channels}")
    
    def _find_audio_device(self):
        info = self.p.get_host_api_info_by_index(0)
        num_devices = info.get('deviceCount')
        
        print("\nAvailable audio devices:")
        for i in range(num_devices):
            device_info = self.p.get_device_info_by_host_api_device_index(0, i)
            if device_info.get('maxOutputChannels') > 0:
                print(f"  [{i}] {device_info.get('name')}")
        
        default_device = self.p.get_default_output_device_info()
        print(f"\nUsing device: {default_device.get('name')}")
        return default_device.get('index')
    
    def generate_tone(self, frequency, duration, volume=0.5, waveform='sine'):
        num_samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, num_samples, False)
        
        if waveform == 'sine':
            wave_data = np.sin(2 * np.pi * frequency * t)
        elif waveform == 'square':
            wave_data = np.sign(np.sin(2 * np.pi * frequency * t))
        elif waveform == 'sawtooth':
            wave_data = 2 * (t * frequency - np.floor(t * frequency + 0.5))
        elif waveform == 'triangle':
            wave_data = 2 * np.abs(2 * (t * frequency - np.floor(t * frequency + 0.5))) - 1
        else:
            raise ValueError(f"Unknown waveform: {waveform}")
        
        wave_data = wave_data * volume
        
        if self.channels == 2:
            wave_data = np.column_stack((wave_data, wave_data))
        
        return wave_data.astype(np.float32)
    
    def play_tone(self, frequency, duration, volume=0.5, waveform='sine'):
        audio_data = self.generate_tone(frequency, duration, volume, waveform)
        
        stream = self.p.open(
            format=pyaudio.paFloat32,
            channels=self.channels,
            rate=self.sample_rate,
            output=True,
            output_device_index=self.device_index
        )
        
        stream.write(audio_data.tobytes())
        
        stream.stop_stream()
        stream.close()
    
    def play_beep(self, frequency=1000, duration=0.2, volume=0.5):
        self.play_tone(frequency, duration, volume, 'sine')
    
    def play_melody(self, notes, tempo=120):
        beat_duration = 60.0 / tempo
        
        for note in notes:
            if len(note) == 2:
                frequency, beats = note
                volume = 0.5
            elif len(note) == 3:
                frequency, beats, volume = note
            else:
                continue
            
            duration = beats * beat_duration
            
            if frequency > 0:
                self.play_tone(frequency, duration, volume, 'sine')
            else:
                time.sleep(duration)
    
    def play_chord(self, frequencies, duration, volume=0.5):
        num_samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, num_samples, False)
        
        wave_data = np.zeros(num_samples)
        for freq in frequencies:
            wave_data += np.sin(2 * np.pi * freq * t)
        
        wave_data = wave_data / len(frequencies) * volume
        
        if self.channels == 2:
            wave_data = np.column_stack((wave_data, wave_data))
        
        wave_data = wave_data.astype(np.float32)
        
        stream = self.p.open(
            format=pyaudio.paFloat32,
            channels=self.channels,
            rate=self.sample_rate,
            output=True,
            output_device_index=self.device_index
        )
        
        stream.write(wave_data.tobytes())
        stream.stop_stream()
        stream.close()
    
    def play_sweep(self, start_freq, end_freq, duration, volume=0.5):
        num_samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, num_samples, False)
        
        freq_range = end_freq - start_freq
        instantaneous_frequency = start_freq + (freq_range * t / duration)
        phase = 2 * np.pi * np.cumsum(instantaneous_frequency) / self.sample_rate
        wave_data = np.sin(phase) * volume
        
        if self.channels == 2:
            wave_data = np.column_stack((wave_data, wave_data))
        
        wave_data = wave_data.astype(np.float32)
        
        stream = self.p.open(
            format=pyaudio.paFloat32,
            channels=self.channels,
            rate=self.sample_rate,
            output=True,
            output_device_index=self.device_index
        )
        
        stream.write(wave_data.tobytes())
        stream.stop_stream()
        stream.close()
    
    def play_wav_file(self, filepath, volume=1.0):
        wf = wave.open(filepath, 'rb')

        stream = self.p.open(
            format=self.p.get_format_from_width(wf.getsampwidth()),
            channels=wf.getnchannels(),
            rate=wf.getframerate(),
            output=True,
            output_device_index=self.device_index
        )

        chunk_size = 1024
        data = wf.readframes(chunk_size)
        
        while data:
            if volume != 1.0:
                audio_array = np.frombuffer(data, dtype=np.int16)
                audio_array = (audio_array * volume).astype(np.int16)
                data = audio_array.tobytes()
            
            stream.write(data)
            data = wf.readframes(chunk_size)
        
        stream.stop_stream()
        stream.close()
        wf.close()
    
    def play_alarm(self, duration=2.0, volume=0.7):
        pulses = int(duration / 0.4)
        for _ in range(pulses):
            self.play_tone(800, 0.15, volume, 'sine')
            time.sleep(0.05)
            self.play_tone(1000, 0.15, volume, 'sine')
            time.sleep(0.05)
    
    def play_notification(self, volume=0.5):
        self.play_tone(800, 0.1, volume, 'sine')
        time.sleep(0.05)
        self.play_tone(1200, 0.15, volume, 'sine')
    
    def play_success(self, volume=0.5):
        self.play_tone(523, 0.1, volume, 'sine')  # C
        time.sleep(0.05)
        self.play_tone(659, 0.1, volume, 'sine')  # E
        time.sleep(0.05)
        self.play_tone(784, 0.2, volume, 'sine')  # G
    
    def play_error(self, volume=0.5):
        self.play_tone(200, 0.3, volume, 'square')
        time.sleep(0.1)
        self.play_tone(150, 0.3, volume, 'square')
    
    def close(self):
        """Close PyAudio instance"""
        self.p.terminate()
        print("TPA3116D2 Audio closed")


NOTES = {
    'C4': 261.63, 'C#4': 277.18, 'D4': 293.66, 'D#4': 311.13,
    'E4': 329.63, 'F4': 349.23, 'F#4': 369.99, 'G4': 392.00,
    'G#4': 415.30, 'A4': 440.00, 'A#4': 466.16, 'B4': 493.88,
    'C5': 523.25, 'C#5': 554.37, 'D5': 587.33, 'D#5': 622.25,
    'E5': 659.25, 'F5': 698.46, 'F#5': 739.99, 'G5': 783.99,
    'G#5': 830.61, 'A5': 880.00, 'A#5': 932.33, 'B5': 987.77,
    'REST': 0
}


if __name__ == "__main__":
    audio = TPA3116D2Audio(sample_rate=44100, channels=2)
    
    try:
        print("\nPlaying test tones...")
        
        print("Sine wave - 440Hz")
        audio.play_tone(440, 1.0, 0.5, 'sine')
        time.sleep(0.5)
        
        print("Square wave - 440Hz")
        audio.play_tone(440, 1.0, 0.3, 'square')
        time.sleep(0.5)
        
        print("Triangle wave - 440Hz")
        audio.play_tone(440, 1.0, 0.4, 'triangle')
        time.sleep(0.5)
        
        print("Beep")
        audio.play_beep(1000, 0.2, 0.5)
        time.sleep(0.5)
        
        print("C Major Chord")
        audio.play_chord([NOTES['C4'], NOTES['E4'], NOTES['G4']], 2.0, 0.4)
        time.sleep(0.5)
        
        print("Frequency sweep (100Hz to 2000Hz)")
        audio.play_sweep(100, 2000, 2.0, 0.3)
        time.sleep(0.5)
        
        print("Simple melody")
        melody = [
            (NOTES['C4'], 0.5),
            (NOTES['E4'], 0.5),
            (NOTES['G4'], 0.5),
            (NOTES['C5'], 1.0),
        ]
        audio.play_melody(melody, tempo=120)
        time.sleep(0.5)
        
        print("Notification sound")
        audio.play_notification(0.5)
        time.sleep(1)
        
        print("Success sound")
        audio.play_success(0.5)
        time.sleep(1)
        
        print("Error sound")
        audio.play_error(0.4)
        time.sleep(1)
        
        print("Alarm sound")
        audio.play_alarm(2.0, 0.5)
        
    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        audio.close()
