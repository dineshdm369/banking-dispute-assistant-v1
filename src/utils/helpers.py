import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
import uuid


def setup_logging(log_level: str = "INFO") -> None:
    """Set up application logging with structured fields"""
    
    class StructuredFormatter(logging.Formatter):
        """Custom formatter that includes extra fields like user_id and session_id"""
        
        def format(self, record):
            # Standard formatting
            formatted = super().format(record)
            
            # Add extra fields if they exist
            extras = []
            if hasattr(record, 'user_id') and record.user_id:
                extras.append(f"user_id={record.user_id}")
            if hasattr(record, 'session_id') and record.session_id:
                extras.append(f"session_id={record.session_id}")
            if hasattr(record, 'dispute_id') and record.dispute_id:
                extras.append(f"dispute_id={record.dispute_id}")
            if hasattr(record, 'function') and record.function:
                extras.append(f"function={record.function}")
            
            if extras:
                formatted += f" [{', '.join(extras)}]"
            
            return formatted
    
    # Create custom handler with structured formatter
    handler = logging.StreamHandler()
    formatter = StructuredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    root_logger.handlers.clear()  # Clear existing handlers
    root_logger.addHandler(handler)
    
    # Reduce noise from external libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)


def load_environment() -> Dict[str, Any]:
    """Load environment variables and configuration"""
    
    from dotenv import load_dotenv
    load_dotenv()
    
    config = {
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "app_name": os.getenv("APP_NAME", "banking-dispute-assistant-v1"),
        "debug": os.getenv("DEBUG", "false").lower() == "true",
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "api_timeout": int(os.getenv("API_TIMEOUT", "30")),
        "max_retries": int(os.getenv("MAX_RETRIES", "3")),
        "confidence_threshold": float(os.getenv("CONFIDENCE_THRESHOLD", "0.7")),
        "processing_delay": float(os.getenv("PROCESSING_DELAY", "2")),
        "max_parallel_lanes": int(os.getenv("MAX_PARALLEL_LANES", "3")),
        "data_path": os.getenv("DATA_PATH", "./data"),
        "mock_api_delay": float(os.getenv("MOCK_API_DELAY", "1.5"))
    }
    
    return config


def validate_config(config: Dict[str, Any]) -> bool:
    """Validate required configuration"""
    
    required_keys = ["openai_api_key"]
    
    for key in required_keys:
        if not config.get(key):
            raise ValueError(f"Missing required configuration: {key}")
    
    return True


def format_currency(amount: float) -> str:
    """Format amount as currency"""
    return f"${amount:,.2f}"


def generate_unique_id(prefix: str = "") -> str:
    """Generate a unique identifier"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_part = str(uuid.uuid4())[:8].upper()
    return f"{prefix}{timestamp}{unique_part}"


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input"""
    if not text:
        return ""
    
    # Remove potential harmful content
    sanitized = str(text).strip()
    
    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def calculate_processing_time(start_time: datetime, end_time: Optional[datetime] = None) -> float:
    """Calculate processing time in seconds"""
    if end_time is None:
        end_time = datetime.now()
    
    return (end_time - start_time).total_seconds()


def format_datetime(dt: datetime) -> str:
    """Format datetime for display"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """Mask sensitive data like card numbers"""
    if len(data) <= visible_chars:
        return "*" * len(data)
    
    return "*" * (len(data) - visible_chars) + data[-visible_chars:]


class ProcessingTimer:
    """Context manager for timing operations"""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.end_time = None
        
    def __enter__(self):
        self.start_time = datetime.now()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = datetime.now()
        duration = calculate_processing_time(self.start_time, self.end_time)
        
        logger = logging.getLogger(__name__)
        if exc_type:
            logger.error(f"{self.operation_name} failed after {duration:.2f}s: {exc_val}")
        else:
            logger.info(f"{self.operation_name} completed in {duration:.2f}s")
    
    @property
    def duration(self) -> float:
        if self.start_time and self.end_time:
            return calculate_processing_time(self.start_time, self.end_time)
        return 0.0


def create_error_response(error_message: str, error_code: str = "GENERAL_ERROR") -> Dict[str, Any]:
    """Create standardized error response"""
    return {
        "success": False,
        "error": {
            "code": error_code,
            "message": error_message,
            "timestamp": datetime.now().isoformat()
        }
    }


def create_success_response(data: Any, message: str = "Operation successful") -> Dict[str, Any]:
    """Create standardized success response"""
    return {
        "success": True,
        "data": data,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }


def safe_json_dumps(obj: Any) -> str:
    """Safely serialize object to JSON"""
    try:
        return json.dumps(obj, default=str, indent=2)
    except Exception as e:
        logging.getLogger(__name__).error(f"JSON serialization error: {e}")
        return str(obj)


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."


# Color constants for Streamlit UI (Apple-inspired)
UI_COLORS = {
    "primary": "#007AFF",      # Blue
    "secondary": "#5856D6",    # Purple  
    "success": "#34C759",      # Green
    "warning": "#FF9500",      # Orange
    "danger": "#FF3B30",       # Red
    "background": "#F2F2F7",   # Light gray
    "surface": "#FFFFFF",      # White
    "text_primary": "#000000", # Black
    "text_secondary": "#6D6D70" # Gray
}


def get_status_color(status: str) -> str:
    """Get color for status display"""
    status_colors = {
        "completed": UI_COLORS["success"],
        "processing": UI_COLORS["warning"],
        "pending": UI_COLORS["secondary"],
        "failed": UI_COLORS["danger"],
        "filed": UI_COLORS["success"],
        "denied": UI_COLORS["danger"],
        "approved": UI_COLORS["success"]
    }
    
    return status_colors.get(status.lower(), UI_COLORS["text_secondary"])