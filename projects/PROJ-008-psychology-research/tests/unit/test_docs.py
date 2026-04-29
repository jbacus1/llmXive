"""
Unit tests for documentation validation (US3 - Compliance & Documentation).

These tests validate consent form templates against IRB requirements.
Per TDD principles, tests should FAIL before implementation of T025-T028.
"""

import os
import yaml
import pytest
from pathlib import Path


# IRB Checklist Requirements for Consent Forms
REQUIRED_CONSENT_SECTIONS = [
    "study_title",
    "purpose",
    "procedures",
    "risks",
    "benefits",
    "confidentiality",
    "compensation",
    "voluntary_participation",
    "contact_information",
    "irb_approval_statement"
]

REQUIRED_CONSENT_FORMS = [
    "parent_consent.md",
    "child_assent.md"
]

class TestConsentFormValidation:
    """Test consent form templates meet IRB compliance requirements."""
    
    @pytest.fixture
    def consent_forms_dir(self):
        """Get path to consent forms directory."""
        return Path("docs/consent-forms")
    
    def test_consent_forms_directory_exists(self, consent_forms_dir):
        """Verify consent forms directory exists."""
        assert consent_forms_dir.exists(), (
            f"Consent forms directory not found at {consent_forms_dir}. "
            "Create docs/consent-forms/ directory (Task T026)."
        )
    
    def test_required_consent_forms_exist(self, consent_forms_dir):
        """Verify all required consent form templates exist."""
        missing_forms = []
        for form_name in REQUIRED_CONSENT_FORMS:
            form_path = consent_forms_dir / form_name
            if not form_path.exists():
                missing_forms.append(form_name)
        
        if missing_forms:
            pytest.fail(
                f"Missing required consent form templates: {missing_forms}. "
                "Create templates per Task T026."
            )
    
    @pytest.mark.parametrize("form_name", REQUIRED_CONSENT_FORMS)
    def test_consent_form_has_required_sections(self, consent_forms_dir, form_name):
        """Verify each consent form contains all IRB-required sections."""
        form_path = consent_forms_dir / form_name
        
        if not form_path.exists():
            pytest.skip(f"Form {form_name} not yet created - expected before T026")
        
        content = form_path.read_text()
        missing_sections = []
        
        for section in REQUIRED_CONSENT_SECTIONS:
            # Check for section headers (markdown or explicit markers)
            section_patterns = [
                f"#{section.replace('_', ' ').title()}",
                f"## {section.replace('_', ' ').title()}",
                f"--- {section.replace('_', ' ').title()} ---",
                f"[{section.upper()}]",
            ]
            
            if not any(pattern in content for pattern in section_patterns):
                missing_sections.append(section)
        
        if missing_sections:
            pytest.fail(
                f"Consent form '{form_name}' missing required sections: {missing_sections}. "
                "Add missing sections per IRB requirements."
            )
    
    def test_consent_forms_are_markdown(self, consent_forms_dir):
        """Verify consent forms use markdown format."""
        for form_name in REQUIRED_CONSENT_FORMS:
            form_path = consent_forms_dir / form_name
            if form_path.exists():
                assert form_path.suffix == ".md", (
                    f"Consent form '{form_name}' should be markdown (.md), "
                    f"found {form_path.suffix}"
                )
    
    def test_parent_consent_has_age_restrictions(self, consent_forms_dir):
        """Verify parent consent form includes age eligibility criteria."""
        form_path = consent_forms_dir / "parent_consent.md"
        
        if not form_path.exists():
            pytest.skip("Parent consent form not yet created - expected before T026")
        
        content = form_path.read_text().lower()
        age_indicators = ["age", "years old", "between", "participant criteria"]
        
        if not any(indicator in content for indicator in age_indicators):
            pytest.fail(
                "Parent consent form missing age eligibility criteria. "
                "Add participant age requirements per IRB protocol."
            )
    
    def test_child_assent_is_age_appropriate(self, consent_forms_dir):
        """Verify child assent form uses age-appropriate language."""
        form_path = consent_forms_dir / "child_assent.md"
        
        if not form_path.exists():
            pytest.skip("Child assent form not yet created - expected before T026")
        
        content = form_path.read_text()
        
        # Check for simplified language indicators
        child_friendly_patterns = [
            "you will",
            "your choice",
            "it's okay",
            "ask questions",
            "stop anytime"
        ]
        
        if not any(pattern in content.lower() for pattern in child_friendly_patterns):
            pytest.fail(
                "Child assent form may not use age-appropriate language. "
                "Review and simplify language for child participants."
            )
    
    def test_consent_forms_have_irb_approval_section(self, consent_forms_dir):
        """Verify consent forms include IRB approval statement."""
        for form_name in REQUIRED_CONSENT_FORMS:
            form_path = consent_forms_dir / form_name
            
            if not form_path.exists():
                continue
            
            content = form_path.read_text().lower()
            irb_indicators = [
                "institutional review board",
                "irb",
                "ethics committee",
                "approval number",
                "irb #"
            ]
            
            if not any(indicator in content for indicator in irb_indicators):
                pytest.fail(
                    f"Consent form '{form_name}' missing IRB approval statement. "
                    "Add IRB approval information per compliance requirements."
                )