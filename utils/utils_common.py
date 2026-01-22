"""
AIPAWE - Common Utility Functions
Shared utilities for configuration loading, GPIO management, and helpers
"""

import yaml
import time
import os
from typing import Any, Dict
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class ConfigLoader:
    """Hot-reloadable configuration loader"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.last_modified = 0
        self.load_config()
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            self.last_modified = os.path.getmtime(self.config_path)
            return self.config
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration: {e}")
    
    def reload_if_changed(self) -> bool:
        """Check if config file changed and reload if needed"""
        try:
            current_modified = os.path.getmtime(self.config_path)
            if current_modified > self.last_modified:
                self.load_config()
                return True
        except FileNotFoundError:
            pass
        return False
    
    def get(self, *keys, default=None) -> Any:
        """Get nested configuration value"""
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        return value


class ConfigWatcher(FileSystemEventHandler):
    """Watch configuration file for changes"""
    
    def __init__(self, config_loader: ConfigLoader, callback=None):
        self.config_loader = config_loader
        self.callback = callback
    
    def on_modified(self, event):
        if event.src_path.endswith('config.yaml'):
            if self.config_loader.reload_if_changed():
                if self.callback:
                    self.callback()


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max"""
    return max(min_val, min(max_val, value))


def map_range(value: float, in_min: float, in_max: float, 
              out_min: float, out_max: float) -> float:
    """Map value from one range to another"""
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def angle_difference(angle1: float, angle2: float) -> float:
    """Calculate shortest angular difference between two angles"""
    diff = (angle2 - angle1) % 360
    if diff > 180:
        diff -= 360
    return diff


def normalize_angle(angle: float) -> float:
    """Normalize angle to 0-360 range"""
    return angle % 360


class RateLimiter:
    """Simple rate limiter for function calls"""
    
    def __init__(self, min_interval: float):
        self.min_interval = min_interval
        self.last_call = 0
    
    def can_proceed(self) -> bool:
        """Check if enough time has passed"""
        current = time.time()
        if current - self.last_call >= self.min_interval:
            self.last_call = current
            return True
        return False
    
    def wait_if_needed(self):
        """Block until rate limit allows"""
        current = time.time()
        elapsed = current - self.last_call
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_call = time.time()


def safe_gpio_cleanup():
    """Safely cleanup GPIO on exit"""
    try:
        import RPi.GPIO as GPIO
        GPIO.cleanup()
    except:
        pass


def ensure_directory(path: str):
    """Ensure directory exists"""
    os.makedirs(path, exist_ok=True)
