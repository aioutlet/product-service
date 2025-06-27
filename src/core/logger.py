import logging
import os
import sys

# Logging utilities

LOG_TO_FILE = os.getenv("LOG_TO_FILE", "false").lower() == "true"
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "product-service.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

class ColorFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[94m',    # Blue
        'INFO': '\033[92m',     # Green
        'WARNING': '\033[93m',  # Yellow
        'ERROR': '\033[91m',    # Red
        'CRITICAL': '\033[95m', # Magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        levelname = record.levelname
        
        # Build the base message
        base_msg = super().format(record)
        
        # Add extra fields if they exist
        extra_fields = []
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
                          'module', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process', 'getMessage', 'exc_info',
                          'exc_text', 'stack_info', 'message']:
                if key == 'event':
                    extra_fields.insert(0, f"{key}={value}")  # Put event first
                else:
                    extra_fields.append(f"{key}={value}")
        
        if extra_fields:
            base_msg += f" | {', '.join(extra_fields)}"
        
        # Apply color if terminal supports it
        if sys.stdout.isatty() and levelname in self.COLORS:
            color = self.COLORS[levelname]
            base_msg = f"{color}{base_msg}{self.RESET}"
        
        return base_msg

class JsonFormatter(logging.Formatter):
    def format(self, record):
        import json
        log_record = {
            'timestamp': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            'service': record.name,
            'message': record.getMessage(),
        }
        
        # Add extra fields from the record
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
                          'module', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process', 'getMessage', 'exc_info',
                          'exc_text', 'stack_info', 'message']:
                log_record[key] = value
        
        return json.dumps(log_record, default=str)

logger = logging.getLogger("product-service")
logger.setLevel(LOG_LEVEL)

if LOG_TO_FILE:
    file_handler = logging.FileHandler(LOG_FILE_PATH)
    file_handler.setFormatter(JsonFormatter())
    logger.addHandler(file_handler)
else:
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ColorFormatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(console_handler)
