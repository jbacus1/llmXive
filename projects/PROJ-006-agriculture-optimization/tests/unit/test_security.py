"""
Unit tests for security module.

Tests cover:
- API key management
- Input sanitization
- Validation functions
- Security error handling
"""

import pytest
import os
import re
from unittest.mock import patch, MagicMock

from src.config.security import (
    APIKeyManager,
    InputSanitizer,
    SecurityError,
    get_api_keys,
    sanitize_input,
    validate_environment,
)
from src.utils.input_sanitizer import (
    AdvancedInputValidator,
    create_secure_filename,
    hash_sensitive_data,
    redact_secrets,
)

class TestAPIKeyManager:
    """Tests for API key management."""
    
    def test_load_from_env_missing_key(self):
        """Test that missing API key raises SecurityError."""
        # Clear all API keys
        for key in ['OPENWEATHERMAP_API_KEY', 'USGS_API_KEY']:
            os.environ.pop(key, None)
        
        manager = APIKeyManager()
        
        with pytest.raises(SecurityError) as exc_info:
            manager.load_from_env()
        
        assert 'Missing required API keys' in str(exc_info.value)
    
    def test_load_from_env_invalid_format(self):
        """Test that invalid API key format raises SecurityError."""
        os.environ['OPENWEATHERMAP_API_KEY'] = 'invalid_key'
        os.environ['USGS_API_KEY'] = 'another_invalid'
        
        manager = APIKeyManager()
        
        with pytest.raises(SecurityError) as exc_info:
            manager.load_from_env()
        
        assert 'Invalid format' in str(exc_info.value)
    
    def test_load_from_env_valid(self):
        """Test successful loading of valid API keys."""
        os.environ['OPENWEATHERMAP_API_KEY'] = 'a' * 32
        os.environ['USGS_API_KEY'] = 'b' * 32
        
        manager = APIKeyManager()
        keys = manager.load_from_env()
        
        assert 'OPENWEATHERMAP_API_KEY' in keys
        assert 'USGS_API_KEY' in keys
        assert len(keys['OPENWEATHERMAP_API_KEY']) == 32
    
    def test_hash_key(self):
        """Test API key hashing."""
        manager = APIKeyManager()
        key = 'test_api_key_1234567890123456'
        
        hashed = manager.hash_key(key)
        
        assert len(hashed) == 16
        assert hashed != key
        assert re.match(r'^[a-f0-9]+$', hashed)
    
    def test_get_key(self):
        """Test getting API key by name."""
        os.environ['OPENWEATHERMAP_API_KEY'] = 'a' * 32
        
        manager = APIKeyManager()
        key = manager.get_key('OPENWEATHERMAP_API_KEY')
        
        assert key == 'a' * 32
    
    def test_get_key_missing(self):
        """Test getting missing API key returns default."""
        manager = APIKeyManager()
        key = manager.get_key('NONEXISTENT_KEY', 'default_value')
        
        assert key == 'default_value'

class TestInputSanitizer:
    """Tests for input sanitization."""
    
    def test_sanitize_for_sql(self):
        """Test SQL injection sanitization."""
        sanitizer = InputSanitizer()
        
        dangerous_input = "'; DROP TABLE users; --"
        sanitized = sanitizer.sanitize_for_sql(dangerous_input)
        
        assert ';' not in sanitized
        assert 'DROP' not in sanitized
        assert "'" not in sanitized
    
    def test_sanitize_for_sql_safe(self):
        """Test that safe input passes through."""
        sanitizer = InputSanitizer()
        
        safe_input = "user_name_123"
        sanitized = sanitizer.sanitize_for_sql(safe_input)
        
        assert sanitized == safe_input
    
    def test_sanitize_for_html(self):
        """Test XSS sanitization."""
        sanitizer = InputSanitizer()
        
        dangerous_input = "<script>alert('xss')</script>"
        sanitized = sanitizer.sanitize_for_html(dangerous_input)
        
        assert '<script>' not in sanitized
        assert '&lt;script&gt;' in sanitized
    
    def test_sanitize_for_path(self):
        """Test path traversal sanitization."""
        sanitizer = InputSanitizer()
        
        dangerous_input = "../../../etc/passwd"
        sanitized = sanitizer.sanitize_for_path(dangerous_input)
        
        assert '..' not in sanitized
    
    def test_sanitize_for_command(self):
        """Test command injection sanitization."""
        sanitizer = InputSanitizer()
        
        dangerous_input = "file.txt; rm -rf /"
        sanitized = sanitizer.sanitize_for_command(dangerous_input)
        
        assert ';' not in sanitized
        assert 'rm' not in sanitized
    
    def test_validate_location(self):
        """Test geographic coordinate validation."""
        sanitizer = InputSanitizer()
        
        # Valid coordinates
        assert sanitizer.validate_location(0, 0)
        assert sanitizer.validate_location(90, 180)
        assert sanitizer.validate_location(-90, -180)
        
        # Invalid coordinates
        with pytest.raises(SecurityError):
            sanitizer.validate_location(91, 0)
        
        with pytest.raises(SecurityError):
            sanitizer.validate_location(0, 181)
    
    def test_validate_numeric_input(self):
        """Test numeric input validation."""
        sanitizer = InputSanitizer()
        
        # Valid numeric input
        assert sanitizer.validate_numeric_input("123.45") == 123.45
        assert sanitizer.validate_numeric_input("-10") == -10.0
        
        # Invalid numeric input
        with pytest.raises(SecurityError):
            sanitizer.validate_numeric_input("abc")
        
        # Out of range
        with pytest.raises(SecurityError):
            sanitizer.validate_numeric_input("100", min_val=0, max_val=50)
    
    def test_max_length_exceeded(self):
        """Test that exceeding max length raises error."""
        sanitizer = InputSanitizer(max_length=10)
        
        with pytest.raises(SecurityError):
            sanitizer.sanitize_for_sql("a" * 20)

class TestAdvancedInputValidator:
    """Tests for advanced input validation."""
    
    def test_validate_string(self):
        """Test string validation."""
        validator = AdvancedInputValidator()
        
        # Valid string
        result = validator.validate_string("test", min_length=1, max_length=100)
        assert result == "test"
        
        # Too short
        with pytest.raises(SecurityError):
            validator.validate_string("", min_length=1)
        
        # Too long
        with pytest.raises(SecurityError):
            validator.validate_string("a" * 101, max_length=100)
    
    def test_validate_file_path(self):
        """Test file path validation."""
        validator = AdvancedInputValidator()
        
        # Valid path
        result = validator.validate_file_path("data/file.csv", allowed_extensions=['.csv'])
        assert result.name == "file.csv"
        
        # Invalid extension
        with pytest.raises(SecurityError):
            validator.validate_file_path("data/file.exe", allowed_extensions=['.csv'])
        
        # Path traversal
        with pytest.raises(SecurityError):
            validator.validate_file_path("../etc/passwd")
    
    def test_validate_url(self):
        """Test URL validation."""
        validator = AdvancedInputValidator()
        
        # Valid URL
        result = validator.validate_url("https://example.com/api")
        assert result == "https://example.com/api"
        
        # Invalid URL
        with pytest.raises(SecurityError):
            validator.validate_url("not_a_url")
    
    def test_validate_geographic_input(self):
        """Test geographic input validation."""
        validator = AdvancedInputValidator()
        
        result = validator.validate_geographic_input(0, 0