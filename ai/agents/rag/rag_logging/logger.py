import logging
import json
from typing import Dict, Any

# Configure standard format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        
    def info(self, msg: str, **kwargs):
        if kwargs:
            self.logger.info(f"{msg} - metadata: {json.dumps(kwargs)}")
        else:
            self.logger.info(msg)
            
    def warning(self, msg: str, **kwargs):
        if kwargs:
            self.logger.warning(f"{msg} - metadata: {json.dumps(kwargs)}")
        else:
            self.logger.warning(msg)
            
    def error(self, msg: str, **kwargs):
        if kwargs:
            self.logger.error(f"{msg} - metadata: {json.dumps(kwargs)}")
        else:
            self.logger.error(msg)
            
    def log_latency(self, phase: str, duration_sec: float, **extra):
        payload = {
            "phase": phase,
            "duration_ms": round(duration_sec * 1000, 2),
            **extra
        }
        self.logger.info(f"[LATENCY] {phase} took {payload['duration_ms']}ms - metrics: {json.dumps(payload)}")

def get_logger(name: str) -> StructuredLogger:
    return StructuredLogger(name)
