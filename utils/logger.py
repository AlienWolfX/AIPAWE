"""
AIPAWE - Logging Module
Centralized logging with rotation and event tracking
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional
from utils.utils_common import ensure_directory


class AIPAWELogger:
    """Centralized logger for AIPAWE system"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger('AIPAWE')
        self.setup_logger()
        
    def setup_logger(self):
        """Configure logger with file and console handlers"""
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Set level
        log_level = getattr(logging, self.config.get('logging', 'log_level', default='INFO'))
        self.logger.setLevel(log_level)
        
        # Create logs directory
        log_file = self.config.get('logging', 'log_file', default='logs/aipawe.log')
        ensure_directory(os.path.dirname(log_file))
        
        # File handler with rotation
        max_bytes = self.config.get('logging', 'max_log_size', default=10485760)
        backup_count = self.config.get('logging', 'backup_count', default=5)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler
        if self.config.get('logging', 'console_output', default=True):
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
    
    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log error message"""
        self.logger.error(message)
    
    def critical(self, message: str):
        """Log critical message"""
        self.logger.critical(message)
    
    def log_state_transition(self, from_state: str, to_state: str):
        """Log state machine transition"""
        self.info(f"STATE TRANSITION: {from_state} → {to_state}")
    
    def log_fire_detected(self, sector: float, confidence: float):
        """Log fire detection event"""
        self.warning(f"FIRE DETECTED: Sector {sector:.1f}° | Confidence {confidence:.2%}")
    
    def log_suppression_attempt(self, method: str, attempt: int):
        """Log suppression attempt"""
        self.info(f"SUPPRESSION: Method={method} | Attempt={attempt}")
    
    def log_suppression_result(self, success: bool, method: str):
        """Log suppression result"""
        if success:
            self.info(f"SUPPRESSION SUCCESS: Method={method}")
        else:
            self.warning(f"SUPPRESSION FAILED: Method={method}")
    
    def log_notification_sent(self, message: str, recipients: list):
        """Log SMS notification"""
        self.info(f"SMS SENT: '{message}' to {len(recipients)} recipient(s)")
    
    def log_hardware_action(self, component: str, action: str, details: str = ""):
        """Log hardware component action"""
        msg = f"HARDWARE: {component} - {action}"
        if details:
            msg += f" | {details}"
        self.debug(msg)
    
    def log_error_with_recovery(self, error: Exception, recovery_action: str):
        """Log error with recovery action"""
        self.error(f"ERROR: {type(error).__name__}: {error} | Recovery: {recovery_action}")
    
    def reload_config(self, config):
        """Reload configuration and reconfigure logger"""
        self.config = config
        self.setup_logger()
        self.info("Logger configuration reloaded")
