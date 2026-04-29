"""
Input sanitization utilities for the climate-smart agriculture system.

Provides comprehensive input validation and sanitization to prevent:
- SQL injection attacks
- Cross-site scripting (XSS)
- Path traversal attacks
- Command injection
- Integer overflow
- Buffer overflow via length checks
"""

import re
import logging
from typing import Optional, Union, List, Dict, Any
from pathlib import Path

from src.config.security import InputSanitizer, SecurityError

logger = logging.getLogger(__name__)

class AdvancedInputValidator:
    """
    Advanced input validation with type checking and business logic validation.
    """
    
    # Valid file extensions for data files
    ALLOWED_EXTENSIONS = {
        'data': ['.csv', '.json', '.xlsx', '.parquet', '.geojson', '.shp'],
        'image': ['.png', '.jpg', '.jpeg', '.tiff', '.tif'],
        'document': ['.pdf', '.doc', '.docx', '.txt', '.md'],
    }
    
    # Valid geographic region codes
    VALID_REGIONS = {
        'AFR', 'AMR', 'EUR', 'SEAR', 'WPR', 'EMR',  # WHO regions
        'USA', 'CAN', 'MEX', 'BRA', 'ARG',  # Americas
        'CHN', 'IND', 'JPN', 'KOR', 'VNM',  # Asia
        'NGA', 'KEN', 'ZAF', 'EGY', 'ETH',  # Africa
    }
    
    def __init__(self, sanitizer: Optional[InputSanitizer] = None):
        """
        Initialize input validator.
        
        Args:
            sanitizer: InputSanitizer instance (creates default if None)
        """
        self.sanitizer = sanitizer or InputSanitizer()
    
    def validate_string(
        self,
        value: str,
        min_length: int = 0,
        max_length: int = 10000,
        pattern: Optional[str] = None,
        context: str = 'general'
    ) -> str:
        """
        Validate string input.
        
        Args:
            value: Input string
            min_length: Minimum length
            max_length: Maximum length
            pattern: Regex pattern to match
            context: Sanitization context
        
        Returns:
            Sanitized string
        
        Raises:
            SecurityError: If validation fails
        """
        if not isinstance(value, str):
            raise SecurityError(f"Expected string, got {type(value).__name__}")
        
        if len(value) < min_length:
            raise SecurityError(f"String too short: {len(value)} < {min_length}")
        
        if len(value) > max_length:
            raise SecurityError(f"String too long: {len(value)} > {max_length}")
        
        if pattern and not re.match(pattern, value):
            raise SecurityError(f"String does not match required pattern: {pattern}")
        
        return self.sanitizer.sanitize_for_api_input(value)
    
    def validate_file_path(self, path: str, allowed_extensions: Optional[List[str]] = None) -> Path:
        """
        Validate file path input.
        
        Args:
            path: File path string
            allowed_extensions: List of allowed extensions
        
        Returns:
            Validated Path object
        
        Raises:
            SecurityError: If path invalid
        """
        # Sanitize path
        sanitized = self.sanitizer.sanitize_for_path(path)
        
        # Check extension
        ext = Path(sanitized).suffix.lower()
        if allowed_extensions and ext not in allowed_extensions:
            raise SecurityError(
                f"File extension {ext} not allowed. Allowed: {allowed_extensions}"
            )
        
        # Prevent absolute paths (security)
        if Path(sanitized).is_absolute():
            raise SecurityError("Absolute paths not allowed")
        
        # Prevent traversal
        if '..' in sanitized:
            raise SecurityError("Path traversal detected")
        
        return Path(sanitized)
    
    def validate_url(self, url: str) -> str:
        """
        Validate URL input.
        
        Args:
            url: URL string
        
        Returns:
            Validated URL
        
        Raises:
            SecurityError: If URL invalid
        """
        # Sanitize
        sanitized = self.sanitizer.sanitize_for_html(url)
        
        # Basic URL pattern
        url_pattern = r'^https?://[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}(/[^\s]*)?$'
        if not re.match(url_pattern, sanitized):
            raise SecurityError(f"Invalid URL format: {url}")
        
        return sanitized
    
    def validate_json_data(self, data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate JSON data against schema.
        
        Args:
            data: Input data dictionary
            schema: Schema definition
        
        Returns:
            Validated data
        
        Raises:
            SecurityError: If validation fails
        """
        for field, rules in schema.items():
            if field not in data:
                if rules.get('required', False):
                    raise SecurityError(f"Missing required field: {field}")
                continue
            
            value = data[field]
            expected_type = rules.get('type')
            
            if expected_type and not isinstance(value, expected_type):
                raise SecurityError(
                    f"Field {field} expected {expected_type.__name__}, got {type(value).__name__}"
                )
            
            # String-specific validation
            if expected_type == str:
                self.validate_string(value)
            
            # Numeric validation
            if expected_type in (int, float):
                self.sanitizer.validate_numeric_input(str(value))
        
        return data
    
    def validate_geographic_input(
        self,
        lat: float,
        lon: float,
        radius_km: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Validate geographic input for queries.
        
        Args:
            lat: Latitude
            lon: Longitude
            radius_km: Optional search radius
        
        Returns:
            Dict with validated coordinates
        
        Raises:
            SecurityError: If input invalid
        """
        # Validate coordinates
        self.sanitizer.validate_location(lat, lon)
        
        # Validate radius
        if radius_km is not None:
            if not 0 < radius_km <= 10000:
                raise SecurityError(f"Invalid radius: {radius_km} km (must be 0-10000)")
        
        return {
            'latitude': float(lat),
            'longitude': float(lon),
            'radius_km': radius_km
        }
    
    def validate_date_range(
        self,
        start_date: str,
        end_date: str,
        date_format: str = '%Y-%m-%d'
    ) -> Dict[str, str]:
        """
        Validate date range input.
        
        Args:
            start_date: Start date string
            end_date: End date string
            date_format: Expected date format
        
        Returns:
            Dict with validated dates
        
        Raises:
            SecurityError: If dates invalid
        """
        from datetime import datetime
        
        # Sanitize
        start_date = self.sanitizer.sanitize_for_api_input(start_date)
        end_date = self.sanitizer.sanitize_for_api_input(end_date)
        
        try:
            start = datetime.strptime(start_date, date_format)
            end = datetime.strptime(end_date, date_format)
        except ValueError as e:
            raise SecurityError(f"Invalid date format: {e}")
        
        if start > end:
            raise SecurityError(f"Start date {start_date} after end date {end_date}")
        
        return {
            'start_date': start_date,
            'end_date': end_date,
            'start_datetime': start,
            'end_datetime': end
        }
    
    def validate_batch_input(self, items: List[Dict[str, Any]], max_items: int = 1000) -> List[Dict[str, Any]]:
        """
        Validate batch input for bulk operations.
        
        Args:
            items: List of input dictionaries
            max_items: Maximum number of items
        
        Returns:
            Validated list
        
        Raises:
            SecurityError: If batch invalid
        """
        if not isinstance(items, list):
            raise SecurityError("Expected list input")
        
        if len(items) > max_items:
            raise SecurityError(f"Batch size {len(items)} exceeds maximum {max_items}")
        
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                raise SecurityError(f"Item {i} is not a dictionary")
        
        return items

def create_secure_filename(original_name: str) -> str:
    """
    Create a secure filename from user input.
    
    Args:
        original_name: Original filename
    
    Returns:
        Sanitized filename
    """
    sanitizer = InputSanitizer()
    
    # Sanitize path characters
    sanitized = sanitizer.sanitize_for_path(original_name)
    
    # Remove extension
    name = Path(sanitized).stem
    
    # Keep only alphanumeric, dash, underscore, and period
    name = re.sub(r'[^a-zA-Z0-9\-_.]', '', name)
    
    # Limit length
    if len(name) > 100:
        name = name[:100]
    
    # Ensure not empty
    if not name:
        name = 'file'
    
    return name

def hash_sensitive_data(data: str, salt: Optional[str] = None) -> str:
    """
    Create hash of sensitive data for storage.
    
    Args:
        data: Sensitive data string
        salt: Optional salt
    
    Returns:
        SHA-256 hash
    """
    import hashlib
    
    if salt:
        combined = f"{salt}{data}"
    else:
        combined = data
    
    return hashlib.sha256(combined.encode()).hexdigest()

def redact_secrets(text: str) -> str:
    """
    Redact sensitive information from text for logging.
    
    Args:
        text: Text that may contain secrets
    
    Returns:
        Text with secrets redacted
    """
    import re
    
    redacted = text
    
    # API keys
    redacted = re.sub(
        r'[A-Za-z0-9_\-]{32,}',
        '[REDACTED_API_KEY]',
        redacted
    )
    
    # Passwords in URLs
    redacted = re.sub(
        r'://([^:]+):([^@]+)@',
        r'://\1:[REDACTED]@',
        redacted
    )
    
    # Tokens
    redacted = re.sub(
        r'Bearer\s+[A-Za-z0-9_\-\.\=]+',
        'Bearer [REDACTED]',
        redacted
    )
    
    return redacted

def validate_api_response(data: Any, required_keys: List[str]) -> Dict[str, Any]:
    """
    Validate API response contains required keys.
    
    Args:
        data: API response data
        required_keys: List of required keys
    
    Returns:
        Validated data
    
    Raises:
        SecurityError: If required keys missing
    """
    if not isinstance(data, dict):
        raise SecurityError("API response must be a dictionary")
    
    missing = [key for key in required_keys if key not in data]
    if missing:
        raise SecurityError(f"API response missing required keys: {missing}")
    
    return data
