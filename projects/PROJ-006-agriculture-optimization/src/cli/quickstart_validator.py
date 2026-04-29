#!/usr/bin/env python3
"""
Quickstart Documentation Validator

Validates that quickstart.md contains all required sections and content
to ensure users can successfully set up and use the Climate-Smart
Agricultural Practices system.

Usage:
    python -m src.cli.quickstart_validator [path/to/quickstart.md]
    
Exit Codes:
    0 - Validation passed
    1 - Validation failed
    2 - File not found or read error
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Tuple, Optional

# Required sections that must be present in quickstart.md
REQUIRED_SECTIONS = [
    (r'#\s*Quickstart', 'Quickstart'),
    (r'#\s*Prerequisites', 'Prerequisites'),
    (r'#\s*Installation', 'Installation'),
    (r'#\s*Configuration', 'Configuration'),
    (r'#\s*Usage', 'Usage'),
    (r'#\s*Testing', 'Testing'),
    (r'#\s*Troubleshooting', 'Troubleshooting'),
]

# Required content patterns to check
REQUIRED_PATTERNS = [
    (r'python\s*[>=]?\s*3\.11', 'Python 3.11 version requirement'),
    (r'requirements\.txt', 'requirements.txt reference'),
    (r'pip\s+install', 'pip install command'),
    (r'export\s+[A-Z_]+', 'Environment variable export'),
    (r'pytest', 'pytest reference'),
    (r'src/', 'src/ directory reference'),
    (r'data/', 'data/ directory reference'),
]

# Required environment variables that should be documented
REQUIRED_ENV_VARS = [
    r'OPENWEATHERMAP_API_KEY',
    r'USGS_USERNAME',
    r'USGS_PASSWORD',
]

def validate_quickstart(filepath: str) -> Tuple[bool, List[str]]:
    """
    Validate quickstart.md contains all required sections and patterns.
    
    Args:
        filepath: Path to quickstart.md file
        
    Returns:
        Tuple of (is_valid, list of issues found)
    """
    issues: List[str] = []
    
    # Check file exists
    if not os.path.exists(filepath):
        issues.append(f"File not found: {filepath}")
        return False, issues
    
    # Read file content
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        issues.append(f"Error reading file: {e}")
        return False, issues
    
    # Check file is not empty
    if len(content.strip()) == 0:
        issues.append("File is empty")
        return False, issues
    
    # Check required sections
    for pattern, name in REQUIRED_SECTIONS:
        if not re.search(pattern, content, re.IGNORECASE):
            issues.append(f"Missing required section: {name}")
    
    # Check required patterns
    for pattern, name in REQUIRED_PATTERNS:
        if not re.search(pattern, content, re.IGNORECASE):
            issues.append(f"Missing required content: {name}")
    
    # Check required environment variables are documented
    env_vars_found = 0
    for pattern in REQUIRED_ENV_VARS:
        if re.search(pattern, content, re.IGNORECASE):
            env_vars_found += 1
    
    if env_vars_found < len(REQUIRED_ENV_VARS):
        missing = len(REQUIRED_ENV_VARS) - env_vars_found
        issues.append(f"Missing {missing} required environment variable(s) in documentation")
    
    # Check for code blocks (should have at least one)
    if not re.search(r'```', content):
        issues.append("No code blocks found - add usage examples")
    
    return len(issues) == 0, issues

def main() -> int:
    """Main entry point for validation."""
    # Default path relative to project root
    quickstart_path = Path("quickstart.md")
    
    # Allow override via command line
    if len(sys.argv) > 1:
        quickstart_path = Path(sys.argv[1])
    
    # Resolve to absolute path
    if not quickstart_path.is_absolute():
        quickstart_path = Path.cwd() / quickstart_path
    
    is_valid, issues = validate_quickstart(str(quickstart_path))
    
    if is_valid:
        print("✓ quickstart.md validation passed")
        return 0
    else:
        print("✗ quickstart.md validation failed:")
        for issue in issues:
            print(f"  - {issue}")
        return 1

if __name__ == "__main__":
    sys.exit(main())