# Job Application Autofill Extension

LLM-powered Chrome extension that automatically fills job application forms.

## Architecture (v2.0 - LLM-Based)

**Simplified Approach**: Instead of complex form scraping, we let the LLM understand the HTML.

```
User clicks "AI Auto-Fill" button
  ↓
Extract & simplify form HTML (~2-5KB)
  ↓
Send to backend LLM (single call)
  ↓
LLM returns actions: [{selector, value, interaction}]
  ↓
Execute actions in browser
  ↓
Show popups for low-confidence fields
```

### Benefits

- **77% less code**: ~300 lines instead of 1300+
- **Handles any form pattern**: LLM understands HTML semantically
- **More reliable**: No brittle scraping logic
- **Easy to maintain**: Just update prompts, not code

## Installation

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (top-right toggle)
3. Click "Load unpacked"
4. Select the `extension` folder

## Usage

1. Make sure you're logged into the web app (`localhost:5173`)
2. Navigate to a job application page
3. Click the floating "AI Auto-Fill" button (bottom-right)
4. The extension will:
   - Extract the form HTML
   - Analyze it with AI
   - Fill high-confidence fields automatically
   - Ask for your input on uncertain fields
5. Review the filled form before submitting

## Files

- **`content.js`** (300 lines): HTML extraction, action execution, user popups
- **`background.js`**: API communication with backend
- **`manifest.json`**: Extension configuration
- **`popup.html/js`**: Extension popup (optional settings)
- **`extension-bridge.js`**: Token sync from web app

## Backend Integration

The extension calls the new `/api/autofill/analyze-form` endpoint:

**Request**:
```json
{
  "html": "<simplified HTML>",
  "url": "https://...",
  "company_name": "..."
}
```

**Response**:
```json
{
  "actions": [
    {
      "label": "First Name",
      "selector": "#first-name",
      "interaction": "fill_text",
      "value": "John",
      "confidence": "high",
      "reasoning": "Found in CV"
    }
  ]
}
```

## Interaction Types

- **`fill_text`**: Set input.value and dispatch events
- **`click`**: Click buttons or radio options
- **`select_option`**: Choose from dropdown
- **`check`**: Check/uncheck checkbox

## Confidence Levels

- **`high`**: Fill immediately (exact match from CV/memory)
- **`medium`**: Fill but user should review (inferred)
- **`low`**: Ask user for input (no data available)

## Troubleshooting

**"CV not found"**: Upload your CV in the Profile page first.

**"Not logged in"**: Log into the web app at `localhost:5173` and reload the page.

**"No form found"**: Make sure you're on an application form page, not a job listing.

**Extension context invalidated**: Reload the page after updating the extension.

## Development

To modify the LLM behavior, edit `backend/prompts/form_fill_prompt.txt` instead of changing code logic.

## Backup

The old complex version is saved as `content.js.old` if you need to reference it.
