# New JavaScript Functions for Item Editing and Collection

Add these JavaScript functions to handle editing, saving, and collection management:

```javascript
function updateItemPreview(item, difficulty) {
    currentItem = item;
    
    let difficultyHTML = '';
    if (difficulty && difficulty.score !== undefined) {
        const score = difficulty.score;
        let difficultyClass = 'difficulty-medium';
        let difficultyLabel = 'Medium';
        
        if (score < 0.4) {
            difficultyClass = 'difficulty-easy';
            difficultyLabel = 'Easy';
        } else if (score > 0.7) {
            difficultyClass = 'difficulty-hard';
            difficultyLabel = 'Hard';
        }
        
        difficultyHTML = `
            <div class="item-field">
                <div class="item-field-label">Estimated Difficulty</div>
                <div class="item-field-content">
                    <span class="difficulty-badge ${difficultyClass}">
                        ${difficultyLabel} (${(score * 100).toFixed(1)}%)
                    </span>
                </div>
            </div>
        `;
    }
    
    itemPreview.innerHTML = `
        <h2>Current Item</h2>
        
        ${difficultyHTML}
        
        <div class="item-field">
            <div class="item-field-label">Passage</div>
            <div class="item-field-content editable" onclick="makeEditable(this, 'passage')">
                ${item.passage || 'N/A'}
            </div>
        </div>
        
        <div class="item-field">
            <div class="item-field-label">Question</div>
            <div class="item-field-content editable" onclick="makeEditable(this, 'question')">
                ${item.question || 'N/A'}
            </div>
        </div>
        
        <div class="item-field">
            <div class="item-field-label">Target Answer</div>
            <div class="item-field-content editable" onclick="makeEditable(this, 'target_answer')">
                ${item.target_answer || 'N/A'}
            </div>
        </div>
        
        <div class="item-field">
            <div class="item-field-label">Distractor 1 (Partial)</div>
            <div class="item-field-content editable" onclick="makeEditable(this, 'distractor_1')">
                ${item.distractor_1 || 'N/A'}
            </div>
        </div>
        
        <div class="item-field">
            <div class="item-field-label">Distractor 2 (Minimal)</div>
            <div class="item-field-content editable" onclick="makeEditable(this, 'distractor_2')">
                ${item.distractor_2 || 'N/A'}
            </div>
        </div>
        
        <div class="item-field">
            <div class="item-field-label">Metadata</div>
            <div class="metadata-grid">
                <div class="metadata-item">
                    <div class="metadata-label">Event-Chain</div>
                    <div class="metadata-value">${item.event_chain_relation || 'N/A'}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Knowledge-Base</div>
                    <div class="metadata-value">${item.knowledge_base_inference || 'N/A'}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">QAR Level</div>
                    <div class="metadata-value">${item.qar_level || 'N/A'}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Coherence</div>
                    <div class="metadata-value">${item.coherence_level || 'N/A'}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Stance</div>
                    <div class="metadata-value">${item.explanatory_stance || 'N/A'}</div>
                </div>
            </div>
        </div>
        
        <div class="item-actions">
            <button class="btn-small btn-save" onclick="saveItemChanges()">Save Changes</button>
            <button class="btn-small btn-add" onclick="addToCollection()">Add to Collection</button>
        </div>
    `;
}

function makeEditable(element, field) {
    const currentText = element.textContent.trim();
    if (currentText === 'N/A') currentText = '';
    
    element.innerHTML = `<textarea>${currentText}</textarea>`;
    const textarea = element.querySelector('textarea');
    textarea.focus();
    textarea.select();
    
    textarea.addEventListener('blur', () => {
        const newValue = textarea.value.trim() || 'N/A';
        element.textContent = newValue;
        if (currentItem) {
            currentItem[field] = newValue === 'N/A' ? '' : newValue;
        }
    });
    
    textarea.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            element.textContent = currentText || 'N/A';
        }
    });
}

async function saveItemChanges() {
    if (!currentItem) {
        alert('No item to save');
        return;
    }
    
    try {
        const response = await fetch('/update_item', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ item: currentItem })
        });
        
        const data = await response.json();
        
        if (data.error) {
            alert('Error: ' + data.error);
        } else {
            alert('Item saved successfully!');
            if (data.difficulty) {
                updateItemPreview(data.item, data.difficulty);
            }
        }
    } catch (error) {
        alert('Error saving item: ' + error.message);
    }
}

async function addToCollection() {
    if (!currentItem) {
        alert('No item to add');
        return;
    }
    
    try {
        const response = await fetch('/save_to_collection', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.error) {
            alert('Error: ' + data.error);
        } else {
            alert(`Item added to collection! (${data.collection_size} items total)`);
            loadCollection();
        }
    } catch (error) {
        alert('Error adding to collection: ' + error.message);
    }
}

async function loadCollection() {
    try {
        const response = await fetch('/get_collection');
        const data = await response.json();
        
        const collectionItems = document.getElementById('collectionItems');
        const collectionCount = document.getElementById('collectionCount');
        const exportAllBtn = document.getElementById('exportAllBtn');
        
        collectionCount.textContent = data.count;
        exportAllBtn.disabled = data.count === 0;
        
        if (data.items.length === 0) {
            collectionItems.innerHTML = `
                <div class="empty-state" style="padding: 40px 20px;">
                    <p style="color: #b0b0b0; font-size: 13px;">No items saved yet</p>
                </div>
            `;
        } else {
            collectionItems.innerHTML = data.items.map(item => `
                <div class="collection-item">
                    <div class="collection-item-header">
                        <span class="collection-item-id">Item #${item.item_id}</span>
                        <button class="collection-item-delete" onclick="deleteFromCollection(${item.item_id})">×</button>
                    </div>
                    <div class="collection-item-preview">
                        ${item.question || item.passage || 'No preview available'}
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading collection:', error);
    }
}

async function deleteFromCollection(itemId) {
    if (!confirm('Delete this item from collection?')) return;
    
    try {
        const response = await fetch('/delete_from_collection', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ item_id: itemId })
        });
        
        const data = await response.json();
        
        if (data.error) {
            alert('Error: ' + data.error);
        } else {
            loadCollection();
        }
    } catch (error) {
        alert('Error deleting item: ' + error.message);
    }
}

async function exportCollection() {
    try {
        const response = await fetch('/export_collection', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.error) {
            alert('Error: ' + data.error);
        } else {
            alert(`Exported ${data.item_count} items to ${data.filename}`);
        }
    } catch (error) {
        alert('Error exporting collection: ' + error.message);
    }
}

// Load collection on page load
document.addEventListener('DOMContentLoaded', () => {
    loadCollection();
});
```

Replace the existing updateItemPreview function and add these new functions.
