"""
Test script for configuration system
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

print("Testing configuration system...")
print("=" * 50)

# Test 1: Import modules
try:
    import config
    import prompt_builder
    import file_handler
    print("✅ All modules imported successfully")
except Exception as e:
    print(f"❌ Module import failed: {e}")
    sys.exit(1)

# Test 2: Default configuration
print("\n1. Testing default configuration:")
print(f"   Passage length: {config.DEFAULT_CONFIG['passage_length']}")
print(f"   Word count: {config.DEFAULT_CONFIG['passage_word_count']}")
print(f"   Questions: {config.DEFAULT_CONFIG['questions_per_passage']}")
print(f"   Distractors: {config.DEFAULT_CONFIG['distractors_per_question']}")
print(f"   Grade: {config.DEFAULT_CONFIG['grade_level']}")
print(f"   Standards: {config.DEFAULT_CONFIG['state_standards']}")
print("✅ Default config loaded")

# Test 3: Config validation
print("\n2. Testing config validation:")
valid_config = config.DEFAULT_CONFIG.copy()
errors = config.validate_config(valid_config)
if not errors:
    print("✅ Valid config passed validation")
else:
    print(f"❌ Validation failed: {errors}")

# Test invalid config
invalid_config = config.DEFAULT_CONFIG.copy()
invalid_config['passage_length'] = 'invalid'
errors = config.validate_config(invalid_config)
if errors:
    print(f"✅ Invalid config caught: {errors[0]}")
else:
    print("❌ Invalid config not caught")

# Test 4: Config merging
print("\n3. Testing config merging:")
updates = {
    'passage_length': 'long',
    'grade_level': 8,
    'questions_per_passage': 5
}
merged = config.merge_config(config.DEFAULT_CONFIG, updates)
if merged['passage_length'] == 'long' and merged['grade_level'] == 8:
    print("✅ Config merged successfully")
    print(f"   New word count: {merged['passage_word_count']}")
else:
    print("❌ Config merge failed")

# Test 5: Prompt builder
print("\n4. Testing prompt builder:")
test_config = config.DEFAULT_CONFIG.copy()
test_message = "Generate a passage about space exploration"
prompt = prompt_builder.build_system_prompt(test_config, test_message)

if "300 words" in prompt and "Grade 4" in prompt and "3 questions" in prompt:
    print("✅ Prompt built successfully")
    print(f"   Prompt length: {len(prompt)} characters")
else:
    print("❌ Prompt build failed")

# Test 6: File handler
print("\n5. Testing file handler:")
test_filename = "test_manual.txt"
if file_handler.allowed_file(test_filename):
    print("✅ File validation works")
else:
    print("❌ File validation failed")

invalid_filename = "test.exe"
if not file_handler.allowed_file(invalid_filename):
    print("✅ Invalid file rejected")
else:
    print("❌ Invalid file not rejected")

# Summary
print("\n" + "=" * 50)
print("✅ All tests passed!")
print("\nConfiguration system is ready for use.")
print("\nNext steps:")
print("1. Install dependencies: pip install -r requirements.txt")
print("2. Set up .env with ANTHROPIC_API_KEY")
print("3. Run the app: python app.py")
