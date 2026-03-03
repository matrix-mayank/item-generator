# Metadata Dropdown Enhancement

## Changes Made

### 1. Added Dropdown Styling
Added CSS for `.metadata-select` to style the dropdown fields:
- Clean, minimal design matching the overall UI
- Hover and focus states for better interactivity
- Full-width dropdowns that fit naturally in the metadata grid

### 2. Converted Metadata to Dropdowns
Replaced static text displays with `<select>` elements for all metadata fields:

**Event-Chain Relation:**
- Informational
- Causal
- Motivational
- Intentional

**Knowledge-Base Inference:**
- Referential
- Elaborative

**QAR Level:**
- Text-Explicit
- Text-Implicit
- Script-Implicit

**Coherence Level:**
- Local
- Global

**Explanatory Stance:**
- N/A
- Physical
- Psychological
- Social

### 3. Auto-Population
Each dropdown is pre-selected with the value from the generated item using the `selected` attribute based on the current item's metadata values.

### 4. Real-Time Updates
Added `updateMetadata(field, value)` function that:
- Updates the `currentItem` object when a dropdown value changes
- Logs the change to console for debugging
- Ensures changes are preserved when "Save Changes" is clicked

## How It Works

1. **Initial Load:** When an item is generated, the metadata fields are pre-populated with Claude's selections
2. **User Override:** User can click any dropdown to change the value to any valid option
3. **Persistence:** Changes are stored in the `currentItem` object
4. **Saving:** When "Save Changes" is clicked, all metadata (including dropdown changes) are sent to the backend and difficulty is re-estimated

## Testing

Try these workflows:
1. Generate an item and observe the pre-populated metadata dropdowns
2. Change any metadata field (e.g., QAR Level from "Text-Explicit" to "Script-Implicit")
3. Click "Save Changes" to persist the updates
4. Add the item to collection to verify the modified metadata is saved
