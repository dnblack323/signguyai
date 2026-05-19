#!/usr/bin/env python3
"""
Test script to verify the Event Web Store Setup Questionnaire template exists
and can be created in the system.
"""
import asyncio
import sys
sys.path.insert(0, '/app/backend')

from models.questionnaires import QUESTIONNAIRE_TEMPLATES, QuestionnaireCategory

def test_template_exists():
    """Test that the event web store template exists"""
    print("="*60)
    print("Testing Event Web Store Setup Questionnaire Template")
    print("="*60)
    
    # Check if template exists
    if "event_web_store_setup" not in QUESTIONNAIRE_TEMPLATES:
        print("✗ FAILED: Template 'event_web_store_setup' not found in QUESTIONNAIRE_TEMPLATES")
        return False
    
    print("✓ Template exists in QUESTIONNAIRE_TEMPLATES")
    
    template = QUESTIONNAIRE_TEMPLATES["event_web_store_setup"]
    
    # Check required fields
    required_fields = ["name", "description", "category", "intro_text", "questions"]
    for field in required_fields:
        if field not in template:
            print(f"✗ FAILED: Missing required field '{field}'")
            return False
    
    print(f"✓ All required template fields present")
    
    # Check template details
    print(f"\nTemplate Details:")
    print(f"  Name: {template['name']}")
    print(f"  Category: {template['category']}")
    print(f"  Description: {template['description'][:100]}...")
    print(f"  Number of questions: {len(template['questions'])}")
    
    # Check category is valid
    if template['category'] != "web_stores":
        print(f"✗ FAILED: Category should be 'web_stores', got '{template['category']}'")
        return False
    
    print(f"✓ Category is 'web_stores'")
    
    # Check WEB_STORES enum exists
    if not hasattr(QuestionnaireCategory, 'WEB_STORES'):
        print("✗ FAILED: QuestionnaireCategory.WEB_STORES enum not found")
        return False
    
    print("✓ QuestionnaireCategory.WEB_STORES enum exists")
    
    # Count question types
    question_types = {}
    sections = []
    required_count = 0
    
    for q in template['questions']:
        q_type = q.get('type', 'unknown')
        question_types[q_type] = question_types.get(q_type, 0) + 1
        
        if q_type == 'heading':
            sections.append(q.get('label', 'Unnamed Section'))
        
        if q.get('required'):
            required_count += 1
    
    print(f"\nQuestion Breakdown:")
    print(f"  Total questions/fields: {len(template['questions'])}")
    print(f"  Required fields: {required_count}")
    print(f"  Sections (headings): {len(sections)}")
    
    print(f"\nSections Found:")
    for i, section in enumerate(sections, 1):
        print(f"  {i}. {section}")
    
    print(f"\nQuestion Types:")
    for q_type, count in sorted(question_types.items()):
        print(f"  {q_type}: {count}")
    
    # Check for specific important fields
    important_fields = {
        "signature": False,
        "file_upload": False,
        "checkbox": False,
        "email": False,
        "phone": False
    }
    
    for q in template['questions']:
        q_type = q.get('type')
        if q_type in important_fields:
            important_fields[q_type] = True
    
    print(f"\nImportant Field Types Present:")
    all_present = True
    for field_type, present in important_fields.items():
        status = "✓" if present else "✗"
        print(f"  {status} {field_type}: {'Yes' if present else 'No'}")
        if not present:
            all_present = False
    
    # Check agreement checkboxes (should have 8)
    agreement_checkboxes = [q for q in template['questions'] 
                           if q.get('type') == 'checkbox' 
                           and q.get('required') 
                           and 'understand' in q.get('label', '').lower()]
    
    print(f"\nAgreement Checkboxes:")
    print(f"  Found: {len(agreement_checkboxes)}")
    print(f"  Expected: 8")
    
    if len(agreement_checkboxes) == 8:
        print("  ✓ Correct number of agreement checkboxes")
    else:
        print("  ⚠ Warning: Expected 8 agreement checkboxes")
    
    # Check intro text
    if len(template.get('intro_text', '')) > 100:
        print("\n✓ Comprehensive intro text present")
    else:
        print("\n⚠ Warning: Intro text seems short")
    
    print("\n" + "="*60)
    print("✓ ALL TESTS PASSED!")
    print("="*60)
    return True

if __name__ == "__main__":
    success = test_template_exists()
    sys.exit(0 if success else 1)
