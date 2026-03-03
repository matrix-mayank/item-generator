# Item Generator Chatbot

An interactive chatbot application for creating and revising educational assessment items with real-time difficulty estimation.

## Features

- 🤖 **AI-Powered Item Generation** - Uses Anthropic's Claude API to generate educational items
- 💬 **Conversational Interface** - Chat with the AI to create and refine items iteratively
- 📊 **Difficulty Estimation** - Automatically estimates item difficulty using your trained model
- 🎨 **Modern Minimal UI** - Clean, professional interface with monochromatic design
- 📝 **Item Preview** - Real-time preview of generated items with metadata
- 💾 **Export Functionality** - Save items as CSV files
- 🔧 **Flexible Prompts** - Generic system that works with any assessment type

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
FLASK_SECRET_KEY=your_secret_key_here
MODEL_PATH=path_to_your_trained_model.pkl
```

**Note:** The `MODEL_PATH` is optional. If you don't have a trained difficulty estimation model yet, the app will still work - it just won't show difficulty predictions.

### 3. Run the Application

```bash
python app.py
```

The application will start on `http://localhost:5000`

## Usage

### Creating Items

Simply chat with the AI assistant to create items:

- "Create a 6th grade reading comprehension item"
- "Generate a math word problem for grade 3"
- "Make a science question about photosynthesis"
- "Create an item about space exploration"

### Revising Items

You can iteratively refine items through conversation:

- "Make the passage simpler"
- "Change the question to be more challenging"
- "Make the incorrect answer less obvious"
- "Rewrite this for younger students"

### Using Specialized Prompts

The app comes with specialized prompts saved in the `prompts/` folder:
- `roar_prompt.md` - For ROAR reading comprehension items

You can add these prompts to your conversation by pasting them in or by modifying the code to load them automatically.

### Exporting Items

Click the "Export Item" button to save the current item as a CSV file with timestamp.

## Project Structure

```
app/
├── app.py                      # Main Flask application
├── difficulty_estimator.py     # Difficulty estimation module
├── templates/
│   └── index.html             # Web interface
├── prompts/
│   └── roar_prompt.md         # ROAR-specific prompt template
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (create this)
├── .env.example              # Example environment file
└── README.md                 # This file
```

## Difficulty Estimation

The app includes a flexible difficulty estimation system. To use it:

1. Train your difficulty prediction model using your preferred ML framework
2. Save the model using `joblib.dump(model, 'model.pkl')`
3. Set the `MODEL_PATH` in your `.env` file
4. Update the `extract_features()` method in `difficulty_estimator.py` to match your model's feature requirements

If no model is provided, the app will still function normally - it just won't display difficulty predictions.

## Technical Details

- **Backend:** Flask (Python web framework)
- **AI Model:** Claude 3.7 Sonnet (Anthropic API)
- **Frontend:** Vanilla JavaScript, HTML5, CSS3
- **Session Management:** Flask sessions for conversation history
- **Data Format:** Structured JSON for items, CSV for export

## Features Breakdown

### Conversation History
- Maintains context across multiple messages
- Allows iterative refinement of items
- Session-based storage (clears on "Clear Session")

### Item Parsing
- Automatically detects when an item is generated
- Extracts structured data (passage, question, answers, metadata)
- Updates preview in real-time

### Validation
- Follows ROAR framework guidelines
- Ensures proper distractor hierarchy
- Validates metadata completeness

## Customization

### Modifying Generation Rules

Edit the `GENERATION_PROMPT_TEMPLATE` in `app.py` to customize:
- Item structure requirements
- Framework definitions
- Validation rules
- Examples

### Adjusting AI Behavior

Modify the `SYSTEM_MESSAGE` in `app.py` to change:
- Assistant personality
- Response style
- Conversation flow

### Feature Engineering

Update `extract_features()` in `difficulty_estimator.py` to:
- Add new features for difficulty prediction
- Change feature encodings
- Adjust feature extraction logic

## Troubleshooting

### API Key Issues
- Ensure your Anthropic API key is valid
- Check that the key is properly set in `.env`
- Verify you have API credits available

### Model Loading Errors
- Check that your model file exists at the specified path
- Ensure the model was saved with joblib
- Verify model compatibility with current scikit-learn version

### Session Issues
- Clear browser cookies if sessions behave unexpectedly
- Restart the Flask server to reset all sessions

## Future Enhancements

Possible improvements:
- Database storage for conversation history
- Multi-user support
- Batch item generation
- Advanced difficulty prediction models
- Item validation scoring
- Export to multiple formats (JSON, Excel)
- Item comparison and analysis tools

## License

This project is for educational purposes.
