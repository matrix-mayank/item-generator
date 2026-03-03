import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from anthropic import Anthropic
from dotenv import load_dotenv
import pandas as pd
from difficulty_estimator import DifficultyEstimator

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
difficulty_estimator = DifficultyEstimator(os.getenv('MODEL_PATH'))

ROAR_PROMPT = """You are an expert educational content designer creating reading comprehension items for the ROAR-Inference assessment. Generate ONE complete item per request following all rules below.

---

## ITEM STRUCTURE

Create items with:
- **Passage:** 3-5 sentences, age-appropriate (grades 2-5)
- **Question:** Targets one inference type
- **Target Answer:** Full coherence (Level 2)
- **Distractor 1:** Partial coherence (Level 1) - uses passage info incorrectly
- **Distractor 2:** Minimal coherence (Level 0) - outside text, world knowledge only

---

## CORE FRAMEWORKS (Choose one from each)

### 1. EVENT-CHAIN RELATION
- **Logical:** Why/how questions (causes, motivations, enabling conditions)
- **Informational:** Who/what/when/where questions (referential/spatiotemporal tracking)
- **Evaluative:** Themes, lessons, significance (global interpretation only)

### 2. KNOWLEDGE-BASE INFERENCE
- **Superordinate goal:** Purpose, intent, future goals (teleological)
- **Causal-antecedent:** Prior causes, mechanisms (mechanistic)
- **State:** Emotions, traits, beliefs explaining behavior (mechanistic)
- **Referential:** Pronoun resolution, textual connections
- **Thematic:** Moral/lesson (evaluative)

### 3. QAR LEVEL
**Text-Explicit:**
- Answer verbatim/near-verbatim in passage
- Grammatical link between question and answer
- Use exact passage wording

**Text-Implicit:**
- Combine adjacent passage details
- NO grammatical link
- Local coherence only
- Must use passage vocabulary (no synonyms/elevated terms)

**Script-Implicit:**
- Requires world knowledge + passage
- NO grammatical link
- Global coherence
- May use terms not in passage

### 4. COHERENCE LEVEL
- **Local:** Adjacent sentences, working memory span
- **Global:** Distant text parts + world knowledge integration

**Mapping:** Text-Explicit/Implicit → Local | Script-Implicit → Global

---

## CRITICAL CONSTRAINTS

### Vocabulary Matching (Text-Explicit/Implicit ONLY)
✅ **MUST** use exact passage wording
❌ **NEVER** replace with synonyms or higher-level terms

**Violations:**
- "thin air" → "high elevation" ❌
- "butterfly emerge" → "metamorphosis" ❌
- "land was scarce" → "limited land" ❌

### Target Answer Rules
**DO NOT ADD:**
- Teleological additions not in text ("safely", "to be safe")
- Emotions not stated ("scared", "fearful")
- Purposes not indicated
- Higher-level vocabulary (for Text-Explicit/Implicit)

**Coherence Quality (Breadth + Simplicity):**
- **Breadth:** Target should connect/explain multiple story elements, not just one detail
- **Simplicity:** Target should require minimal additional assumptions beyond the passage
- Best answers integrate multiple pieces of evidence while remaining straightforward

---

## DISTRACTOR CONSTRUCTION

**Psychometric Ordering Requirement:**
Distractors must follow attractiveness hierarchy:
- **D1 (Partial Coherence):** Should attract mid-ability students who engage with text but miss full inference
- **D2 (Minimal Coherence):** Should attract low-ability students who rely on world knowledge without text integration
- D1 must be MORE plausible than D2 to create proper difficulty ordering

### Distractor 1 (Partial Coherence)
**Pattern:** Text-based misconnection
- References details FROM passage
- Connects them incorrectly to question
- Shows partial text engagement
- Lacks full explanatory integration
- **Attractiveness:** Plausible enough to tempt students who read the passage but don't make full inference

### Distractor 2 (Minimal Coherence)
**Pattern:** Over-reliance on world knowledge
- Based on question/general knowledge only
- Ignores passage content
- Plausible generally, not for this story
- Represents reading question without passage
- **Attractiveness:** Less plausible than D1; attracts students who don't engage with passage

---

## OUTPUT FORMAT

```
Passage: [3-5 sentences]

Question: [Your question]

Target Answer: [Full coherence]

Distractor 1 (Partial Coherence): [Text-based misconnection]

Distractor 2 (Minimal Coherence): [World knowledge only]

---
METADATA:
Event-Chain Relation: [Logical/Informational/Evaluative]
Knowledge-Base Inference: [Superordinate Goal/Causal-Antecedent/State/Referential/Thematic]
QAR Level: [Text-Explicit/Text-Implicit/Script-Implicit]
Coherence Level: [Local/Global]
Explanatory Stance: [Teleological/Mechanistic/N/A]
---
```

---

## KEY PRINCIPLES

1. **Vocabulary matching mandatory** for Text-Explicit/Implicit (no synonyms/elevated terms)
2. **Never add to story** (no unstated safety/emotions/purposes)
3. **Clear distractor hierarchy** (D1=partial text, D2=world knowledge only)
4. **Attractiveness ordering** (Target > D1 > D2 in plausibility for different ability levels)
5. **Coherence quality** (Target shows breadth across story elements + simplicity in assumptions)
6. **No redundancy** (distractors must be qualitatively different)
7. **Plausible distractors** (wrong due to coherence, not impossibility)
8. **QAR consistency** (question-answer-passage relationship must match chosen level)

---

Generate items that provide diagnostic information about students' inferential reasoning and coherence evaluation processes.
"""

SYSTEM_MESSAGE = """You are an expert educational content designer assistant helping create ROAR reading comprehension items. 

When a user asks you to create or revise an item, you should:
1. Generate or revise the item following all the guidelines in your instructions
2. Engage in conversation about the item, accepting feedback and making revisions
3. Always output items in the structured format when generating/revising
4. Be conversational and helpful, explaining your design choices when asked

Remember:
- You can revise items based on user feedback
- You can explain why you made certain choices
- Be flexible and creative within the constraints"""


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
    """Parse Claude's response into structured item"""
    text = response_text.strip()
    
    # Remove all markdown formatting
    text_clean = text.replace('**', '')
    
    print("PARSING RESPONSE - First 800 chars (cleaned):")
    print(text_clean[:800])
    print("=" * 50)
    
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
    
    # Extract passage (can be multi-line)
    passage_match = text_clean.find('Passage:')
    if passage_match != -1:
        passage_start = passage_match + len('Passage:')
        passage_end = text_clean.find('\n\nQuestion:', passage_start)
        if passage_end == -1:
            passage_end = text_clean.find('\nQuestion:', passage_start)
        if passage_end != -1:
            item['passage'] = text_clean[passage_start:passage_end].strip()
    
    # Extract question
    question_match = text_clean.find('Question:')
    if question_match != -1:
        question_start = question_match + len('Question:')
        question_end = text_clean.find('\n\nTarget Answer:', question_start)
        if question_end == -1:
            question_end = text_clean.find('\nTarget Answer:', question_start)
        if question_end != -1:
            item['question'] = text_clean[question_start:question_end].strip()
    
    # Extract target answer
    target_match = text_clean.find('Target Answer:')
    if target_match != -1:
        target_start = target_match + len('Target Answer:')
        target_end = text_clean.find('\nDistractor 1', target_start)
        if target_end == -1:
            target_end = text_clean.find('\n\nDistractor 1', target_start)
        if target_end != -1:
            item['target_answer'] = text_clean[target_start:target_end].strip()
    
    # Extract Distractor 1
    d1_match = text_clean.find('Distractor 1')
    if d1_match != -1:
        d1_start = text_clean.find(':', d1_match) + 1
        d1_end = text_clean.find('\nDistractor 2', d1_match)
        if d1_end == -1:
            d1_end = text_clean.find('\n\nDistractor 2', d1_match)
        if d1_end != -1:
            content = text_clean[d1_start:d1_end].strip()
            # Remove anything in parentheses like "(Partial Coherence)"
            paren_pos = content.find('(')
            if paren_pos > 0:
                content = content[:paren_pos].strip()
            item['distractor_1'] = content
    
    # Extract Distractor 2
    d2_match = text_clean.find('Distractor 2')
    if d2_match != -1:
        d2_start = text_clean.find(':', d2_match) + 1
        # Look for end markers - stop before metadata/separator
        d2_end = text_clean.find('\nMETADATA:', d2_match)
        if d2_end == -1:
            d2_end = text_clean.find('\n\n---', d2_match)
        if d2_end == -1:
            d2_end = text_clean.find('\n---', d2_match)
        if d2_end == -1:
            # Try to find next double newline
            d2_end = text_clean.find('\n\n', d2_start)
        
        if d2_end != -1:
            content = text_clean[d2_start:d2_end].strip()
            # Remove anything in parentheses
            paren_pos = content.find('(')
            if paren_pos > 0:
                content = content[:paren_pos].strip()
            # Take only first line if multiple lines exist
            if '\n' in content:
                content = content.split('\n')[0].strip()
            # Remove any remaining dashes
            content = content.replace('---', '').strip()
            item['distractor_2'] = content
    
    # Parse metadata section
    metadata_start = text_clean.find('METADATA:')
    if metadata_start != -1:
        metadata_section = text_clean[metadata_start:]
        
        # Extract each metadata field
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
    
    print(f"Parsed passage length: {len(item['passage'])}")
    print(f"Parsed question length: {len(item['question'])}")
    print(f"Parsed target_answer length: {len(item['target_answer'])}")
    print(f"Parsed distractor_1 length: {len(item['distractor_1'])}")
    print(f"Parsed distractor_2 length: {len(item['distractor_2'])}")
    print(f"Distractor 2 content: '{item['distractor_2']}'")
    
    return item


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/chat', methods=['POST'])
def chat():
    print("=" * 50)
    print("CHAT ENDPOINT CALLED")
    print("=" * 50)
    try:
        data = request.json
        user_message = data.get('message', '')
        print(f"User message: {user_message}")
        
        if 'conversation_history' not in session:
            session['conversation_history'] = []
        
        conversation_history = session['conversation_history']
        
        conversation_history.append({
            'role': 'user',
            'content': user_message
        })
        
        messages = [{'role': msg['role'], 'content': msg['content']} 
                   for msg in conversation_history]
        
        # Use streaming for faster responses
        with client.messages.stream(
            model='claude-haiku-4-5-20251001',
            max_tokens=4000,
            temperature=1,
            system=SYSTEM_MESSAGE + "\n\n" + ROAR_PROMPT,
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
                    difficulty = difficulty_estimator.estimate_difficulty(parsed_item)
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
            'message': assistant_message,
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
        difficulty = difficulty_estimator.estimate_difficulty(current_item)
    
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
            difficulty = difficulty_estimator.estimate_difficulty(updated_item)
        
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
            filename = f'roar_items_collection_{timestamp}.csv'
            
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
