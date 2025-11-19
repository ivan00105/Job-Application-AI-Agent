# Chrome Extension – Auto-Fill Agent

LLM-powered Chrome extension that understands and fills job application forms using semantic analysis.

**Parent docs:** [../docs/SETUP.md](../docs/SETUP.md) for full installation instructions.

---

## How it works

```
User clicks "AI Auto-Fill"
  ↓
Extract form elements via Accessibility API
  ↓
Send element metadata (role, label, context) to backend
  ↓
LLM matches CV data to fields → returns actions
  ↓
Extension executes high-confidence actions
  ↓
Highlights medium-confidence fields for review
  ↓
Prompts user for low-confidence fields
```

**Key advantage:** Uses semantic roles (`textbox`, `combobox`, `radio`) instead of CSS selectors, so it works across React, Workday, Lever, SmartRecruiters, and other modern form implementations.

---

## Installation

```bash
cd extension
pip install Pillow
python create-icons.py
# Then: chrome://extensions/ → Developer Mode → Load unpacked → select extension/
```

---

## Usage

1. Log into the web app at `http://localhost:5173` and upload your CV
2. Navigate to any job application form
3. Click the purple "AI Auto-Fill" button (bottom-right)
4. Extension auto-fills high-confidence fields, highlights uncertain ones, and asks for missing info
5. Review and submit

---

## Files

- **`content.js`** (~2850 lines): Element extraction, DOM manipulation, action execution, user prompts
- **`background.js`** (~260 lines): API communication, token management
- **`manifest.json`**: Extension configuration (Manifest V3)
- **`popup.html/js`**: Extension popup UI
- **`extension-bridge.js`**: Token sync bridge from web app
- **`config.js`**: Backend URL configuration

---

## API contract

**Endpoint:** `POST /api/autofill/analyze-form`

**Request:**
```json
{
  "elements": [
    {
      "id": "elem_0",
      "role": "textbox",
      "label": "First Name",
      "type": "text",
      "required": true,
      "currentValue": "",
      "context": "Personal Information section...",
      "groupLabel": "Contact Details",
      "optionLabel": "",
      "multiSelect": false
    }
  ],
  "url": "https://jobs.company.com/apply",
  "company_name": "Company Inc"
}
```

**Response:**
```json
{
  "actions": [
    {
      "elementId": "elem_0",
      "label": "First Name",
      "interaction": "fill_text",
      "value": "John",
      "confidence": "high",
      "reasoning": "Found in CV personal_info"
    }
  ]
}
```

---

## Interaction types

- **`fill_text`**: Set value on input/textarea
- **`select_option`**: Choose from native `<select>` dropdown
- **`click`**: Click buttons, radios, or custom dropdown options
- **`check`**: Check/uncheck checkboxes
- **`need_options`**: Placeholder for custom dropdowns that need option extraction

---

## Confidence levels

- **`high`**: Auto-fill immediately (exact match from CV or memory)
- **`medium`**: Fill and highlight for review (inferred or partial match)
- **`low`**: Show popup asking user for input (no data available)

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Button not appearing | Reload page, check extension is enabled at `chrome://extensions/` |
| "CV not found" | Upload CV in the Profile page first |
| "Not logged in" | Log into web app at `localhost:5173`, token syncs automatically |
| "No form found" | Make sure you're on an application form, not a job listing page |
| Extension context invalidated | Reload page after updating extension code |

---

## Development notes

- To change LLM behavior, edit `backend/prompts/form_fill_prompt.txt` instead of extension code
- Extension uses `MutationObserver` for dynamic content detection
- Element registry maintains DOM references even after re-renders
- Deep Shadow DOM traversal reaches inputs inside custom web components
- Portal-aware dropdown watchers detect options rendered in `document.body`

---

## Architecture highlights (v4.0)

- **Accessibility API extraction**: Uses semantic roles instead of DOM scraping
- **Element registry pattern**: Maps `elem_0`, `elem_1` to actual DOM nodes to avoid token bloat
- **Stale element recovery**: Re-queries detached DOM nodes on SPA re-renders
- **React state sync**: Bypasses React's synthetic events to update controlled components
- **Legend-aware labeling**: Stitches `<fieldset>/<legend>` text into radio/checkbox labels
- **Multi-select detection**: Identifies Workday-style multi-select dropdowns via `data-automation-id`
- **Portal option matching**: Watches entire `document.body` for dropdown options, not just immediate children
