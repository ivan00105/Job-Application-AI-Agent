// Content script for LLM-based job application autofill
// Simplified approach: Extract HTML → Send to LLM → Execute actions

console.log('[AutoFill Agent] Content script loaded (LLM-based v2.0)');

// State management
let isAutoFillActive = false;
let autoFillButton = null;

/**
 * Inject floating auto-fill button
 */
function injectAutoFillButton() {
    // Don't inject on our own web app
    if (window.location.hostname === 'localhost' && window.location.port === '5173') {
        return;
    }

    // Don't inject if already exists
    if (autoFillButton) {
        return;
    }

    // Create floating button
    const button = document.createElement('div');
    button.id = 'autofill-trigger-button';
    button.innerHTML = `
    <div style="
      position: fixed;
      bottom: 20px;
      right: 20px;
      z-index: 999999;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 15px 20px;
      border-radius: 50px;
      box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
      cursor: pointer;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      font-size: 14px;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: all 0.3s ease;
      user-select: none;
    " onmouseover="this.style.transform='scale(1.05)'; this.style.boxShadow='0 6px 20px rgba(102, 126, 234, 0.6)';" onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='0 4px 15px rgba(102, 126, 234, 0.4)';">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
        <path d="M2 17l10 5 10-5"></path>
        <path d="M2 12l10 5 10-5"></path>
      </svg>
      <span id="autofill-button-text">AI Auto-Fill</span>
    </div>
  `;

    button.addEventListener('click', handleAutoFillClick);
    document.body.appendChild(button);
    autoFillButton = button;

    console.log('[AutoFill Agent] Button injected');
}

/**
 * Update button state
 */
function updateButtonState(text, color, loading = false) {
    const buttonEl = document.querySelector('#autofill-trigger-button > div');
    const textEl = document.getElementById('autofill-button-text');

    if (buttonEl && textEl) {
        textEl.textContent = text;
        if (loading) {
            buttonEl.style.background = '#9CA3AF';
            buttonEl.style.cursor = 'wait';
            textEl.textContent = text + '...';
        } else {
            buttonEl.style.background = color || 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
            buttonEl.style.cursor = 'pointer';
        }
    }
}

/**
 * Handle auto-fill button click
 */
async function handleAutoFillClick() {
    if (isAutoFillActive) {
        console.log('[AutoFill Agent] Already processing...');
        return;
    }

    isAutoFillActive = true;
    updateButtonState('Extracting', null, true);

    try {
        // 1. Extract form elements (NEW: structured extraction)
        const elements = extractFormElements();
        if (!elements || elements.length === 0) {
            alert('❌ No form fields found on this page.\n\nMake sure you\'re on a job application form.');
            isAutoFillActive = false;
            updateButtonState('AI Auto-Fill', null, false);
            return;
        }

        console.log(`[AutoFill Agent] Extracted ${elements.length} form elements`);

        // 2. Send to backend
        updateButtonState('Analyzing', null, true);
        const companyName = extractCompanyName();

        const response = await chrome.runtime.sendMessage({
            action: 'analyzeForm',
            elements: elements,  // Send structured elements instead of HTML
            url: window.location.href,
            companyName: companyName
        });

        if (!response || !response.success) {
            throw new Error(response?.error || 'Failed to analyze form');
        }

        const actions = response.actions || [];
        console.log(`[AutoFill Agent] Received ${actions.length} actions from LLM`);

        // 3. Execute actions
        updateButtonState('Filling', null, true);
        await executeActions(actions);

        // 4. Show completion
        isAutoFillActive = false;
        updateButtonState('✓ Done', '#10b981', false);

        setTimeout(() => {
            updateButtonState('AI Auto-Fill', null, false);
        }, 3000);

        const highConfCount = actions.filter(a => a.confidence === 'high').length;
        const lowConfCount = actions.filter(a => a.confidence === 'low').length;

        alert(`✅ Auto-Fill Complete!\n\n` +
            `✓ High confidence: ${highConfCount} fields\n` +
            `? Need your input: ${lowConfCount} fields\n\n` +
            `Review the highlighted fields before submitting.`);

    } catch (error) {
        console.error('[AutoFill Agent] Error:', error);
        isAutoFillActive = false;
        updateButtonState('AI Auto-Fill', null, false);

        let errorMessage = '❌ Auto-fill failed';
        const errStr = error.message || error.toString();

        if (errStr.includes('CV not found')) {
            errorMessage = '📄 No CV found\n\nPlease upload your CV in the Profile page first.';
        } else if (errStr.includes('Unauthorized') || errStr.includes('401')) {
            errorMessage = '🔒 Not logged in\n\nPlease log into the web app at localhost:5173';
        } else {
            errorMessage = `❌ Error\n\n${errStr}`;
        }

        alert(errorMessage);
    }
}

/**
 * Check if a button is an action/navigation button (not a form choice)
 */
function isActionButton(button) {
    const text = button.textContent.toLowerCase().trim();
    const ariaLabel = (button.getAttribute('aria-label') || '').toLowerCase();
    const dataTest = (button.getAttribute('data-test') || '').toLowerCase();

    // IMPORTANT: Check if button is a CHOICE button first (keep these)
    // These are buttons used as form selections (like radio buttons)
    if (isChoiceButton(button)) {
        return false; // NOT an action button - it's a form choice
    }

    // Common action button patterns
    const actionPatterns = [
        'add', 'save', 'submit', 'next', 'previous', 'back', 'cancel',
        'close', 'delete', 'remove', 'edit', 'upload', 'download',
        'continue', 'proceed', 'skip', 'finish', 'done', 'apply now'
    ];

    // Check if button text/label matches action patterns
    for (const pattern of actionPatterns) {
        if (text.includes(pattern) || ariaLabel.includes(pattern) || dataTest.includes(pattern)) {
            return true;
        }
    }

    // Check if button is in an ACTION button group/toolbar (navigation)
    // BUT: Only if it's NOT a choice button group (radiogroup, list with choices)
    const parent = button.parentElement;
    if (parent && (
        parent.classList.contains('actions') ||
        parent.classList.contains('toolbar') ||
        parent.getAttribute('role') === 'toolbar'
    )) {
        return true;
    }

    // If button has an icon but no meaningful text, likely an action button
    if (button.querySelector('svg, i[class*="icon"]') && text.length < 3) {
        return true;
    }

    return false;
}

/**
 * Check if a button is a choice button (like radio button alternative)
 */
function isChoiceButton(button) {
    // Check if button has aria-pressed (toggle behavior)
    if (button.hasAttribute('aria-pressed')) {
        return true;
    }

    // Check if button is in a radiogroup or list (choice group)
    const choiceGroup = button.closest('[role="radiogroup"], [role="list"], [role="group"][aria-label*="select"], [class*="select-pill"], [class*="choice"], [class*="option"]');
    if (choiceGroup) {
        return true;
    }

    // Check if button has data-value attribute (common for choice buttons)
    if (button.hasAttribute('data-value')) {
        return true;
    }

    // Check if button text is short and looks like a choice (Mr., Yes, No, etc.)
    const text = button.textContent.trim();
    const commonChoices = ['mr', 'mrs', 'ms', 'dr', 'yes', 'no', 'male', 'female', 'other'];
    if (text.length < 10 && commonChoices.includes(text.toLowerCase())) {
        return true;
    }

    return false;
}

/**
 * Extract structured form elements with labels and selectors
 * NEW: Smart extraction instead of sending bloated HTML
 */
function extractFormElements() {
    const elements = [];

    // Find all interactive elements (excluding hidden)
    const selectors = [
        'input:not([type="hidden"])',
        'textarea',
        'select',
        'button[type="button"]',
        'button:not([type="submit"])',
        '[role="textbox"]',
        '[role="combobox"]',
        '[role="radiogroup"]',
        '[contenteditable="true"]'
    ];

    document.querySelectorAll(selectors.join(',')).forEach(el => {
        // Skip navigation/header/footer elements
        if (el.closest('nav, header, footer, [role="navigation"]')) return;

        // Skip if hidden
        if (el.offsetParent === null && el.type !== 'file') return;

        // Skip file upload inputs (can't programmatically set for security reasons)
        if (el.type === 'file') {
            console.log(`[AutoFill] Skipping file upload: ${el.name || el.id}`);
            return;
        }

        // Skip submit and reset inputs (action buttons, not data entry)
        if (el.type === 'submit' || el.type === 'reset' || el.type === 'image') {
            console.log(`[AutoFill] Skipping ${el.type} button: ${el.name || el.value}`);
            return;
        }

        // Handle radiogroups: Skip the container, we'll capture individual buttons
        if (el.getAttribute('role') === 'radiogroup') {
            console.log(`[AutoFill] Skipping radiogroup container (will capture individual buttons): ${el.getAttribute('aria-label') || el.id}`);
            return;
        }

        // Skip action/navigation buttons (not data entry)
        if (el.tagName.toLowerCase() === 'button' && isActionButton(el)) {
            console.log(`[AutoFill] Skipping action button: ${el.textContent.trim()}`);
            return;
        }

        // Keep choice buttons (like Title: Mr/Mrs/Ms)
        if (el.tagName.toLowerCase() === 'button' && isChoiceButton(el)) {
            console.log(`[AutoFill] Found choice button: ${el.textContent.trim()}`);
        }

        // Skip if already has a value (pre-filled)
        if (el.value && el.value.trim() && el.type !== 'button') {
            console.log(`[AutoFill] Skipping pre-filled field: ${el.name || el.id}`);
            return;
        }

        const elementInfo = {
            tag: el.tagName.toLowerCase(),
            type: el.type || el.getAttribute('role') || '',
            id: el.id || '',
            name: el.name || '',
            placeholder: el.placeholder || '',
            value: el.value || '',
            required: el.required || false,
            label: findLabelForElement(el),
            selector: generateSelector(el),
            context: getMinimalContext(el)
        };

        elements.push(elementInfo);
    });

    console.log(`[AutoFill Agent] Extracted ${elements.length} form elements`);
    return elements;
}

/**
 * Find label for an element using multiple strategies
 */
function findLabelForElement(element) {
    // Strategy 1: <label for="id">
    if (element.id) {
        const label = document.querySelector(`label[for="${element.id}"]`);
        if (label) return cleanText(label.textContent);
    }

    // Strategy 2: Wrapped in label
    const parentLabel = element.closest('label');
    if (parentLabel) return cleanText(parentLabel.textContent);

    // Strategy 3: aria-label
    if (element.getAttribute('aria-label')) {
        return cleanText(element.getAttribute('aria-label'));
    }

    // Strategy 4: aria-labelledby
    const labelledBy = element.getAttribute('aria-labelledby');
    if (labelledBy) {
        const labelEl = document.getElementById(labelledBy);
        if (labelEl) return cleanText(labelEl.textContent);
    }

    // Strategy 5: Placeholder as fallback
    if (element.placeholder) {
        return cleanText(element.placeholder);
    }

    // Strategy 6: Find nearest text in wrapper
    const wrapper = element.closest('[class*="field"], [class*="form"], [class*="input"]');
    if (wrapper) {
        // Get all text nodes before the input
        const allText = wrapper.textContent;
        const lines = allText.trim().split('\n').map(l => l.trim()).filter(l => l);

        // Find a line that looks like a label (short, not too generic)
        for (const line of lines) {
            if (line.length > 2 && line.length < 50 && !line.match(/^\d+$/)) {
                return cleanText(line);
            }
        }
    }

    return 'Unknown Field';
}

/**
 * Generate best available CSS selector for element
 */
function generateSelector(element) {
    // Priority 1: ID (most reliable)
    if (element.id) return `#${element.id}`;

    // Priority 2: Name attribute
    if (element.name) return `[name="${element.name}"]`;

    // Priority 3: Unique data attributes
    const dataAttrs = ['data-test', 'data-qa', 'data-testid', 'data-id'];
    for (const attr of dataAttrs) {
        const val = element.getAttribute(attr);
        if (val) return `[${attr}="${val}"]`;
    }

    // Priority 4: nth-of-type with tag
    const parent = element.parentElement;
    if (parent) {
        const siblings = Array.from(parent.children).filter(e => e.tagName === element.tagName);
        const index = siblings.indexOf(element) + 1;
        return `${element.tagName.toLowerCase()}:nth-of-type(${index})`;
    }

    return element.tagName.toLowerCase();
}

/**
 * Get minimal HTML context for element (wrapper structure)
 */
function getMinimalContext(element) {
    // Get immediate wrapper for LLM context
    const wrapper = element.closest('[class*="field"], [class*="form-group"], [class*="input"]') || element.parentElement;

    if (wrapper) {
        const clone = wrapper.cloneNode(true);

        // Keep structure but simplify
        clone.querySelectorAll('*').forEach(el => {
            const keep = ['id', 'name', 'class', 'type', 'role', 'for'];
            Array.from(el.attributes).forEach(attr => {
                if (!keep.includes(attr.name)) el.removeAttribute(attr.name);
            });
        });

        // Limit to 500 chars
        return clone.outerHTML.substring(0, 500);
    }

    return '';
}

/**
 * Clean text: remove extra whitespace, newlines, special chars
 */
function cleanText(text) {
    return text
        .replace(/[\n\r\t]+/g, ' ')  // Replace newlines/tabs with space
        .replace(/\s+/g, ' ')         // Collapse multiple spaces
        .replace(/[*:]+$/g, '')       // Remove trailing asterisks/colons
        .trim();
}

/**
 * Find element using fallback strategies when primary selector fails
 * ENHANCED: Uses findLabelForElement() and type matching
 */
function findElementFallback(action) {
    const label = action.label.toLowerCase();
    const value = action.value ? action.value.toLowerCase() : '';

    // Strategy 0: Check if selector points to a wrapper component
    // If so, find the actual input/select/textarea inside it
    try {
        const wrapper = document.querySelector(action.selector);
        if (wrapper) {
            // Check if it's a custom component (not a native form element)
            const tagName = wrapper.tagName.toLowerCase();
            if (!['input', 'select', 'textarea', 'button'].includes(tagName)) {
                // It's a wrapper component - find the actual form element inside
                const actualInput = wrapper.querySelector('input, select, textarea, button');
                if (actualInput) {
                    console.log(`[AutoFill Agent] Found actual input inside ${action.selector}:`, actualInput);
                    return actualInput;
                }
            }
        }
    } catch (e) {
        // Invalid selector, continue to other strategies
    }

    // NEW: Comprehensive search by label + type + name + placeholder
    const allInputs = document.querySelectorAll('input, select, textarea, button');

    for (const input of allInputs) {
        // Skip hidden elements
        if (input.type === 'hidden' || input.offsetParent === null) continue;

        // Match by label (using our smart findLabelForElement function)
        const inputLabel = findLabelForElement(input).toLowerCase();
        const labelMatches = inputLabel.includes(label) || label.includes(inputLabel);

        if (labelMatches) {
            // Also check type matches the interaction
            if (action.interaction === 'fill_text' &&
                ['text', 'email', 'tel', 'url', 'password', 'number', 'date', ''].includes(input.type || '')) {
                return input;
            }
            if (action.interaction === 'fill_text' && input.tagName.toLowerCase() === 'textarea') {
                return input;
            }
            if (action.interaction === 'select_option' && input.tagName.toLowerCase() === 'select') {
                return input;
            }
            if (action.interaction === 'click' && ['button', 'radio', 'checkbox'].includes(input.type || input.tagName.toLowerCase())) {
                return input;
            }
            if (action.interaction === 'check' && ['checkbox', 'radio'].includes(input.type)) {
                return input;
            }
        }

        // Match by placeholder
        if (input.placeholder &&
            (input.placeholder.toLowerCase().includes(label) || label.includes(input.placeholder.toLowerCase()))) {
            return input;
        }

        // Match by name attribute (fuzzy)
        if (input.name &&
            (input.name.toLowerCase().includes(label.replace(/\s+/g, '')) ||
                label.replace(/\s+/g, '').includes(input.name.toLowerCase()))) {
            return input;
        }
    }

    return null;
}

/**
 * Execute actions returned by LLM
 */
async function executeActions(actions) {
    for (let i = 0; i < actions.length; i++) {
        const action = actions[i];

        // Show popup for low confidence actions
        if (action.confidence === 'low') {
            showUserPrompt(action);
            continue;
        }

        try {
            let element = document.querySelector(action.selector);

            // Check if we found a wrapper component instead of actual input
            if (element) {
                const tagName = element.tagName.toLowerCase();
                if (!['input', 'select', 'textarea', 'button'].includes(tagName)) {
                    console.log(`[AutoFill Agent] Selector points to wrapper component: ${action.selector}, searching inside...`);
                    const actualInput = element.querySelector('input, select, textarea, button');
                    if (actualInput) {
                        element = actualInput;
                        console.log(`[AutoFill Agent] Found actual form element inside wrapper`);
                    } else {
                        console.warn(`[AutoFill Agent] No form element found inside wrapper`);
                        element = null;
                    }
                }
            }

            // If selector fails or no actual input found, try fallback strategies
            if (!element) {
                console.warn(`[AutoFill Agent] Primary selector failed or invalid: ${action.selector}`);
                element = findElementFallback(action);

                if (!element) {
                    console.warn(`[AutoFill Agent] All fallback strategies failed for: ${action.label}`);
                    // Fallback to user prompt
                    showUserPrompt(action);
                    continue;
                } else {
                    console.log(`[AutoFill Agent] Found element via fallback for: ${action.label}`);
                }
            }

            // Execute based on interaction type (using improved tryFillField logic)
            switch (action.interaction) {
                case 'fill_text':
                    element.value = action.value;
                    element.dispatchEvent(new Event('input', { bubbles: true }));
                    element.dispatchEvent(new Event('change', { bubbles: true }));
                    element.dispatchEvent(new Event('blur', { bubbles: true }));
                    console.log(`✓ Filled: ${action.label} = ${action.value}`);
                    break;

                case 'click':
                    console.log(`[AutoFill] Attempting to click: ${action.label}`, action.selector, element);

                    // Special handling for radio buttons - ensure we click the right value
                    if (element.type === 'radio') {
                        const radioName = element.name;
                        // Try to find the specific radio button by value
                        const radios = document.querySelectorAll(`input[type="radio"][name="${radioName}"]`);
                        let targetRadio = element; // default to found element

                        for (const radio of radios) {
                            // Match by value or associated label
                            if (radio.value.toLowerCase() === action.value.toLowerCase()) {
                                targetRadio = radio;
                                break;
                            }
                            const label = document.querySelector(`label[for="${radio.id}"]`);
                            if (label && label.textContent.toLowerCase().trim() === action.value.toLowerCase()) {
                                targetRadio = radio;
                                break;
                            }
                        }
                        element = targetRadio;
                        console.log(`[AutoFill] Found specific radio button for value: ${action.value}`);
                    }

                    // Special handling for choice buttons - find by text content
                    if (element.tagName === 'BUTTON' && isChoiceButton(element)) {
                        const buttonText = element.textContent.trim().toLowerCase();
                        const targetValue = action.value.toLowerCase();

                        // If text doesn't match, try to find the right button in the group
                        if (buttonText !== targetValue) {
                            const parent = element.closest('[role="radiogroup"], [role="list"], [role="group"]');
                            if (parent) {
                                const buttons = parent.querySelectorAll('button');
                                for (const btn of buttons) {
                                    if (btn.textContent.trim().toLowerCase() === targetValue) {
                                        element = btn;
                                        console.log(`[AutoFill] Found specific choice button: ${btn.textContent.trim()}`);
                                        break;
                                    }
                                }
                            }
                        }
                    }

                    // Try multiple click methods for better compatibility
                    try {
                        // Method 1: Direct click
                        element.click();

                        // Method 2: Dispatch mouse events (for some custom components)
                        element.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
                        element.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
                        element.dispatchEvent(new MouseEvent('click', { bubbles: true }));

                        // Method 3: Dispatch change event (for form elements)
                        element.dispatchEvent(new Event('change', { bubbles: true }));

                        // Method 4: Focus and trigger (for some custom inputs)
                        element.focus();
                        element.dispatchEvent(new Event('focus', { bubbles: true }));

                        console.log(`✓ Clicked: ${action.label} = ${action.value}`);
                    } catch (clickError) {
                        console.error(`[AutoFill] Click failed for ${action.label}:`, clickError);
                    }

                    // Wait a bit for any animations/changes
                    await new Promise(resolve => setTimeout(resolve, 100));
                    break;

                case 'select_option':
                    if (element.tagName === 'SELECT') {
                        // Improved dropdown selection with multiple matching strategies
                        const options = Array.from(element.options);
                        let match = null;

                        // 1. Exact match
                        match = options.find(opt =>
                            opt.text.toLowerCase() === action.value.toLowerCase()
                        );

                        // 2. Value contains option
                        if (!match) {
                            match = options.find(opt =>
                                action.value.toLowerCase().includes(opt.text.toLowerCase())
                            );
                        }

                        // 3. Option contains value
                        if (!match) {
                            match = options.find(opt =>
                                opt.text.toLowerCase().includes(action.value.toLowerCase())
                            );
                        }

                        // 4. Word-level matching
                        if (!match) {
                            const valueWords = action.value.toLowerCase().split(/\s+/);
                            match = options.find(opt => {
                                const optWords = opt.text.toLowerCase().split(/\s+/);
                                return valueWords.some(vw => optWords.some(ow =>
                                    ow.includes(vw) || vw.includes(ow)
                                ));
                            });
                        }

                        if (match) {
                            element.value = match.value;
                            element.dispatchEvent(new Event('change', { bubbles: true }));
                            element.dispatchEvent(new Event('input', { bubbles: true }));
                            element.dispatchEvent(new Event('blur', { bubbles: true }));
                            console.log(`✓ Selected: ${action.label} = ${match.text}`);
                        } else {
                            console.warn(`[AutoFill Agent] No matching option for: ${action.label} = "${action.value}"`);
                            console.warn(`Available: ${options.map(o => o.text).join(', ')}`);
                            showUserPrompt(action);
                        }
                    } else if (element.tagName === 'INPUT' && element.hasAttribute('list')) {
                        // Input with datalist
                        element.value = action.value;
                        element.dispatchEvent(new Event('input', { bubbles: true }));
                        element.dispatchEvent(new Event('change', { bubbles: true }));
                        element.dispatchEvent(new Event('blur', { bubbles: true }));
                        console.log(`✓ Filled datalist: ${action.label} = ${action.value}`);
                    } else {
                        // Custom dropdown fallback
                        element.value = action.value;
                        element.dispatchEvent(new Event('input', { bubbles: true }));
                        element.dispatchEvent(new Event('change', { bubbles: true }));
                        console.log(`✓ Filled: ${action.label} = ${action.value}`);
                    }
                    break;

                case 'check':
                    const shouldCheck = action.value === 'true' ||
                        action.value.toLowerCase() === 'yes' ||
                        action.value === '1' ||
                        action.value === true;
                    element.checked = shouldCheck;
                    element.dispatchEvent(new Event('change', { bubbles: true }));
                    element.dispatchEvent(new Event('click', { bubbles: true }));
                    console.log(`✓ ${shouldCheck ? 'Checked' : 'Unchecked'}: ${action.label}`);
                    break;

                default:
                    console.warn(`[AutoFill Agent] Unknown interaction type: ${action.interaction}`);
            }

            // Small delay between actions
            await new Promise(resolve => setTimeout(resolve, 50));

        } catch (error) {
            console.error(`[AutoFill Agent] Error executing action for ${action.label}:`, error);
            // Fallback to user prompt
            showUserPrompt(action);
        }
    }
}

/**
 * Show popup for user input (positioned near the field)
 */
function showUserPrompt(action) {
    // Try to find the element to position near
    let targetElement = null;
    try {
        targetElement = document.querySelector(action.selector);

        // If it's a wrapper component, find the actual input inside
        if (targetElement) {
            const tagName = targetElement.tagName.toLowerCase();
            if (!['input', 'select', 'textarea', 'button'].includes(tagName)) {
                const actualInput = targetElement.querySelector('input, select, textarea, button');
                if (actualInput) {
                    targetElement = actualInput;
                }
            }
        }

        // Try fallback if still not found
        if (!targetElement) {
            targetElement = findElementFallback(action);
        }
    } catch (e) {
        console.warn('[AutoFill Agent] Invalid selector for popup positioning, trying fallback');
        targetElement = findElementFallback(action);
    }

    // Create popup container
    const popup = document.createElement('div');
    popup.id = `autofill-popup-${action.label.replace(/\s+/g, '-')}`;
    popup.style.cssText = `
        position: fixed;
        z-index: 999999;
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        min-width: 350px;
        max-width: 450px;
        border: 3px solid #667eea;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    `;

    const companyName = extractCompanyName();

    // Show message for different interaction types
    let actionMessage = '';
    if (action.interaction === 'click') {
        actionMessage = '<p style="margin: 0 0 8px 0; color: #22c55e; font-size: 12px; font-weight: 600;">⚡ This will click the button</p>';
    }

    popup.innerHTML = `
        <h3 style="margin: 0 0 10px 0; font-size: 17px; color: #333;">🤔 Help Needed</h3>
        <p style="margin: 0 0 6px 0; color: #666; font-weight: 600; font-size: 14px;">${action.label}</p>
        <p style="margin: 0 0 8px 0; color: #888; font-size: 12px; font-style: italic;">${action.reasoning || 'The AI needs your help with this field'}</p>
        ${actionMessage}
        <input id="user-input" value="${action.value || ''}" placeholder="${action.interaction === 'click' ? 'Leave as-is for button clicks' : 'Enter value...'}" style="
            width: 100%;
            padding: 10px;
            border: 2px solid #ddd;
            border-radius: 6px;
            font-size: 14px;
            box-sizing: border-box;
            margin-bottom: 14px;
        " />
        <div style="display: flex; gap: 6px; flex-direction: column;">
            <button id="fill-once" style="
                padding: 10px;
                background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
                color: white;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 13px;
                font-weight: 600;
            ">✓ Fill Once (Don't Save)</button>
            <button id="save-global" style="
                padding: 10px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 13px;
                font-weight: 600;
            ">✨ Save for All Jobs</button>
            <button id="save-company" style="
                padding: 10px;
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                color: white;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 13px;
                font-weight: 600;
            ">🏢 Save for ${companyName}</button>
            <button id="skip" style="
                padding: 9px;
                background: #f5f5f5;
                color: #666;
                border: 1px solid #ddd;
                border-radius: 6px;
                cursor: pointer;
                font-size: 13px;
            ">Skip</button>
        </div>
    `;

    document.body.appendChild(popup);

    // Position popup near the field
    if (targetElement) {
        const rect = targetElement.getBoundingClientRect();
        const popupHeight = 350; // Approximate
        const popupWidth = 400;

        let top = rect.bottom + 10;
        let left = rect.left;

        // Check if popup fits below the field
        const spaceBelow = window.innerHeight - rect.bottom;
        if (spaceBelow < popupHeight && rect.top > spaceBelow) {
            // Position above if more space
            top = rect.top - popupHeight - 10;
        }

        // Check if popup fits horizontally
        if (left + popupWidth > window.innerWidth) {
            left = window.innerWidth - popupWidth - 20;
        }

        // Ensure popup is not off-screen
        top = Math.max(10, Math.min(top, window.innerHeight - popupHeight - 10));
        left = Math.max(10, left);

        popup.style.top = `${top}px`;
        popup.style.left = `${left}px`;

        // Highlight the field
        targetElement.style.outline = '3px solid #667eea';
        targetElement.style.outlineOffset = '2px';
        targetElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
    } else {
        // Fallback to center if element not found
        popup.style.top = '50%';
        popup.style.left = '50%';
        popup.style.transform = 'translate(-50%, -50%)';
    }

    // Focus input
    const input = popup.querySelector('#user-input');
    setTimeout(() => input.focus(), 100);

    // Event handlers
    popup.querySelector('#fill-once').addEventListener('click', () => {
        console.log(`[AutoFill] Fill Once clicked for:`, action.label, action.interaction);

        const answer = input ? input.value : '';
        const valueToUse = answer || action.value || '';

        // Always try to execute the action
        console.log(`[AutoFill] Executing:`, {
            selector: action.selector,
            value: valueToUse,
            interaction: action.interaction
        });

        tryFillField(action.selector, valueToUse, action.interaction);
        cleanup();
    });

    popup.querySelector('#save-global').addEventListener('click', () => {
        console.log(`[AutoFill] Save Global clicked for:`, action.label, action.interaction);

        const answer = input.value || '';
        const valueToUse = answer || action.value || '';

        // Save to memory (except for click interactions)
        if (action.interaction !== 'click' && valueToUse) {
            saveAnswer(action.label, valueToUse, 'global');
        }

        // Execute action
        tryFillField(action.selector, valueToUse, action.interaction);
        cleanup();
    });

    popup.querySelector('#save-company').addEventListener('click', () => {
        console.log(`[AutoFill] Save Company clicked for:`, action.label, action.interaction);

        const answer = input.value || '';
        const valueToUse = answer || action.value || '';

        // Save to memory (except for click interactions)
        if (action.interaction !== 'click' && valueToUse) {
            saveAnswer(action.label, valueToUse, 'company');
        }

        // Execute action
        tryFillField(action.selector, valueToUse, action.interaction);
        cleanup();
    });

    popup.querySelector('#skip').addEventListener('click', () => {
        cleanup();
    });

    // Cleanup function
    function cleanup() {
        popup.remove();
        if (targetElement) {
            targetElement.style.outline = '';
            targetElement.style.outlineOffset = '';
        }
    }

    // Close on Escape
    const escapeHandler = (e) => {
        if (e.key === 'Escape') {
            cleanup();
            document.removeEventListener('keydown', escapeHandler);
        }
    };
    document.addEventListener('keydown', escapeHandler);
}

/**
 * Try to fill field with value (improved for all field types)
 */
function tryFillField(selector, value, interaction) {
    try {
        let element = document.querySelector(selector);
        if (!element) {
            console.warn(`[AutoFill Agent] Element not found: ${selector}`);
            return;
        }

        // Check if we found a wrapper component instead of actual input
        const tagName = element.tagName.toLowerCase();
        if (!['input', 'select', 'textarea', 'button'].includes(tagName)) {
            const actualInput = element.querySelector('input, select, textarea, button');
            if (actualInput) {
                element = actualInput;
                console.log(`[AutoFill Agent] Found actual input inside wrapper for tryFillField`);
            }
        }

        switch (interaction) {
            case 'fill_text':
                // Standard text input
                element.value = value;
                element.dispatchEvent(new Event('input', { bubbles: true }));
                element.dispatchEvent(new Event('change', { bubbles: true }));
                element.dispatchEvent(new Event('blur', { bubbles: true }));
                console.log(`✓ Filled text: ${value}`);
                break;

            case 'click':
                // Click buttons or radio options
                console.log(`[AutoFill] Attempting to click: ${selector}`, element);

                // Try multiple click methods for better compatibility
                try {
                    // Method 1: Direct click
                    element.click();

                    // Method 2: Dispatch mouse events (for some custom components)
                    element.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
                    element.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
                    element.dispatchEvent(new MouseEvent('click', { bubbles: true }));

                    // Method 3: Dispatch change event (for form elements)
                    element.dispatchEvent(new Event('change', { bubbles: true }));

                    // Method 4: Focus and trigger (for some custom inputs)
                    element.focus();
                    element.dispatchEvent(new Event('focus', { bubbles: true }));

                    console.log(`✓ Clicked: ${selector}`);
                } catch (clickError) {
                    console.error(`[AutoFill] Click failed for ${selector}:`, clickError);
                    throw clickError;
                }
                break;

            case 'select_option':
                if (element.tagName === 'SELECT') {
                    // Improved dropdown selection with better matching
                    const options = Array.from(element.options);

                    // Try multiple matching strategies
                    let match = null;

                    // 1. Exact match (case-insensitive)
                    match = options.find(opt =>
                        opt.text.toLowerCase() === value.toLowerCase()
                    );

                    // 2. Fuzzy match - value contains option text
                    if (!match) {
                        match = options.find(opt =>
                            value.toLowerCase().includes(opt.text.toLowerCase())
                        );
                    }

                    // 3. Fuzzy match - option text contains value
                    if (!match) {
                        match = options.find(opt =>
                            opt.text.toLowerCase().includes(value.toLowerCase())
                        );
                    }

                    // 4. Partial word match
                    if (!match) {
                        const valueWords = value.toLowerCase().split(/\s+/);
                        match = options.find(opt => {
                            const optWords = opt.text.toLowerCase().split(/\s+/);
                            return valueWords.some(vw => optWords.some(ow =>
                                ow.includes(vw) || vw.includes(ow)
                            ));
                        });
                    }

                    if (match) {
                        element.value = match.value;
                        element.dispatchEvent(new Event('change', { bubbles: true }));
                        element.dispatchEvent(new Event('input', { bubbles: true }));
                        element.dispatchEvent(new Event('blur', { bubbles: true }));
                        console.log(`✓ Selected option: ${match.text}`);
                    } else {
                        console.warn(`[AutoFill Agent] No matching option found for: "${value}"`);
                        console.warn(`Available options: ${options.map(o => o.text).join(', ')}`);
                    }
                } else if (element.tagName === 'INPUT' && element.hasAttribute('list')) {
                    // Input with datalist dropdown
                    element.value = value;
                    element.dispatchEvent(new Event('input', { bubbles: true }));
                    element.dispatchEvent(new Event('change', { bubbles: true }));
                    element.dispatchEvent(new Event('blur', { bubbles: true }));
                    console.log(`✓ Filled datalist input: ${value}`);
                } else {
                    // Fallback for custom dropdowns
                    element.value = value;
                    element.dispatchEvent(new Event('input', { bubbles: true }));
                    element.dispatchEvent(new Event('change', { bubbles: true }));
                    console.log(`✓ Filled custom dropdown: ${value}`);
                }
                break;

            case 'check':
                // Checkbox
                const shouldCheck = value === 'true' ||
                    value.toLowerCase() === 'yes' ||
                    value === '1' ||
                    value === true;
                element.checked = shouldCheck;
                element.dispatchEvent(new Event('change', { bubbles: true }));
                element.dispatchEvent(new Event('click', { bubbles: true }));
                console.log(`✓ ${shouldCheck ? 'Checked' : 'Unchecked'}: ${selector}`);
                break;

            default:
                console.warn(`[AutoFill Agent] Unknown interaction type: ${interaction}`);
        }
    } catch (error) {
        console.error('[AutoFill Agent] Error filling field:', error);
    }
}

/**
 * Save answer to memory
 */
function saveAnswer(label, answer, contextType) {
    chrome.runtime.sendMessage({
        action: 'saveAnswer',
        data: {
            field_label: label,
            answer: answer,
            context_type: contextType,
            company_name: contextType === 'company' ? extractCompanyName() : null,
            job_url: window.location.href
        }
    }, response => {
        if (response && response.success) {
            console.log(`[AutoFill Agent] Saved answer: ${label}`);
        }
    });
}

/**
 * Extract company name from page
 */
function extractCompanyName() {
    const patterns = [
        document.querySelector('meta[property="og:site_name"]')?.content,
        document.querySelector('.company-name')?.innerText,
        document.title.split('-')[0].trim(),
        window.location.hostname.split('.')[0]
    ];

    return patterns.find(p => p) || 'Unknown';
}

// Inject button when page loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(injectAutoFillButton, 1000);
    });
} else {
    setTimeout(injectAutoFillButton, 1000);
}

// Listen for messages from background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'scrapeCurrentPage') {
        handleAutoFillClick();
        sendResponse({ success: true });
    }
    return true;
});
