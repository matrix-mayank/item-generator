"""
Configuration management for Reading Comprehension Item Generator.
Default settings are based on NY/Texas Grade 3-4 standardized test items.
"""

DEFAULT_CONFIG = {
    'passage_word_count': 20,   # specific word count
    'questions_per_passage': 1,  # Always 1 question
    'distractors_per_question': 2,
    'grade_level': 4,
    'state_standards': ['NY', 'TX'],  # New York and Texas standards
    'inference_type': 'all',  # all/text-explicit/text-implicit/script-implicit
    'custom_manual': None,  # Path to uploaded manual
    'question_types': ['vocabulary', 'comprehension', 'inference']
}

# Available configuration options
VALID_INFERENCE_TYPES = ['all', 'text-explicit', 'text-implicit', 'script-implicit']
VALID_GRADES = list(range(3, 13))  # Grades 3-12
VALID_STATE_STANDARDS = ['NY', 'TX', 'CA', 'FL', 'Other']
VALID_QUESTION_TYPES = ['vocabulary', 'comprehension', 'inference', 'main-idea', 'detail']

def validate_config(config):
    """Validate configuration settings"""
    errors = []
    
    if config.get('passage_word_count', 0) < 10 or config.get('passage_word_count', 0) > 1000:
        errors.append("passage_word_count must be between 10 and 1000")
    
    if config.get('distractors_per_question', 0) < 2 or config.get('distractors_per_question', 0) > 4:
        errors.append("distractors_per_question must be between 2 and 4")
    
    if config.get('grade_level', 0) not in VALID_GRADES:
        errors.append(f"grade_level must be between 3 and 12")
    
    if config.get('inference_type') not in VALID_INFERENCE_TYPES:
        errors.append(f"Invalid inference_type. Must be one of {VALID_INFERENCE_TYPES}")
    
    return errors

def merge_config(base_config, updates):
    """Merge configuration updates with base config"""
    merged = base_config.copy()
    
    for key, value in updates.items():
        if key in DEFAULT_CONFIG:
            merged[key] = value
    
    # Always ensure 1 question per passage
    merged['questions_per_passage'] = 1
    
    return merged
