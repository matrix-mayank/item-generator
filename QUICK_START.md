# Quick Start Guide: Reading Comprehension Item Generator

## What Changed?

The ROAR Item Generator has been transformed into a **generic Reading Comprehension Item Generator** with configurable settings based on NY/Texas standardized tests (Grades 3-12).

## New Features

### 1. **Settings Panel (Left Sidebar)**
Configure everything before generating items:
- **Passage Length**: Short (150), Medium (300), or Long (450 words)
- **Questions**: 1-5 questions per passage
- **Distractors**: 2-4 wrong answers per question
- **Grade Level**: Grades 3-12
- **Inference Type**: Text-Explicit, Text-Implicit, Script-Implicit, or All
- **Custom Manual**: Upload your own guidelines (TXT, PDF, DOCX)

### 2. **Multiple Questions per Passage**
Generate passages with multiple questions in standard A/B/C/D format:
```
Question 1: What is the main idea?
A) [Correct answer]
B) [Distractor 1]
C) [Distractor 2]
D) [Distractor 3]
```

### 3. **Custom Guidelines**
Upload assessment manuals or rubrics to customize item generation.

### 4. **Backward Compatible**
Old ROAR format items still work!

## How to Use

### Step 1: Configure Settings
1. Open the app
2. Look at the **left panel** (⚙️ Configuration)
3. Adjust settings to your needs
4. Click **"Apply Settings"**

### Step 2: Generate Items
Chat with the AI:
- "Generate a passage about space exploration"
- "Create a Grade 5 passage with 4 questions"
- "Make a short passage with vocabulary questions"

### Step 3: Review & Edit
- View generated item in the **right panel**
- Click any field to edit
- Difficulty automatically recalculates

### Step 4: Save & Export
- **"Save to Collection"** - Add to your item bank
- **"Export Current"** - Download as CSV
- **"View Collection"** - See all saved items

## Default Settings

Based on analysis of **5,347 NY/Texas test items**:
- ✅ Medium passages (~300 words)
- ✅ 3 questions per passage
- ✅ 3 distractors per question (A/B/C/D format)
- ✅ Grade 4 level
- ✅ Mixed inference types

## File Structure

```
New Files:
├── config.py                   ✨ Configuration management
├── prompt_builder.py           ✨ Dynamic prompt generation
├── file_handler.py            ✨ File upload handling
├── test_config.py             ✨ Test suite
├── README_NEW.md              ✨ Full documentation
└── IMPLEMENTATION_SUMMARY.md  ✨ Technical details

Modified Files:
├── app.py                     🔧 Added config endpoints
├── templates/index.html       🔧 Added settings panel
└── requirements.txt           🔧 Added PDF/DOCX support
```

## Quick Test

Run the test suite to verify everything works:

```bash
cd app
python test_config.py
```

Should see:
```
✅ All modules imported successfully
✅ Default config loaded
✅ Config validation works
✅ Config merged successfully
✅ Prompt built successfully
✅ File validation works
✅ All tests passed!
```

## Example Prompts

### Basic
- "Generate a passage about dinosaurs"
- "Create an item about the solar system"

### Specific Grade
- "Make a Grade 3 passage about animals"
- "Generate a Grade 8 passage about World War 2"

### Custom Length
- "Create a short passage with 2 questions"
- "Make a long passage about climate change"

### Question Types
- "Generate a passage with vocabulary questions"
- "Create an item with inference questions"
- "Make a passage with text-explicit questions"

## What's Different from ROAR?

| Feature | ROAR | New Version |
|---------|------|-------------|
| **Passages** | 3-5 sentences | 150-450 words |
| **Questions** | 1 question | 1-5 questions |
| **Format** | ROAR-specific | Generic standardized test |
| **Configurable** | No | Yes (all settings) |
| **Grade Levels** | 2-5 | 3-12 |
| **Custom Guidelines** | No | Yes (upload files) |
| **Standards** | ROAR framework | NY/TX standardized tests |

## Need Help?

1. **Full Documentation**: See `README_NEW.md`
2. **Technical Details**: See `IMPLEMENTATION_SUMMARY.md`
3. **Test the System**: Run `python test_config.py`

## Next Steps

1. ✅ **Configure Settings** - Adjust the left panel
2. ✅ **Generate Items** - Chat with AI
3. ✅ **Build Collection** - Save multiple items
4. ✅ **Export** - Download as CSV
5. ✅ **(Optional) Upload Manual** - Add custom guidelines

## Tips

- 💡 Apply settings before generating items
- 💡 Start with default settings, then customize
- 💡 Edit any field by clicking on it
- 💡 Save items before clearing session
- 💡 Upload manuals for specialized assessments

---

**Ready to start?** Open the app and configure your settings!
