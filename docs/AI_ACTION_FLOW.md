# AI Action Button Flow

## Overview
This document describes the complete flow when a user clicks an AI action button (e.g., "Improve Tone", "Shorten", "Add Metrics") in the CV Editor.

## Complete Flow Diagram

```
User Clicks AI Action Button
    ↓
[FRONTEND] handleAIAssist() called
    ↓
1. Validation Checks (Frontend)
   ├─ Check if text is selected
   ├─ Check if in Visual mode
   ├─ Check if iframe is ready
   └─ Check if document is accessible
    ↓
2. Cleanup Previous Actions
   ├─ Remove leftover placeholders
   └─ Remove leftover highlights
    ↓
3. Lock Editing
   ├─ Disable contentEditable
   ├─ Add overlay to prevent interaction
   └─ Disable keyboard/mouse events
    ↓
4. Selection Validation
   ├─ Verify selection range is valid
   ├─ Refresh selection if needed
   └─ Clone selection range for safety
    ↓
5. Visual Feedback
   ├─ Highlight selected text (yellow)
   ├─ Show "Processing with AI..." message
   └─ Insert placeholder element
    ↓
6. Capture Selection HTML
   ├─ Clone selection contents
   └─ Convert to HTML string
    ↓
7. API Request (with Retry Logic)
   ├─ Attempt 1: Call backend API
   ├─ If fails: Wait (exponential backoff)
   ├─ Attempt 2: Retry
   ├─ If fails: Wait (exponential backoff)
   └─ Attempt 3: Final retry
    ↓
[BACKEND] /prepare/cv/{cv_id}/assist endpoint
    ↓
8. Backend Validation
   ├─ Check selection_html is provided
   ├─ Verify CV exists and belongs to user
   └─ Fetch job context (description, title, company)
    ↓
9. AI Service Call
   ├─ Build prompts (system + user)
   ├─ Include job context in prompt
   └─ Call LLM (OpenRouter) with:
      - Model: openai/gpt-oss-120b
      - Temperature: 0.3
      - Max tokens: 2000
    ↓
10. LLM Response Processing
    ├─ Strip markdown code fences (if present)
    └─ Return improved HTML
    ↓
[FRONTEND] Receives Response
    ↓
11. Response Validation (Frontend)
    ├─ Check result.success === true
    ├─ Check result.improved_html exists
    └─ Normalize HTML (strip code fences again)
    ↓
12. DOM Replacement
    ├─ Remove highlight wrapper
    ├─ Replace placeholder with improved HTML
    └─ Use DocumentFragment for batch insertion
    ↓
13. UI State Update (Immediate)
    ├─ flushSync() forces immediate React render
    ├─ setAssisting(false) - clears "Processing..."
    ├─ setShowCustomDialog(false) - closes dialog
    ├─ setCustomInstruction('') - clears input
    └─ unlockEditing() - re-enables editing
    ↓
14. Success Message
    └─ Show "Text improved successfully!" for 3 seconds
    ↓
15. Background Sync
    └─ syncIframeDocumentToState() - syncs iframe to React state
```

## Double-Checking and Validation

### Frontend Validation (Multiple Layers)

1. **Pre-Request Validation**:
   - ✅ Selection exists and is not empty
   - ✅ Editor is in Visual mode
   - ✅ Iframe is ready and accessible
   - ✅ Selection range is valid (not collapsed, not pointing to removed elements)

2. **Selection Range Validation**:
   - ✅ Range is cloned before use (prevents mutation)
   - ✅ Range validity is checked after cleanup
   - ✅ Selection is refreshed if invalid

3. **Response Validation**:
   - ✅ `result.success === true` check
   - ✅ `result.improved_html` existence check
   - ✅ HTML normalization (removes markdown fences)

4. **HTML Normalization** (Double-Check):
   - ✅ **Frontend**: `normalizeImprovedHtml()` removes markdown code fences
   - ✅ **Backend**: `_strip_code_fences()` also removes markdown code fences
   - **Note**: Both frontend and backend strip code fences, providing redundancy

### Backend Validation

1. **Input Validation**:
   - ✅ `selection_html` is required (400 error if missing)
   - ✅ CV exists and belongs to authenticated user (404 if not found)

2. **Context Enhancement**:
   - ✅ Job description is fetched and added to context
   - ✅ Job title and company are added to context

3. **Error Handling**:
   - ✅ Returns original HTML on error (graceful degradation)
   - ✅ Error message is included in response

### No Content Validation

**Important**: The system does NOT double-check the content quality or accuracy:
- ❌ No validation that improved text is better than original
- ❌ No fact-checking or accuracy verification
- ❌ No comparison with original CV data
- ❌ No grammar/spell checking (relies on LLM)
- ❌ No validation that metrics are real (if "add_metrics" intent)

The system trusts the LLM output and directly inserts it into the CV.

## Retry Logic

- **Max Retries**: 2 (total 3 attempts)
- **Retry Delay**: Exponential backoff (1s, 2s)
- **Timeout**: 60 seconds per attempt
- **Abort Conditions**: Request cancellation, network errors

## Error Handling

### Frontend Errors
- Selection invalid → Show error, unlock editing
- Request timeout → Show timeout message, retry
- Network error → Show network error, retry
- Invalid response → Show error, restore original content

### Backend Errors
- Missing input → 400 Bad Request
- CV not found → 404 Not Found
- LLM error → 500 Internal Server Error, returns original HTML

## Security Considerations

1. **Authentication**: User must be authenticated (via `get_current_user`)
2. **Authorization**: CV must belong to the authenticated user
3. **Input Sanitization**: HTML is inserted directly (no XSS protection beyond browser defaults)
4. **Rate Limiting**: None implemented (could be added)

## Performance Characteristics

- **Request Timeout**: 60 seconds
- **Typical LLM Response**: Fast (as reported by user)
- **Frontend Processing**: Minimal delay (optimized with flushSync)
- **DOM Updates**: Batched using DocumentFragment
- **State Updates**: Forced immediate render with flushSync

## Potential Improvements

1. **Content Validation**: Add validation service to check improved content quality
2. **Fact Verification**: Compare against original CV data to ensure no false information
3. **Grammar Check**: Additional grammar/spell checking layer
4. **User Confirmation**: Optional "Accept/Reject" step before applying changes
5. **Diff View**: Show before/after comparison
6. **Rate Limiting**: Prevent abuse of AI actions

