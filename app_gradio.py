import gradio as gr
import os
from anthropic import Anthropic
from difficulty_estimator import DifficultyEstimator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Anthropic client
client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# Initialize difficulty estimator
MODEL_PATH = os.getenv('MODEL_PATH', './models')
difficulty_estimator = DifficultyEstimator(MODEL_PATH)

# Load ROAR prompt
with open('prompts/roar_prompt.md', 'r') as f:
    ROAR_PROMPT = f.read()

SYSTEM_MESSAGE = """You are an expert educational assessment designer specializing in creating reading comprehension items. 
Generate high-quality assessment items following the exact format provided."""

# Store conversation history and current item
conversation_state = {"history": [], "current_item": None, "collection": []}


def parse_item_from_response(text):
    """Parse item from Claude's response"""
    # Remove markdown bold formatting
    text = text.replace('**', '')
    
    item = {}
    
    # Define field markers and their end markers
    fields = {
        'passage': 'Question:',
        'question': 'Target Answer:',
        'target_answer': 'Distractor 1:',
        'distractor_1': 'Distractor 2:',
        'distractor_2': 'Distractor 3:',
        'distractor_3': 'Metadata:',
    }
    
    # Parse each field
    for field, end_marker in fields.items():
        # Find the field label
        field_label = field.replace('_', ' ').title().replace('Distractor', 'Distractor')
        if field == 'passage':
            field_label = 'Passage:'
        elif field == 'question':
            field_label = 'Question:'
        elif field == 'target_answer':
            field_label = 'Target Answer:'
        elif field.startswith('distractor'):
            num = field.split('_')[1]
            field_label = f'Distractor {num}:'
        
        start_pos = text.find(field_label)
        if start_pos == -1:
            continue
            
        start_pos += len(field_label)
        end_pos = text.find(end_marker, start_pos) if end_marker else len(text)
        
        if end_pos == -1:
            end_pos = len(text)
        
        content = text[start_pos:end_pos].strip()
        
        # For distractors, clean up extra formatting
        if field.startswith('distractor'):
            # Remove parenthetical notes
            if '(' in content:
                paren_pos = content.find('(')
                content = content[:paren_pos].strip()
            # Take only first line
            if '\n' in content:
                content = content.split('\n')[0].strip()
            # Remove dashes
            content = content.replace('---', '').strip()
        
        item[field] = content
    
    # Parse metadata
    metadata_section = text[text.find('Metadata:'):] if 'Metadata:' in text else ''
    
    metadata_fields = {
        'event_chain_relation': 'Event-Chain Relation:',
        'knowledge_base_inference': 'Knowledge-Base Inference:',
        'qar_level': 'QAR Level:',
        'coherence_level': 'Coherence Level:',
        'explanatory_stance': 'Explanatory Stance:'
    }
    
    for field, label in metadata_fields.items():
        if label in metadata_section:
            start = metadata_section.find(label) + len(label)
            end = metadata_section.find('\n', start)
            if end == -1:
                end = len(metadata_section)
            value = metadata_section[start:end].strip()
            # Clean up value
            if '(' in value:
                value = value[:value.find('(')].strip()
            item[field] = value
    
    return item


def chat_with_ai(user_message, history):
    """Handle chat with Claude and generate items"""
    if not user_message:
        return history, None, None
    
    # Add user message to history
    conversation_state["history"].append({
        'role': 'user',
        'content': user_message
    })
    
    # Get response from Claude
    messages = [{'role': msg['role'], 'content': msg['content']} 
                for msg in conversation_state["history"]]
    
    with client.messages.stream(
        model='claude-sonnet-4-20250514',
        max_tokens=4000,
        temperature=1,
        system=SYSTEM_MESSAGE + "\n\n" + ROAR_PROMPT,
        messages=messages
    ) as stream:
        assistant_message = ""
        for text in stream.text_stream:
            assistant_message += text
    
    conversation_state["history"].append({
        'role': 'assistant',
        'content': assistant_message
    })
    
    # Parse item from response
    item = None
    difficulty = None
    try:
        item = parse_item_from_response(assistant_message)
        if item and (item.get('passage') or item.get('question')):
            conversation_state["current_item"] = item
            if difficulty_estimator.is_loaded():
                difficulty = difficulty_estimator.estimate_difficulty(item)
    except Exception as e:
        print(f"Error parsing item: {e}")
    
    # Update chat history for display
    history.append((user_message, assistant_message))
    
    # Format item display
    item_display = format_item_display(item, difficulty) if item else "No item generated yet"
    
    return history, item_display, item


def format_item_display(item, difficulty=None):
    """Format item for display"""
    if not item:
        return "No item to display"
    
    display = "# Current Item\n\n"
    
    # Add difficulty if available
    if difficulty:
        score = difficulty['score']
        irt_score = difficulty.get('irt_difficulty', 'N/A')
        label = difficulty.get('interpretation', 'Medium')
        display += f"**Estimated Difficulty:** {label}\n"
        display += f"- Normalized: {score*100:.1f}%\n"
        display += f"- IRT Score: {irt_score:.3f if isinstance(irt_score, float) else irt_score}\n\n"
    
    # Add item fields
    display += f"**Passage:**\n{item.get('passage', 'N/A')}\n\n"
    display += f"**Question:**\n{item.get('question', 'N/A')}\n\n"
    display += f"**Target Answer:**\n{item.get('target_answer', 'N/A')}\n\n"
    display += f"**Distractor 1:**\n{item.get('distractor_1', 'N/A')}\n\n"
    display += f"**Distractor 2:**\n{item.get('distractor_2', 'N/A')}\n\n"
    display += f"**Distractor 3:**\n{item.get('distractor_3', 'N/A')}\n\n"
    
    # Add metadata
    display += "---\n**Metadata:**\n"
    display += f"- Event-Chain Relation: {item.get('event_chain_relation', 'N/A')}\n"
    display += f"- Knowledge-Base Inference: {item.get('knowledge_base_inference', 'N/A')}\n"
    display += f"- QAR Level: {item.get('qar_level', 'N/A')}\n"
    display += f"- Coherence Level: {item.get('coherence_level', 'N/A')}\n"
    display += f"- Explanatory Stance: {item.get('explanatory_stance', 'N/A')}\n"
    
    return display


def save_to_collection(item_data):
    """Save current item to collection"""
    if not conversation_state["current_item"]:
        return "No item to save", format_collection_display()
    
    # Add to collection
    item_copy = conversation_state["current_item"].copy()
    item_copy['item_id'] = len(conversation_state["collection"]) + 1
    
    # Add difficulty if available
    if difficulty_estimator.is_loaded():
        difficulty = difficulty_estimator.estimate_difficulty(item_copy)
        if difficulty:
            item_copy['difficulty_score'] = difficulty['score']
            item_copy['difficulty_irt'] = difficulty.get('irt_difficulty')
            item_copy['difficulty_label'] = difficulty.get('interpretation')
    
    conversation_state["collection"].append(item_copy)
    
    return f"✅ Item saved! ({len(conversation_state['collection'])} items total)", format_collection_display()


def format_collection_display():
    """Format collection for display"""
    if not conversation_state["collection"]:
        return "No items in collection yet"
    
    display = f"# Collection ({len(conversation_state['collection'])} items)\n\n"
    
    for item in conversation_state["collection"]:
        display += f"## Item #{item['item_id']}\n"
        if 'difficulty_label' in item:
            display += f"**Difficulty:** {item['difficulty_label']} "
            display += f"({item.get('difficulty_score', 0)*100:.1f}%)\n"
        display += f"**Question:** {item.get('question', 'N/A')[:100]}...\n\n"
    
    return display


def export_collection():
    """Export collection as CSV"""
    if not conversation_state["collection"]:
        return None
    
    import pandas as pd
    import io
    from datetime import datetime
    
    df = pd.DataFrame(conversation_state["collection"])
    
    # Save to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'roar_items_{timestamp}.csv'
    df.to_csv(filename, index=False)
    
    return filename


def clear_chat():
    """Clear chat history"""
    conversation_state["history"] = []
    conversation_state["current_item"] = None
    return [], "No item generated yet"


# Create Gradio interface
with gr.Blocks(title="ROAR Item Generator", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🦁 ROAR Assessment Item Generator")
    gr.Markdown("Generate reading comprehension items with AI guidance and difficulty estimation")
    
    with gr.Row():
        with gr.Column(scale=2):
            chatbot = gr.Chatbot(label="Chat", height=500)
            msg = gr.Textbox(
                label="Your message",
                placeholder="Try: Generate a reading comprehension item about ocean animals",
                lines=2
            )
            with gr.Row():
                send_btn = gr.Button("Send", variant="primary")
                clear_btn = gr.Button("Clear Chat")
        
        with gr.Column(scale=1):
            item_display = gr.Markdown("No item generated yet", label="Current Item")
            save_btn = gr.Button("💾 Save to Collection", variant="secondary")
            save_status = gr.Textbox(label="Status", lines=1, interactive=False)
    
    gr.Markdown("---")
    
    with gr.Accordion("📚 Collection", open=False):
        collection_display = gr.Markdown("No items in collection yet")
        export_btn = gr.Button("📥 Export Collection as CSV")
        export_file = gr.File(label="Download CSV")
    
    # Hidden state to pass item data
    item_state = gr.State(None)
    
    # Event handlers
    msg.submit(chat_with_ai, [msg, chatbot], [chatbot, item_display, item_state]).then(
        lambda: "", None, msg
    )
    send_btn.click(chat_with_ai, [msg, chatbot], [chatbot, item_display, item_state]).then(
        lambda: "", None, msg
    )
    clear_btn.click(clear_chat, None, [chatbot, item_display])
    save_btn.click(save_to_collection, item_state, [save_status, collection_display])
    export_btn.click(export_collection, None, export_file)

if __name__ == "__main__":
    demo.launch()
