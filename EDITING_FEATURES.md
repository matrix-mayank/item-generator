# Editing and Collection Features Fix

## Issues Fixed

### 1. Editing Fields Not Working
**Problem:** The onclick handlers on editable fields were being escaped by `escapeHtml()`, preventing clicks from working.

**Solution:** 
- Removed inline `onclick` attributes
- Added `data-field` attributes to store the field name
- Added event listeners programmatically after rendering using `querySelectorAll` and `addEventListener`

### 2. Save Button Functionality
**Problem:** User wanted the "Save" button to directly save to collection instead of having two separate buttons.

**Solution:**
- Removed "Save Changes" button
- Changed "Add to Collection" button to "Save to Collection"
- When clicked, it saves the current item (with any edits) to the collection

### 3. Collection Viewing and CSV Export
**Features confirmed working:**
- Click "View Collection" in navbar to see all saved items
- Each item shows its ID and preview
- Can delete individual items with × button
- "Export All to CSV" button downloads all items in collection
- Collection count updates in real-time

## How It Works Now

1. **Generate an item** - Item appears in right panel
2. **Click any field** (Passage, Question, etc.) - It becomes editable with a textarea
3. **Edit the content** - Click outside or press Escape to finish
4. **Change metadata** - Use the dropdown menus to adjust Event-Chain, QAR Level, etc.
5. **Click "Save to Collection"** - Item is added to your collection with all edits
6. **View Collection** - Click navbar button to see modal with all saved items
7. **Export CSV** - Click "Export All to CSV" to download everything

## Technical Implementation

### Event Listeners Setup
```javascript
// After rendering HTML
itemPreview.querySelectorAll('.editable').forEach(el => {
    el.addEventListener('click', function() {
        makeEditable(this, this.dataset.field);
    });
});

itemPreview.querySelectorAll('.metadata-select').forEach(select => {
    select.addEventListener('change', function() {
        updateMetadata(this.dataset.field, this.value);
    });
});
```

### Editable Fields
- Passage
- Question  
- Target Answer
- Distractor 1
- Distractor 2

### Metadata Dropdowns
- Event-Chain Relation
- Knowledge-Base Inference
- QAR Level
- Coherence Level
- Explanatory Stance

All changes are stored in the `currentItem` object and saved when you click "Save to Collection".
