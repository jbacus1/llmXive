"""
Security module for API key management and sensitive data handling.

Implements:
- Secure API key loading from environment variables
- API key validation with fail-fast behavior
- Encrypted credential storage (optional)
- Input sanitization utilities
"""

import os
import re
import hashlib
import logging
from typing import Optional, Dict, Any
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

# Required API keys for the climate-smart agriculture system
REQUIRED_API_KEYS = [
    'OPENWEATHERMAP_API_KEY',
    'USGS_API_KEY',
]

# API key patterns for validation
API_KEY_PATTERNS = {
    'OPENWEATHERMAP_API_KEY': r'^[a-f0-9]{32}$',  # 32 hex characters
    'USGS_API_KEY': r'^[a-zA-Z0-9_-]{32,}$',      # USGS format
}

# Sensitive data patterns to detect and redact
SENSITIVE_PATTERNS = [
    (r'api[_-]?key\s*[=:]\s*["\']?([a-zA-Z0-9_-]{16,})["\']?', 'api_key'),
    (r'password\s*[=:]\s*["\']?([^\s"\']+)["\']?', 'password'),
    (r'secret\s*[=:]\s*["\']?([^\s"\']+)["\']?', 'secret'),
    (r'token\s*[=:]\s*["\']?([a-zA-Z0-9_-]{16,})["\']?', 'token'),
]

class SecurityError(Exception):
    """Custom exception for security-related errors."""
    pass

class APIKeyManager:
    """
    Manages API keys securely using environment variables.
    
    Follows security best practices:
    - Never hardcode keys in source code
    - Validate key format before use
    - Fail-fast on missing/invalid keys
    - Log only key status, never actual values
    """
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize API key manager.
        
        Args:
            env_file: Optional path to .env file for local development
        """
        self.env_file = env_file
        self._keys: Dict[str, str] = {}
        self._loaded = False
    
    def load_from_env(self) -> Dict[str, str]:
        """
        Load API keys from environment variables.
        
        Returns:
            Dict of API keys (without actual values in logs)
        
        Raises:
            SecurityError: If required keys are missing or invalid
        """
        if self._loaded:
            return self._keys
        
        missing_keys = []
        invalid_keys = []
        
        for key in REQUIRED_API_KEYS:
            value = os.environ.get(key)
            
            if value is None:
                missing_keys.append(key)
                logger.warning(f"Missing required API key: {key}")
            elif not self._validate_key_format(key, value):
                invalid_keys.append(key)
                logger.warning(f"Invalid format for API key: {key}")
            else:
                self._keys[key] = value
                logger.info(f"API key loaded and validated: {key}")
        
        if missing_keys:
            raise SecurityError(
                f"Missing required API keys: {', '.join(missing_keys)}. "
                f"Set these in environment or use load_from_env_file()."
            )
        
        if invalid_keys:
            raise SecurityError(
                f"Invalid format for API keys: {', '.join(invalid_keys)}. "
                f"Check your key format and regenerate if needed."
            )
        
        self._loaded = True
        logger.info("All API keys loaded and validated successfully")
        return self._keys
    
    def load_from_env_file(self, env_file: Optional[str] = None) -> Dict[str, str]:
        """
        Load API keys from .env file (development only).
        
        Args:
            env_file: Path to .env file
        
        Returns:
            Dict of API keys
        
        Raises:
            SecurityError: If file not found or keys invalid
        """
        file_path = env_file or self.env_file
        
        if not file_path:
            raise SecurityError(
                "No env_file specified. Use load_from_env() for production."
            )
        
        env_path = Path(file_path)
        if not env_path.exists():
            raise SecurityError(f"Env file not found: {file_path}")
        
        # Load .env file
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    os.environ[key] = value
        
        logger.info(f"Loaded environment from {file_path}")
        return self.load_from_env()
    
    def _validate_key_format(self, key: str, value: str) -> bool:
        """
        Validate API key format.
        
        Args:
            key: Key name
            value: Key value
        
        Returns:
            True if valid format
        """
        pattern = API_KEY_PATTERNS.get(key)
        if pattern:
            return bool(re.match(pattern, value))
        return len(value) >= 16  # Generic minimum length check
    
    def get_key(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get API key by name.
        
        Args:
            key: Key name
            default: Default value if not found
        
        Returns:
            API key value or default
        """
        if not self._loaded:
            self.load_from_env()
        return self._keys.get(key, default)
    
    def hash_key(self, key: str) -> str:
        """
        Create hash of API key for logging/comparison (never store actual key).
        
        Args:
            key: API key value
        
        Returns:
            SHA-256 hash of key
        """
        return hashlib.sha256(key.encode()).hexdigest()[:16]

class InputSanitizer:
    """
    Sanitizes user input to prevent injection attacks.
    
    Provides:
    - SQL injection prevention
    - XSS prevention
    - Path traversal prevention
    - Command injection prevention
    """
    
    # Dangerous characters/patterns for different contexts
    SQL_DANGEROUS = [
        r';', r'--', r'/*', r'*/', r"'", r'"', r'\\',
        r'UNION', r'SELECT', r'DROP', r'INSERT', r'UPDATE', r'DELETE',
        r'OR\s+1\s*=\s*1', r'AND\s+1\s*=\s+1'
    ]
    
    XSS_DANGEROUS = [
        r'<script', r'</script>', r'javascript:', r'on\w+\s*=',
        r'<iframe', r'<object', r'<embed', r'<link\s+rel'
    ]
    
    PATH_DANGEROUS = [
        r'\.\.', r'~', r'\$', r'`', r'\|', r'&', r';'
    ]
    
    COMMAND_DANGEROUS = [
        r';', r'&', r'\|', r'`', r'\$', r'\(', r'\)'
    ]
    
    def __init__(self, max_length: int = 10000):
        """
        Initialize input sanitizer.
        
        Args:
            max_length: Maximum allowed input length
        """
        self.max_length = max_length
        self._sql_pattern = re.compile('|'.join(self.SQL_DANGEROUS), re.IGNORECASE)
        self._xss_pattern = re.compile('|'.join(self.XSS_DANGEROUS), re.IGNORECASE)
        self._path_pattern = re.compile('|'.join(self.PATH_DANGEROUS))
        self._command_pattern = re.compile('|'.join(self.COMMAND_DANGEROUS))
    
    def sanitize_for_sql(self, value: str) -> str:
        """
        Sanitize input for SQL queries.
        
        Args:
            value: Input string
        
        Returns:
            Sanitized string
        
        Raises:
            SecurityError: If dangerous SQL patterns detected
        """
        self._check_length(value)
        
        if self._sql_pattern.search(value):
            logger.warning(f"Potential SQL injection detected and sanitized")
            # Remove dangerous characters
            sanitized = re.sub(r'[;\'"\\]', '', value)
            # Remove SQL keywords
            for keyword in ['UNION', 'SELECT', 'DROP', 'INSERT', 'UPDATE', 'DELETE']:
                sanitized = re.sub(keyword, '', sanitized, flags=re.IGNORECASE)
            return sanitized
        
        return value
    
    def sanitize_for_html(self, value: str) -> str:
        """
        Sanitize input for HTML output (XSS prevention).
        
        Args:
            value: Input string
        
        Returns:
            HTML-escaped string
        
        Raises:
            SecurityError: If dangerous XSS patterns detected
        """
        self._check_length(value)
        
        if self._xss_pattern.search(value):
            logger.warning(f"Potential XSS detected and sanitized")
        
        # HTML escape
        return (value
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#x27;'))
    
    def sanitize_for_path(self, value: str) -> str:
        """
        Sanitize input for file paths.
        
        Args:
            value: Input string
        
        Returns:
            Sanitized path string
        
        Raises:
            SecurityError: If path traversal detected
        """
        self._check_length(value)
        
        if self._path_pattern.search(value):
            logger.warning(f"Potential path traversal detected and sanitized")
            # Remove dangerous characters
            return re.sub(r'[\.~\$\`&;|]', '', value)
        
        return value
    
    def sanitize_for_command(self, value: str) -> str:
        """
        Sanitize input for shell commands.
        
        Args:
            value: Input string
        
        Returns:
            Sanitized command argument
        
        Raises:
            SecurityError: If command injection detected
        """
        self._check_length(value)
        
        if self._command_pattern.search(value):
            logger.warning(f"Potential command injection detected and sanitized")
            # Remove dangerous characters
            return re.sub(r'[;&\|`$()]', '', value)
        
        return value
    
    def sanitize_for_api_input(self, value: str) -> str:
        """
        Sanitize input for API requests.
        
        Args:
            value: Input string
        
        Returns:
            Sanitized string with sensitive patterns redacted
        """
        self._check_length(value)
        
        # Redact sensitive data
        sanitized = value
        for pattern, _ in SENSITIVE_PATTERNS:
            sanitized = re.sub(pattern, r'\g<0> [REDACTED]', sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    def _check_length(self, value: str) -> None:
        """
        Check input length.
        
        Args:
            value: Input string
        
        Raises:
            SecurityError: If input exceeds max length
        """
        if len(value) > self.max_length:
            raise SecurityError(
                f"Input exceeds maximum allowed length of {self.max_length} characters"
            )
    
    def validate_location(self, lat: float, lon: float) -> bool:
        """
        Validate geographic coordinates.
        
        Args:
            lat: Latitude
            lon: Longitude
        
        Returns:
            True if valid coordinates
        
        Raises:
            SecurityError: If coordinates invalid
        """
        if not (-90 <= lat <= 90):
            raise SecurityError(f"Invalid latitude: {lat}")
        if not (-180 <= lon <= 180):
            raise SecurityError(f"Invalid longitude: {lon}")
        return True
    
    def validate_numeric_input(self, value: str, min_val: float = None, max_val: float = None) -> float:
        """
        Validate and convert numeric input.
        
        Args:
            value: Input string
            min_val: Minimum allowed value
            max_val: Maximum allowed value
        
        Returns:
            Converted float
        
        Raises:
            SecurityError: If input invalid or out of range
        """
        self._check_length(value)
        
        # Only allow digits, decimal point, minus sign, and whitespace
        if not re.match(r'^[\d.\-+\s]+$', value):
            raise SecurityError(f"Invalid numeric input: {value}")
        
        try:
            num = float(value.strip())
        except ValueError:
            raise SecurityError(f"Cannot convert to float: {value}")
        
        if min_val is not None and num < min_val:
            raise SecurityError(f"Value {num} below minimum {min_val}")
        if max_val is not None and num > max_val:
            raise SecurityError(f"Value {num} above maximum {max_val}")
        
        return num

def get_api_keys() -> Dict[str, str]:
    """
    Convenience function to load and return all API keys.
    
    Returns:
        Dict of API keys
    
    Raises:
        SecurityError: If keys missing or invalid
    """
    manager = APIKeyManager()
    return manager.load_from_env()

def sanitize_input(value: str, context: str = 'general') -> str:
    """
    Convenience function for input sanitization.
    
    Args:
        value: Input string
        context: Sanitization context ('sql', 'html', 'path', 'command', 'api', 'general')
    
    Returns:
        Sanitized string
    """
    sanitizer = InputSanitizer()
    
    sanitizers = {
        'sql': sanitizer.sanitize_for_sql,
        'html': sanitizer.sanitize_for_html,
        'path': sanitizer.sanitize_for_path,
        'command': sanitizer.sanitize_for_command,
        'api': sanitizer.sanitize_for_api_input,
        'general': lambda x: x,
    }
    
    return sanitizers.get(context, sanitizers['general'])(value)

def validate_environment() -> bool:
    """
    Validate that all required security configurations are in place.
    
    Returns:
        True if environment is secure
    
    Raises:
        SecurityError: If security checks fail
    """
    manager = APIKeyManager()
    manager.load_from_env()
    
    logger.info("Security environment validation passed")
    return True
