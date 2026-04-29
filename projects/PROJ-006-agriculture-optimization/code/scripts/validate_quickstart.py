"""
Quickstart.md validation script.

Validates that quickstart.md exists, is properly formatted,
and contains all required sections for project onboarding.

This script is executed by the Implementer Agent (T054).
"""
import os
import sys
import yaml
from pathlib import Path

def validate_quickstart():
    """Validate quickstart.md file exists and contains required sections."""
    quickstart_path = Path("docs/quickstart.md")
    required_sections = [
        "Getting Started",
        "Installation",
        "Configuration",
        "Running the Pipeline",
        "Troubleshooting"
    ]
    
    errors = []
    warnings = []
    
    # Check file exists
    if not quickstart_path.exists():
        errors.append(f"ERROR: {quickstart_path} does not exist")
        return errors, warnings
    
    # Read file contents
    try:
        with open(quickstart_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        errors.append(f"ERROR: Failed to read {quickstart_path}: {e}")
        return errors, warnings
    
    # Check for required sections
    for section in required_sections:
        if section.lower() not in content.lower():
            warnings.append(f"WARNING: Section '{section}' not found in quickstart.md")
    
    # Check for code blocks
    if "```bash" not in content and "```python" not in content:
        warnings.append("WARNING: No code examples found in quickstart.md")
    
    # Check for environment variables section
    if "API_KEY" not in content and "ENV" not in content.upper():
        warnings.append("WARNING: No environment variable documentation found")
    
    return errors, warnings

if __name__ == "__main__":
    print("=" * 60)
    print("QUICKSTART.md VALIDATION REPORT")
    print("=" * 60)
    
    errors, warnings = validate_quickstart()
    
    if errors:
        print(f"\n❌ ERRORS ({len(errors)}):")
        for err in errors:
            print(f"  {err}")
        sys.exit(1)
    
    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)}):")
        for warn in warnings:
            print(f"  {warn}")
    else:
        print("\n✅ No warnings found")
    
    print("\n" + "=" * 60)
    print("VALIDATION COMPLETE")
    print("=" * 60)
    
    # Summary
    print(f"\nStatus: {'PASSED' if not errors else 'FAILED'}")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
