# Reading Comprehension Item Generator

A web-based application for generating standardized reading comprehension test items with configurable settings and AI-powered difficulty estimation.

## Overview

This application generates reading comprehension items modeled after New York and Texas standardized assessments (Grades 3-12). It uses Claude AI to generate items and ModernBERT for difficulty estimation.

### Key Features

- **Configurable Settings**: Customize passage length, number of questions, distractors, grade level, and inference types
- **Custom Guidelines**: Upload your own assessment manuals/rubrics (TXT, PDF, DOCX)
- **AI-Powered Generation**: Uses Claude Haiku 4.5 for fast, high-quality item generation
- **Difficulty Estimation**: ModernBERT-based IRT difficulty scoring
- **Item Collection**: Save, export, and manage multiple items
- **Real-time Editing**: Edit any field and automatically recalculate difficulty
- **Session Management**: Maintains conversation context for iterative refinement

## Project Structure

```
app/
├── app.py                      # Main Flask application
├── config.py                   # Configuration management
├── prompt_builder.py           # Dynamic prompt generation
├── file_handler.py             # File upload handling
├── difficulty_estimator.py     # Difficulty estimation (ModernBERT)
├── templates/
│   └── index.html             # Main UI with settings panel
├── uploads/                    # Uploaded manuals storage
├── requirements.txt            # Python dependencies
└── .env                       # Environment variables
```

## Configuration Options

### Passage Settings
- **Length**: Short (~150 words), Medium (~300 words), Long (~450 words)
- **Grade Level**: Grades 3-12
- **Word Count**: Automatically calculated based on length preset

### Question Settings
- **Questions per Passage**: 1-5 questions
- **Distractors per Question**: 2-4 wrong answer choices
- **Inference Type**:
  - All (Mixed): Combination of all types
  - Text-Explicit: Answers directly stated in passage
  - Text-Implicit: Combine adjacent passage details
  - Script-Implicit: Requires world knowledge + passage

### Standards
- **Default**: NY/Texas Grade 3-4 format
- Based on 5,347 authentic test items from NY/Texas assessments

### Custom Guidelines
- Upload assessment manuals or rubrics (TXT, PDF, DOCX)
- Guidelines are incorporated into AI prompts
- Max file size: 5MB

## Installation

1. **Clone/Download the repository**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   Create a `.env` file with:
   ```
   ANTHROPIC_API_KEY=your_api_key_here
   FLASK_SECRET_KEY=your_secret_key_here
   MODEL_PATH=path/to/difficulty/model
   FLASK_RUN_PORT=5001
   ```

4. **Download difficulty model** (optional):
   - Place ModernBERT difficulty model files in a directory
   - Set `MODEL_PATH` in `.env`
   - Required files: `ridge_model.pkl`, `pca.pkl`, `scaler_emb.pkl`, `scaler_features.pkl`, `grade_columns.pkl`

## Usage

### Start the Application

```bash
python app.py
```

Navigate to `http://localhost:5001` in your browser.

### Configure Settings (Left Panel)

1. Set passage length (short/medium/long)
2. Choose number of questions (1-5)
3. Set distractors per question (2-4)
4. Select grade level (3-12)
5. Choose inference type
6. Optional: Upload custom guidelines
7. Click "Apply Settings"

### Generate Items

1. Type your request in the chat, e.g.:
   - "Generate a passage about space exploration with 3 questions"
   - "Create a Grade 5 passage about climate change"
   - "Make a short passage with vocabulary questions"

2. Review the generated item in the right panel

3. Edit any field by clicking on it

4. Save to collection or export as CSV

### Manage Collection

- **View Collection**: See all saved items
- **Export Collection**: Download all items as CSV
- **Delete Items**: Remove items from collection
- **Clear Session**: Reset conversation and current item

## Item Format

### New Generic Format (Default)

```
Passage: [~300 word passage divided into paragraphs]

---

Question 1: [Question text]

A) [Correct answer]
B) [Distractor 1]
C) [Distractor 2]
D) [Distractor 3]

Type: vocabulary

---

Question 2: [Question text]

A) [Correct answer]
B) [Distractor 1]
C) [Distractor 2]
D) [Distractor 3]

Type: comprehension

---

[Additional questions...]

---
METADATA:
Passage Word Count: 298
Grade Level: 4
Flesch-Kincaid Grade Level: 7.2
Standards: NY, TX
```

### Legacy ROAR Format (Still Supported)

The app still supports the original ROAR-Inference format for backward compatibility.

## Difficulty Estimation

The app uses a ModernBERT-based model trained on IRT parameters to estimate item difficulty:

- **Normalized Score**: 0-1 scale (0 = very easy, 1 = very hard)
- **IRT Difficulty**: Raw IRT score (typically -3 to +3)
- **Interpretation**: Easy/Medium/Hard label

Difficulty is automatically calculated when:
- A new item is generated
- An existing item is edited
- An item is saved to collection

## API Endpoints

### Configuration
- `GET /get_config` - Get current configuration
- `POST /update_config` - Update configuration settings
- `POST /upload_manual` - Upload custom guidelines
- `POST /clear_manual` - Clear uploaded manual

### Item Generation
- `POST /chat` - Generate/revise items via chat
- `GET /get_current_item` - Get current item with difficulty
- `POST /update_item` - Update item and recalculate difficulty

### Collection Management
- `POST /save_to_collection` - Add item to collection
- `GET /get_collection` - Get all saved items
- `POST /delete_from_collection` - Remove item
- `POST /export_collection` - Export collection as CSV
- `POST /export_item` - Export current item as CSV

### Session
- `POST /clear` - Clear session data

## Example Prompts

### Basic Generation
- "Generate a passage about ocean animals"
- "Create a reading comprehension item about ancient Egypt"
- "Make a passage with 3 questions about space exploration"

### Specific Requirements
- "Generate a short passage for Grade 3 with vocabulary questions"
- "Create a long passage about the water cycle with text-implicit questions"
- "Make a Grade 8 passage about World War 2 with 5 questions"

### Iterative Refinement
- "Make the passage shorter"
- "Add more challenging vocabulary"
- "Revise the second question to be clearer"
- "Make the distractors more plausible"

## Deployment

### Railway (Recommended)

1. Create new Railway project
2. Connect GitHub repository
3. Set environment variables:
   - `ANTHROPIC_API_KEY`
   - `FLASK_SECRET_KEY`
   - `MODEL_PATH` (if using difficulty estimation)
4. Railway will automatically detect and deploy the Flask app

### Other Platforms

The app is compatible with any platform that supports Python/Flask:
- Heroku
- Google Cloud Run
- AWS Elastic Beanstalk
- Azure App Service

## Data Source

The default configuration is based on analysis of 5,347 authentic reading comprehension items from:
- New York State ELA assessments (Grades 3-8)
- Texas STAAR assessments (Grades 3-8)

Sample characteristics:
- Passage Length: ~450 words (8 paragraphs) for Grade 4
- Question Types: Vocabulary, comprehension, inference
- Answer Format: 1 correct + 3 distractors
- Flesch-Kincaid: ~7.6 (Grade 7-8 reading level)

## Technical Stack

- **Backend**: Flask (Python)
- **AI Model**: Claude Haiku 4.5 (Anthropic)
- **Difficulty Model**: ModernBERT-base + Ridge Regression
- **Frontend**: Vanilla JavaScript + CSS
- **Data Processing**: Pandas, NumPy, scikit-learn
- **Deep Learning**: PyTorch, Transformers

## Performance

- **Item Generation**: 8-13 seconds (with Claude Haiku + ModernBERT on CPU)
- **Difficulty Estimation**: ~2-3 seconds (ModernBERT on CPU)
- **File Upload**: Instant (< 1 second for typical manuals)

## Limitations

- AI-generated items should be reviewed by educational experts
- Difficulty estimation is based on Grade 3-8 data
- Custom manuals must be in text-extractable format (no scanned images)
- Session data is stored in cookies (cleared on browser close)

## Future Enhancements

Potential improvements from the plan:
- Multi-language support
- Advanced metadata tagging
- Item bank management
- Collaborative editing
- Integration with LMS platforms
- Automated item review workflows

## Testing

Run the configuration test suite:

```bash
python test_config.py
```

This validates:
- Module imports
- Configuration validation
- Config merging
- Prompt generation
- File handling

## License

[Your license here]

## Contact

[Your contact information]

## Acknowledgments

- Based on authentic NY/Texas standardized assessment items
- Built with Claude AI (Anthropic)
- Difficulty estimation using ModernBERT (Answer.AI)
