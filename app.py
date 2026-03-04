import os
import re
import json
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from anthropic import Anthropic
from dotenv import load_dotenv
import pandas as pd
from difficulty_estimator import DifficultyEstimator
from config import DEFAULT_CONFIG, validate_config, merge_config
from prompt_builder import build_system_prompt, build_chat_system_message
from file_handler import process_manual_upload, allowed_file

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['MANUALS_DIR'] = os.path.join(app.config['UPLOAD_FOLDER'], 'manuals')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size


def get_manual_text(config):
    """Return full manual text. Manuals are stored in a file to avoid session cookie truncation (~4KB limit)."""
    manual_id = config.get('custom_manual_id')
    if manual_id:
        path = os.path.join(app.config['MANUALS_DIR'], manual_id + '.txt')
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8', errors='replace') as f:
                    return f.read()
            except Exception:
                pass
    return config.get('custom_manual')  # fallback: inline (may be truncated if large)

client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
_model_dir = os.getenv('MODEL_PATH') or os.path.join(os.path.dirname(__file__), 'models')
difficulty_estimator = DifficultyEstimator(_model_dir)

# Configuration will be stored in session
# Prompts will be dynamically generated using prompt_builder.py


def message_for_display(raw_message):
    """Strip metadata, design notes, and any content after the item so chat shows only the item."""
    if not raw_message or not raw_message.strip():
        return raw_message
    text = raw_message.strip()
    # Remove everything from --- or METADATA onward (no design notes or metadata in chat)
    for sep in ('\n---', '\nMETADATA:', '\n\nMETADATA:', '\nDesign note', '\nDesign Note', '\n*Note'):
        idx = text.find(sep)
        if idx != -1:
            text = text[:idx].rstrip()
    # Keep only from first "Passage:" so we drop any leading "Here's your item..." or design blurb
    for marker in ('Passage:', 'passage:'):
        passage_start = text.find(marker)
        if passage_start != -1:
            text = text[passage_start:]
            break
    return text.strip()


def capitalize_answer_fields(item):
    """Ensure target_answer and distractors have proper first-letter capitalization."""
    for key in ('target_answer', 'distractor_1', 'distractor_2', 'distractor_3', 'distractor_4'):
        val = item.get(key)
        if val and isinstance(val, str):
            val = val.strip()
            if val and val[0].islower():
                item[key] = val[0].upper() + val[1:]
            else:
                item[key] = val
    return item


def clean_field_content(content):
    """Remove asterisks and explanatory notes from field content"""
    if not content:
        return content
    
    # Remove content after asterisk (explanatory notes)
    if '*' in content:
        content = content.split('*')[0].strip()
    
    # Remove any remaining asterisks
    content = content.replace('*', '').strip()
    
    # Take only first line if multiple lines (for answer choices)
    lines = content.split('\n')
    if lines:
        content = lines[0].strip()
    
    return content


def parse_item_from_response(response_text):
    """
    Parse Claude's response into structured item.
    Handles both old ROAR format and new generic reading comp format.
    """
    text = response_text.strip()
    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # If the response is inside a markdown code block, extract the inner content
    code_block = re.search(r'```(?:\w*)\n?(.*?)```', text, re.DOTALL)
    if code_block:
        text = code_block.group(1).strip()
    # Remove all markdown formatting
    text_clean = text.replace('**', '')
    
    print("PARSING RESPONSE - First 800 chars (cleaned):")
    print(text_clean[:800])
    print("=" * 50)
    
    item = {
        'passage': '',
        'questions': [],  # List of questions with options
        'metadata': {}
    }
    
    # Extract passage (can be multi-line) - case-insensitive start
    passage_match = text_clean.find('Passage:')
    if passage_match == -1:
        passage_match = text_clean.lower().find('passage:')
    if passage_match != -1:
        passage_start = passage_match + len('Passage:')
        # Find the end of passage (before first question or separator)
        passage_end = text_clean.find('\n---', passage_start)
        if passage_end == -1:
            passage_end = text_clean.find('\nQuestion', passage_start)
        if passage_end != -1:
            item['passage'] = text_clean[passage_start:passage_end].strip()
    
    # Extract questions - look for multiple questions
    question_num = 1
    search_start = 0
    
    while True:
        # Try to find Question N:
        question_marker = f'Question {question_num}:'
        question_match = text_clean.find(question_marker, search_start)
        
        if question_match == -1:
            # Try without number
            if question_num == 1:
                question_marker = 'Question:'
                question_match = text_clean.find(question_marker, search_start)
            
            if question_match == -1:
                break
        
        question_obj = {
            'question': '',
            'correct_answer': '',
            'distractors': [],
            'type': ''
        }
        
        # Extract question text
        question_start = question_match + len(question_marker)
        
        # Find options start (A), B), etc.) or Target Answer: (new format, case-insensitive)
        option_a_match = text_clean.find('\nA)', question_start)
        if option_a_match == -1:
            option_a_match = text_clean.find('\nA.', question_start)
        target_re = re.search(r'\n\s*Target\s+Answer\s*:', text_clean[question_start:], re.IGNORECASE)
        target_match = question_start + target_re.start() if target_re else -1
        
        if option_a_match != -1:
            question_obj['question'] = text_clean[question_start:option_a_match].strip()
            
            # Extract options A, B, C, D
            options = []
            for letter in ['A', 'B', 'C', 'D', 'E']:
                for separator in [')', '.']:
                    option_marker = f'\n{letter}{separator}'
                    option_match = text_clean.find(option_marker, option_a_match if letter == 'A' else search_start)
                    
                    if option_match != -1:
                        option_start = option_match + len(option_marker)
                        
                        # Find next option or end
                        next_letter = chr(ord(letter) + 1)
                        option_end = text_clean.find(f'\n{next_letter})', option_start)
                        if option_end == -1:
                            option_end = text_clean.find(f'\n{next_letter}.', option_start)
                        if option_end == -1:
                            option_end = text_clean.find('\nType:', option_start)
                        if option_end == -1:
                            option_end = text_clean.find('\n---', option_start)
                        if option_end == -1:
                            option_end = text_clean.find(f'\nQuestion {question_num + 1}:', option_start)
                        
                        if option_end != -1:
                            option_text = text_clean[option_start:option_end].strip()
                            if option_text:
                                options.append(option_text)
                        break
            
            # First option is correct, rest are distractors
            if options:
                question_obj['correct_answer'] = options[0]
                question_obj['distractors'] = options[1:]
            
            # Extract question type
            type_match = text_clean.find('Type:', option_a_match)
            if type_match != -1:
                type_start = type_match + len('Type:')
                type_end = text_clean.find('\n', type_start)
                if type_end != -1:
                    question_obj['type'] = text_clean[type_start:type_end].strip()
        elif target_match != -1:
            # New format: Question / Target Answer / Distractor 1, 2, ... (case-insensitive)
            question_obj['question'] = text_clean[question_start:target_match].strip()
            ta_colon = text_clean.find(':', target_match)
            ta_start = ta_colon + 1 if ta_colon != -1 else target_match + 14
            d1_re = re.search(r'\n\s*Distractor\s+1\s*:', text_clean[ta_start:], re.IGNORECASE)
            d1_match = ta_start + d1_re.start() if d1_re else -1
            if d1_match != -1:
                question_obj['correct_answer'] = text_clean[ta_start:d1_match].strip()
            else:
                end = text_clean.find('\n---', ta_start)
                if end == -1:
                    end = text_clean.find('\n\n', ta_start)
                if end != -1:
                    question_obj['correct_answer'] = text_clean[ta_start:end].strip()
                else:
                    question_obj['correct_answer'] = text_clean[ta_start:].strip()
            # Distractors (case-insensitive "Distractor N:")
            for i in range(1, 5):
                d_re = re.search(r'\n\s*Distractor\s+' + str(i) + r'\s*:', text_clean[question_start:], re.IGNORECASE)
                if not d_re:
                    continue
                d_match = question_start + d_re.start()
                d_start = text_clean.find(':', d_match) + 1
                next_re = re.search(r'\n\s*Distractor\s+' + str(i + 1) + r'\s*:', text_clean[d_start:], re.IGNORECASE)
                next_m = d_start + next_re.start() if next_re else -1
                if next_m == -1:
                    next_m = text_clean.find('\n---', d_start)
                if next_m == -1:
                    next_m = text_clean.find('\nMETADATA:', d_start)
                if next_m == -1:
                    next_m = len(text_clean)
                content = text_clean[d_start:next_m].strip()
                if '\n' in content:
                    content = content.split('\n')[0].strip()
                if content:
                    question_obj['distractors'].append(content)
        
        if question_obj['question']:
            item['questions'].append(question_obj)
        
        question_num += 1
        search_start = question_match + len(question_marker) + 100  # Move forward
        
        # Safety limit
        if question_num > 10:
            break
    
    # If no questions found in new format, try old ROAR format
    if not item['questions']:
        roar_item = parse_roar_format(text_clean)
        if roar_item:
            return roar_item
    
    # Normalize to flat shape for frontend (question, target_answer, distractor_1, ...)
    if item['questions']:
        q0 = item['questions'][0]
        item['question'] = q0.get('question', '')
        item['target_answer'] = q0.get('correct_answer', '')
        distractors = q0.get('distractors') or []
        for i, d in enumerate(distractors):
            if i < 4:
                item[f'distractor_{i + 1}'] = d
        for i in range(len(distractors), 4):
            item[f'distractor_{i + 1}'] = ''
        # If we still have no target/distractors, try ROAR parser and merge flat fields
        if not item['target_answer'] and not any(item.get(f'distractor_{i}') for i in range(1, 5)):
            roar_item = parse_roar_format(text_clean)
            if roar_item:
                item['question'] = roar_item.get('question') or item['question']
                item['target_answer'] = roar_item.get('target_answer', '')
                for i in range(1, 5):
                    key = f'distractor_{i}'
                    if roar_item.get(key):
                        item[key] = roar_item[key]
    
    # Extract metadata
    metadata_start = text_clean.find('METADATA:')
    if metadata_start != -1:
        metadata_section = text_clean[metadata_start:]
        
        for line in metadata_section.split('\n'):
            line = line.strip()
            if ':' not in line or line.startswith('---'):
                continue
            
            parts = line.split(':', 1)
            if len(parts) == 2:
                key = parts[0].strip().lower().replace(' ', '_')
                value = parts[1].strip()
                item['metadata'][key] = value
    
    print(f"Parsed passage length: {len(item['passage'])}")
    print(f"Parsed {len(item['questions'])} questions")
    
    capitalize_answer_fields(item)
    return item


def parse_roar_format(text_clean):
    """Parse old ROAR format for backward compatibility"""
    item = {
        'passage': '',
        'question': '',
        'target_answer': '',
        'distractor_1': '',
        'distractor_2': '',
        'event_chain_relation': '',
        'knowledge_base_inference': '',
        'qar_level': '',
        'coherence_level': '',
        'explanatory_stance': ''
    }
    
    # Extract passage
    passage_match = text_clean.find('Passage:')
    if passage_match != -1:
        passage_start = passage_match + len('Passage:')
        passage_end = text_clean.find('\n\nQuestion:', passage_start)
        if passage_end == -1:
            passage_end = text_clean.find('\nQuestion:', passage_start)
        if passage_end != -1:
            item['passage'] = text_clean[passage_start:passage_end].strip()
    
    # Extract question (case-insensitive for Target Answer)
    question_match = text_clean.find('Question:')
    if question_match == -1:
        question_match = text_clean.lower().find('question:')
    if question_match != -1:
        qm_len = len('Question:')
        if text_clean[question_match:question_match+qm_len].lower() != 'question:':
            qm_len = len('question:')
        question_start = question_match + qm_len
        ta_re = re.search(r'\n\s*Target\s+Answer\s*:', text_clean[question_start:], re.IGNORECASE)
        question_end = question_start + ta_re.start() if ta_re else -1
        if question_end != -1:
            item['question'] = text_clean[question_start:question_end].strip()
    
    # Extract target answer (case-insensitive)
    ta_re = re.search(r'Target\s+Answer\s*:', text_clean, re.IGNORECASE)
    if ta_re:
        target_match = ta_re.start()
        target_start = ta_re.end()
        d1_re = re.search(r'\n\s*Distractor\s+1\s*:', text_clean[target_start:], re.IGNORECASE)
        target_end = target_start + d1_re.start() if d1_re else -1
        if target_end != -1:
            item['target_answer'] = text_clean[target_start:target_end].strip()
        else:
            end = text_clean.find('\n---', target_start)
            if end == -1:
                end = len(text_clean)
            item['target_answer'] = text_clean[target_start:end].strip()
    
    # Extract Distractor 1 (case-insensitive)
    d1_re = re.search(r'Distractor\s+1\s*:', text_clean, re.IGNORECASE)
    if d1_re:
        d1_match = d1_re.start()
        d1_start = text_clean.find(':', d1_match) + 1
        d2_re = re.search(r'\n\s*Distractor\s+2\s*:', text_clean[d1_start:], re.IGNORECASE)
        d1_end = d1_start + d2_re.start() if d2_re else -1
        if d1_end != -1:
            content = text_clean[d1_start:d1_end].strip()
            paren_pos = content.find('(')
            if paren_pos > 0:
                content = content[:paren_pos].strip()
            if '\n' in content:
                content = content.split('\n')[0].strip()
            item['distractor_1'] = content
    
    # Extract Distractor 2 (case-insensitive)
    d2_re = re.search(r'Distractor\s+2\s*:', text_clean, re.IGNORECASE)
    d2_match = d2_re.start() if d2_re else -1
    if d2_match != -1:
        d2_start = text_clean.find(':', d2_match) + 1
        d2_end = text_clean.find('\nMETADATA:', d2_match)
        if d2_end == -1:
            d2_end = text_clean.find('\n\n---', d2_match)
        if d2_end == -1:
            d2_end = text_clean.find('\n---', d2_match)
        if d2_end == -1:
            d2_end = text_clean.find('\n\n', d2_start)
        
        if d2_end != -1:
            content = text_clean[d2_start:d2_end].strip()
            paren_pos = content.find('(')
            if paren_pos > 0:
                content = content[:paren_pos].strip()
            if '\n' in content:
                content = content.split('\n')[0].strip()
            content = content.replace('---', '').strip()
            item['distractor_2'] = content
    
    # Parse metadata
    metadata_start = text_clean.find('METADATA:')
    if metadata_start != -1:
        metadata_section = text_clean[metadata_start:]
        
        for line in metadata_section.split('\n'):
            line = line.strip()
            if ':' not in line:
                continue
            if line.startswith('Event-Chain Relation:'):
                item['event_chain_relation'] = line.split(':', 1)[1].strip()
            elif line.startswith('Knowledge-Base Inference:'):
                item['knowledge_base_inference'] = line.split(':', 1)[1].strip()
            elif line.startswith('QAR Level:'):
                item['qar_level'] = line.split(':', 1)[1].strip()
            elif line.startswith('Coherence Level:'):
                item['coherence_level'] = line.split(':', 1)[1].strip()
            elif line.startswith('Explanatory Stance:'):
                item['explanatory_stance'] = line.split(':', 1)[1].strip()
    
    # Only return if we found at least passage and question
    if item['passage'] and item['question']:
        capitalize_answer_fields(item)
        return item
    
    return None


@app.route('/')
def index():
    # Initialize session config if not present
    if 'config' not in session:
        session['config'] = DEFAULT_CONFIG.copy()
    return render_template('index.html')


@app.route('/get_config', methods=['GET'])
def get_config():
    """Get current configuration"""
    if 'config' not in session:
        session['config'] = DEFAULT_CONFIG.copy()
    out = dict(session['config'])
    # Frontend checks custom_manual for "manual loaded"; we store full text in file, id in session
    if out.get('custom_manual_id') and not out.get('custom_manual'):
        out['custom_manual'] = True  # signal that a manual is loaded (content read from file when needed)
    out['difficulty_model_loaded'] = difficulty_estimator.is_loaded()
    return jsonify(out)


@app.route('/model_status', methods=['GET'])
def model_status():
    """Check if the difficulty estimation model (BERT + Ridge) is loaded. No terminal needed."""
    return jsonify({'loaded': difficulty_estimator.is_loaded()})


@app.route('/update_config', methods=['POST'])
def update_config():
    """Update configuration settings"""
    try:
        data = request.json
        updates = data.get('config', {})
        
        # Ensure passage_word_count is an integer
        if 'passage_word_count' in updates:
            try:
                updates['passage_word_count'] = int(updates['passage_word_count'])
            except (TypeError, ValueError):
                updates['passage_word_count'] = 20
        
        # Get current config or use default
        current_config = session.get('config', DEFAULT_CONFIG.copy())
        
        # Merge with updates
        new_config = merge_config(current_config, updates)
        
        # Validate
        errors = validate_config(new_config)
        if errors:
            return jsonify({'error': ', '.join(errors)}), 400
        
        # Save to session
        session['config'] = new_config
        session.modified = True
        
        return jsonify({
            'status': 'success',
            'config': new_config
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/upload_manual', methods=['POST'])
def upload_manual():
    """Handle manual file upload"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Process the file
        success, result = process_manual_upload(file, app.config['UPLOAD_FOLDER'])
        
        if not success:
            return jsonify({'error': result}), 400
        
        # Store manual in file so session cookie is not truncated (Flask session ~4KB limit)
        os.makedirs(app.config['MANUALS_DIR'], exist_ok=True)
        manual_id = str(uuid.uuid4())
        manual_path = os.path.join(app.config['MANUALS_DIR'], manual_id + '.txt')
        with open(manual_path, 'w', encoding='utf-8') as f:
            f.write(result)
        
        if 'config' not in session:
            session['config'] = DEFAULT_CONFIG.copy()
        session['config']['custom_manual_id'] = manual_id
        session['config']['custom_manual'] = None  # no longer store full text in session
        session.modified = True
        
        return jsonify({
            'status': 'success',
            'message': 'Manual uploaded successfully',
            'preview': result[:200] + '...' if len(result) > 200 else result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/clear_manual', methods=['POST'])
def clear_manual():
    """Clear uploaded manual"""
    try:
        if 'config' in session:
            manual_id = session['config'].get('custom_manual_id')
            if manual_id:
                path = os.path.join(app.config['MANUALS_DIR'], manual_id + '.txt')
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except OSError:
                        pass
            session['config']['custom_manual_id'] = None
            session['config']['custom_manual'] = None
            session.modified = True
        
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/chat', methods=['POST'])
def chat():
    print("=" * 50)
    print("CHAT ENDPOINT CALLED")
    print("=" * 50)
    try:
        data = request.json
        user_message = data.get('message', '')
        print(f"User message: {user_message}")
        
        # Initialize config if not present
        if 'config' not in session:
            session['config'] = DEFAULT_CONFIG.copy()
        
        if 'conversation_history' not in session:
            session['conversation_history'] = []
        
        # If client sent config (e.g. from form), merge over session so generation always uses it
        request_config = data.get('config')
        if request_config and isinstance(request_config, dict):
            if 'passage_word_count' in request_config:
                try:
                    request_config['passage_word_count'] = int(request_config['passage_word_count'])
                except (TypeError, ValueError):
                    request_config['passage_word_count'] = 20
                request_config['passage_word_count'] = max(10, min(1000, request_config['passage_word_count']))
            if 'distractors_per_question' in request_config:
                try:
                    request_config['distractors_per_question'] = int(request_config['distractors_per_question'])
                except (TypeError, ValueError):
                    request_config['distractors_per_question'] = 2
            current = session.get('config', DEFAULT_CONFIG.copy())
            session['config'] = merge_config(current, request_config)
            session.modified = True
        
        config = session['config']
        conversation_history = session['conversation_history']
        
        # Load full manual from file (avoids session cookie truncation); fallback to session for old data
        manual_text = get_manual_text(config)
        
        # Use request body config for injected instruction so we always use what the user just sent (not stale session)
        effective_config = request_config if (request_config and isinstance(request_config, dict)) else config
        if request_config:
            print(f"Request body config: passage_word_count={request_config.get('passage_word_count')}, distractors={request_config.get('distractors_per_question')}")
        word_count = effective_config.get('passage_word_count', 20)
        try:
            word_count = int(word_count)
        except (TypeError, ValueError):
            word_count = 20
        word_count = max(10, min(1000, word_count))
        num_d = effective_config.get('distractors_per_question', 2)
        try:
            num_d = int(num_d)
        except (TypeError, ValueError):
            num_d = 2
        num_d = max(2, min(4, num_d))
        
        print(f"Using config: passage_word_count={word_count}, distractors={num_d}, (from request: {request_config is not None})")
        
        conversation_history.append({
            'role': 'user',
            'content': user_message
        })
        
        # Build user message for API: include full manual in chat (like when user pastes it) so model follows it
        manual_reminder = " (3) You MUST follow the guidelines below for this item." if manual_text else ""
        user_message_for_api = (
            f"[Your response: (1) The passage must be exactly {word_count} words—count them. "
            f"(2) Include exactly {num_d} wrong-answer options (Distractor 1 through Distractor {num_d}).{manual_reminder}] "
        )
        if manual_text:
            user_message_for_api += "\n\n**Guidelines to follow (apply to this item):**\n" + manual_text.strip() + "\n\n**User request:** " + user_message
        else:
            user_message_for_api += user_message
        
        messages = [{'role': msg['role'], 'content': msg['content']} for msg in conversation_history]
        messages[-1] = {'role': 'user', 'content': user_message_for_api}
        
        # Build system prompt from config, but force passage_word_count and distractors from this request so they match the injected message
        config_for_prompt = {**config, 'passage_word_count': word_count, 'distractors_per_question': num_d}
        system_prompt = build_system_prompt(
            config_for_prompt,
            user_message,
            manual_text
        )
        
        chat_system_message = build_chat_system_message(has_custom_manual=bool(manual_text))
        full_system_message = chat_system_message + "\n\n" + system_prompt
        
        # Use streaming for faster responses
        with client.messages.stream(
            model='claude-opus-4-6',
            max_tokens=4000,
            temperature=1,
            system=full_system_message,
            messages=messages
        ) as stream:
            assistant_message = ""
            for text in stream.text_stream:
                assistant_message += text
        
        conversation_history.append({
            'role': 'assistant',
            'content': assistant_message
        })
        
        session['conversation_history'] = conversation_history
        
        print("=" * 50)
        print("ASSISTANT MESSAGE:")
        print(assistant_message[:500])  # First 500 chars
        print("=" * 50)
        
        parsed_item = None
        difficulty = None
        
        # Try to parse item from response
        try:
            parsed_item = parse_item_from_response(assistant_message)
            print(f"Parsed item: {parsed_item}")
            # Check if we actually found an item (has at least passage or question)
            if parsed_item and (parsed_item.get('passage') or parsed_item.get('question')):
                session['current_item'] = parsed_item
                print(f"Item saved to session")
                
                if difficulty_estimator.is_loaded():
                    grade_level = config.get('grade_level', 4)
                    item_for_difficulty = {**parsed_item, 'grade': f'Grade{grade_level}'}
                    difficulty = difficulty_estimator.estimate_difficulty(item_for_difficulty)
                    print(f"Difficulty estimated: {difficulty}")
            else:
                print(f"No valid item found - passage: {parsed_item.get('passage') if parsed_item else None}, question: {parsed_item.get('question') if parsed_item else None}")
                parsed_item = None
        except Exception as e:
            print(f"Error parsing item: {e}")
            import traceback
            traceback.print_exc()
            parsed_item = None
        
        response_data = {
            'message': message_for_display(assistant_message),
            'item': parsed_item,
            'difficulty': difficulty
        }
        print(f"Returning response with item: {parsed_item is not None}")
        print(f"Item keys: {list(parsed_item.keys()) if parsed_item else 'None'}")
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/clear', methods=['POST'])
def clear_session():
    session.clear()
    return jsonify({'status': 'success'})


@app.route('/get_current_item', methods=['GET'])
def get_current_item():
    current_item = session.get('current_item')
    difficulty = None

    if current_item and difficulty_estimator.is_loaded():
        grade_level = session.get('config', {}).get('grade_level', 4)
        item_with_grade = {**current_item, 'grade': f'Grade{grade_level}'}
        difficulty = difficulty_estimator.estimate_difficulty(item_with_grade)
    
    return jsonify({
        'item': current_item,
        'difficulty': difficulty
    })


@app.route('/export_item', methods=['POST'])
def export_item():
    try:
        current_item = session.get('current_item')
        
        if not current_item:
            return jsonify({'error': 'No item to export'}), 400
        
        # Create CSV in memory
        from io import StringIO
        import csv
        
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=sorted(current_item.keys()))
        writer.writeheader()
        writer.writerow(current_item)
        
        csv_content = output.getvalue()
        output.close()
        
        # Create response with CSV file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'roar_item_{timestamp}.csv'
        
        from flask import make_response
        response = make_response(csv_content)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        return response
        
    except Exception as e:
        print(f"Error in export_item: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/update_item', methods=['POST'])
def update_item():
    try:
        data = request.json
        updated_item = data.get('item')
        
        if not updated_item:
            return jsonify({'error': 'No item data provided'}), 400
        
        session['current_item'] = updated_item
        
        # Re-calculate difficulty if model is loaded
        difficulty = None
        if difficulty_estimator.is_loaded():
            grade_level = session.get('config', {}).get('grade_level', 4)
            item_with_grade = {**updated_item, 'grade': f'Grade{grade_level}'}
            difficulty = difficulty_estimator.estimate_difficulty(item_with_grade)
        
        return jsonify({
            'status': 'success',
            'item': updated_item,
            'difficulty': difficulty
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/save_to_collection', methods=['POST'])
def save_to_collection():
    try:
        # Get item from request body (edited) or fall back to session
        data = request.json
        item_to_save = data.get('item') if data else None
        
        print(f"save_to_collection called")
        print(f"Item from request: {item_to_save is not None}")
        
        if not item_to_save:
            item_to_save = session.get('current_item')
            print(f"Using item from session: {item_to_save is not None}")
        
        if not item_to_save:
            return jsonify({'error': 'No item to save'}), 400
        
        # Update current_item in session with the latest edits
        session['current_item'] = item_to_save
        
        if 'item_collection' not in session:
            session['item_collection'] = []
        
        collection = session['item_collection']
        print(f"Current collection size: {len(collection)}")
        
        # Create a copy to save
        item_copy = item_to_save.copy()
        item_copy['saved_at'] = datetime.now().isoformat()
        item_copy['item_id'] = len(collection) + 1
        
        collection.append(item_copy)
        session['item_collection'] = collection
        
        print(f"After saving, collection size: {len(collection)}")
        print(f"Session modified: {session.modified}")
        
        return jsonify({
            'status': 'success',
            'collection_size': len(collection),
            'item': item_copy
        })
    except Exception as e:
        print(f"Error in save_to_collection: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/get_collection', methods=['GET'])
def get_collection():
    collection = session.get('item_collection', [])
    print(f"get_collection called - found {len(collection)} items")
    print(f"Collection: {collection}")
    return jsonify({
        'items': collection,
        'count': len(collection)
    })


@app.route('/export_collection', methods=['POST'])
def export_collection():
    try:
        collection = session.get('item_collection', [])
        
        if not collection:
            return jsonify({'error': 'No items in collection'}), 400
        
        # Create a temporary file in memory
        from io import StringIO
        import csv
        
        # Convert collection to CSV
        output = StringIO()
        if collection:
            # Get all keys from all items
            keys = set()
            for item in collection:
                keys.update(item.keys())
            
            writer = csv.DictWriter(output, fieldnames=sorted(keys))
            writer.writeheader()
            writer.writerows(collection)
            
            # Get the CSV content
            csv_content = output.getvalue()
            output.close()
            
            # Create response with CSV file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'items_{timestamp}.csv'
            
            from flask import make_response
            response = make_response(csv_content)
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = f'attachment; filename={filename}'
            return response
            
    except Exception as e:
        print(f"Error in export_collection: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/delete_from_collection', methods=['POST'])
def delete_from_collection():
    try:
        data = request.json
        item_id = data.get('item_id')
        
        if 'item_collection' not in session:
            return jsonify({'error': 'No collection found'}), 400
        
        collection = session['item_collection']
        collection = [item for item in collection if item.get('item_id') != item_id]
        session['item_collection'] = collection
        
        return jsonify({
            'status': 'success',
            'collection_size': len(collection)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    import os
    port = int(os.environ.get('FLASK_RUN_PORT', 5001))
    app.run(debug=True, port=port)
