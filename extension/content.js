// Content script for LLM-based job application autofill
// A11y-enhanced approach: Extract semantic elements → Send to LLM → Execute via registry

console.log('[AutoFill Agent] Content script loaded (A11y-enhanced v4.0 - Shadow DOM + Retries)');

// State management
let isAutoFillActive = false;
let autoFillButton = null;

// Global registry to map IDs to actual DOM elements
const elementRegistry = new Map();

// Global state for agent (prepared for future multi-step loop)
// Currently only used for one-shot, but ready for loop architecture
let agentState = {
    loopCount: 0,
    maxLoops: 10,
    completedActions: new Set(),
    startTime: null,
    isRunning: false
};

const DROPDOWN_OPTION_SELECTORS = [
    '[role="option"]',
    '[data-automation-id="promptOption"]',
    '[data-automation-id="multiSelectOption"]',
    '[data-automation-id="selectItem"]',
    '[data-automation-id="selectOption"]',
    '[data-uxi-widget-type="selectoption"]',
    '[data-testid*="option"]',
    '[data-test*="option"]',
    '[data-role="option"]',
    '.select-option',
    '.Select-option',
    '.dropdown-item',
    '.ant-select-item-option',
    '.MuiAutocomplete-option',
    '.MuiListItem-root',
    '.chakra-select__option'
];

const GENERIC_PLACEHOLDER_PATTERNS = [
    /^select\b/i,
    /^choose\b/i,
    /^please select\b/i,
    /^please choose\b/i,
    /^select an option\b/i,
    /^select one\b/i,
    /^-- select/i,
    /^select\.\.\./i,
    /^none selected\b/i
];

const YES_VALUE_SET = new Set(['yes', 'true', 'y', '1', 'affirmative']);
const NO_VALUE_SET = new Set(['no', 'false', 'n', '0', 'negative']);

/**
 * Safely set the value of controlled inputs/textareas (React/Vue/etc.)
 */
function setNativeValue(element, value) {
    if (!element) {
        return;
    }

    const hasValueProperty = 'value' in element;
    if (!hasValueProperty) {
        if (element.isContentEditable) {
            element.textContent = value;
            element.dispatchEvent(new Event('input', { bubbles: true }));
            element.dispatchEvent(new Event('change', { bubbles: true }));
            element.dispatchEvent(new Event('blur', { bubbles: true }));
        }
        return;
    }

    const previousValue = element.value;
    const tracker = element._valueTracker;
    if (tracker) {
        tracker.setValue(previousValue);
    }

    const tag = element.tagName?.toLowerCase();
    let prototype = null;
    if (tag === 'textarea') {
        prototype = window.HTMLTextAreaElement && window.HTMLTextAreaElement.prototype;
    } else if (tag === 'select') {
        prototype = window.HTMLSelectElement && window.HTMLSelectElement.prototype;
    } else {
        prototype = window.HTMLInputElement && window.HTMLInputElement.prototype;
    }

    const ownDescriptor = Object.getOwnPropertyDescriptor(element, 'value');
    const prototypeDescriptor = prototype ? Object.getOwnPropertyDescriptor(prototype, 'value') : null;
    const descriptor = ownDescriptor?.set ? ownDescriptor : prototypeDescriptor;

    if (!descriptor || !descriptor.set) {
        element.value = value;
    } else {
        descriptor.set.call(element, value);
    }

    element.dispatchEvent(new Event('input', { bubbles: true }));
    element.dispatchEvent(new Event('change', { bubbles: true }));
    element.dispatchEvent(new Event('blur', { bubbles: true }));
}

/**
 * Ensure registry element references remain attached to the DOM
 */
async function ensureLiveElementData(action) {
    const elementData = elementRegistry.get(action.elementId);
    if (!elementData) {
        console.error(`[AutoFill] Element not found in registry: ${action.elementId}`);
        return null;
    }

    if (!elementData.domElement || !elementData.domElement.isConnected) {
        console.warn(`[AutoFill] Element ${action.elementId} detached. Attempting to re-query...`);
        if (elementData.a11yRole === 'option' && elementData.parentDropdownId) {
            const parentEntry = elementRegistry.get(elementData.parentDropdownId);
            if (parentEntry?.domElement) {
                focusAndOpenDropdown(parentEntry.domElement);
                const optionNode = await waitForDropdownOption(
                    elementData.optionText || action.value || action.label
                );
                if (optionNode) {
                    elementData.domElement = optionNode;
                    return elementData;
                }
            }
        }

        const refreshedElement = findElementFallback({
            label: action.label,
            value: action.value,
            interaction: action.interaction,
            selector: elementData.serialized?.selector
        });

        if (!refreshedElement) {
            console.error(`[AutoFill] Unable to recover element for ${action.label || action.elementId}`);
            elementRegistry.delete(action.elementId);
            return null;
        }

        elementData.domElement = refreshedElement;
    }

    return elementData;
}

/**
 * Helper function to check if agent can continue (for future loop implementation)
 * Includes all safety mechanisms to prevent infinite loops
 */
function canContinueAgent() {
    if (!agentState.isRunning) {
        return false;
    }

    if (agentState.loopCount >= agentState.maxLoops) {
        console.warn('[AutoFill] ⚠️ Max loops reached (10). Stopping agent.');
        return false;
    }

    if (agentState.startTime && Date.now() - agentState.startTime > 60000) {
        console.warn('[AutoFill] ⚠️ Agent timeout (60s). Stopping agent.');
        return false;
    }

    return true;
}

/**
 * Reset agent state
 */
function resetAgentState() {
    agentState.loopCount = 0;
    agentState.completedActions.clear();
    agentState.startTime = null;
    agentState.isRunning = false;
}

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
 * Close all active popups and remove highlights
 */
function closeAllPopups() {
    document.querySelectorAll('[id^="autofill-popup-"]').forEach(popup => {
        popup.remove();
    });

    // Remove any outline highlights from elements
    elementRegistry.forEach((elementData) => {
        if (elementData.domElement) {
            elementData.domElement.style.outline = '';
            elementData.domElement.style.outlineOffset = '';
        }
    });

    console.log('[AutoFill] Closed all popups and removed highlights');
}

/**
 * Open a single custom dropdown and extract its options
 * Handles auto-close by opening one at a time
 * Returns array of option objects: [{text, value, element}]
 */
async function waitForVisibleOptions(timeout = 1000) {
    const hasVisibleOptions = () => getVisibleOptionNodes().length > 0;

    if (hasVisibleOptions()) {
        return;
    }

    await new Promise(resolve => {
        const start = Date.now();
        const observer = new MutationObserver(() => {
            if (hasVisibleOptions()) {
                observer.disconnect();
                clearInterval(pollInterval);
                resolve();
            }
        });

        observer.observe(document.body, { childList: true, subtree: true });

        const pollInterval = setInterval(() => {
            if (hasVisibleOptions() || Date.now() - start > timeout) {
                observer.disconnect();
                clearInterval(pollInterval);
                resolve();
            }
        }, 100);
    });
}

async function extractOptionsFromDropdown(dropdown) {
    try {
        const dropdownLabel = findBestLabel(dropdown).label || getAccessibleName(dropdown);
        console.log(`[AutoFill] Opening dropdown: "${dropdownLabel}"`);

        // Try to find and click the dropdown button (many custom dropdowns have a separate button)
        const buttonId = dropdown.getAttribute('aria-controls') || dropdown.id.replace('-edit', '-button');
        const button = document.getElementById(buttonId);
        if (button && button.tagName.toLowerCase() === 'button') {
            console.log(`[AutoFill] Clicking dropdown button: ${buttonId}`);
            button.click();
        }

        // Also click and focus the input itself
        dropdown.click();
        dropdown.focus();
        dropdown.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
        dropdown.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
        dropdown.dispatchEvent(new Event('focus', { bubbles: true }));
        dropdown.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true }));

        // Wait for options to render instead of fixed timeout
        await waitForVisibleOptions(1200);

        // Extract options (try multiple strategies)
        const options = [];

        // Strategy 1: aria-owns
        const ownsId = dropdown.getAttribute('aria-owns');
        if (ownsId) {
            const listbox = document.getElementById(ownsId);
            if (listbox) {
                getVisibleOptionNodes(listbox).forEach(opt => {
                    options.push(buildOptionDescriptor(opt));
                });
            }
        }

        // Strategy 2: aria-controls
        if (options.length === 0) {
            const controlsId = dropdown.getAttribute('aria-controls');
            if (controlsId) {
                const listbox = document.getElementById(controlsId);
                if (listbox) {
                    getVisibleOptionNodes(listbox).forEach(opt => {
                        options.push(buildOptionDescriptor(opt));
                    });
                }
            }
        }

        // Strategy 3: Next sibling or parent container
        if (options.length === 0) {
            const container = dropdown.nextElementSibling ||
                dropdown.closest('[role="combobox"], .dropdown, .select, [class*="dropdown"]');
            if (container) {
                getVisibleOptionNodes(container).forEach(opt => {
                    options.push(buildOptionDescriptor(opt));
                });
            }
        }

        // Strategy 4: Global search for visible options (last resort)
        if (options.length === 0) {
            getVisibleOptionNodes().forEach(opt => {
                if (!options.some(existing => existing.element === opt)) {
                    options.push(buildOptionDescriptor(opt));
                }
            });
        }

        // Close the dropdown (multiple strategies)
        dropdown.blur();
        dropdown.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
        dropdown.dispatchEvent(new Event('blur', { bubbles: true }));
        document.body.click();

        // Longer delay to ensure dropdown closes before next one opens
        await new Promise(resolve => setTimeout(resolve, 300));

        if (options.length > 0) {
            console.log(`[AutoFill] ✓ Found ${options.length} options for "${dropdownLabel}": ${options.map(o => o.text).slice(0, 5).join(', ')}...`);
        } else {
            console.warn(`[AutoFill] ✗ No options found for "${dropdownLabel}"`);
        }

        return options;

    } catch (error) {
        console.error(`[AutoFill] Failed to extract options from dropdown:`, error);
        return [];
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

    closeAllPopups(); // Close any existing popups
    isAutoFillActive = true;
    updateButtonState('Extracting', null, true);

    try {
        // ==================== PASS 1: Initial Analysis ====================
        console.log('[AutoFill] ========== PASS 1: Initial Analysis ==========');

        // Extract all visible form elements
        const domElements = extractA11yEnhancedElements();

        if (!domElements || domElements.length === 0) {
            alert('❌ No form fields found on this page.\n\nMake sure you\'re on a job application form.');
            isAutoFillActive = false;
            updateButtonState('AI Auto-Fill', null, false);
            return;
        }

        // Build registry (keeps DOM references)
        const serializedElements = buildElementRegistry(domElements);
        console.log(`[AutoFill] Pass 1: Extracted ${serializedElements.length} visible elements`);

        // Identify all custom dropdowns (combobox/listbox that are NOT native <select>)
        const customDropdownElements = domElements.filter(el => {
            const role = el.a11yRole || '';
            const isCustomDropdown = (role === 'combobox' || role === 'listbox') &&
                el.element.tagName.toLowerCase() !== 'select';
            return isCustomDropdown;
        });

        console.log(`[AutoFill] Detected ${customDropdownElements.length} custom dropdowns (will handle in Pass 2)`);
        if (customDropdownElements.length > 0) {
            console.log('[AutoFill] Custom dropdowns:', customDropdownElements.map(el => ({
                elementId: el.elementId,
                role: el.a11yRole,
                label: el.a11yName,
                tag: el.element.tagName.toLowerCase(),
                id: el.element.id
            })));
        }

        // Send to backend for Pass 1 analysis (EXCLUDE custom dropdowns - they'll be handled in Pass 2)
        const customDropdownIds = new Set(
            customDropdownElements
                .map(el => el.elementId)
                .filter(id => typeof id === 'string')
        );

        const pass1Elements = serializedElements.filter(el => !customDropdownIds.has(el.id));

        console.log(`[AutoFill] Pass 1: Analyzing ${pass1Elements.length} non-dropdown fields`);
        console.log(`[AutoFill] Pass 1: Deferring ${customDropdownIds.size} custom dropdowns to Pass 2`);

        updateButtonState('Analyzing (1/2)', null, true);
        const companyName = extractCompanyName();

        const pass1Response = await chrome.runtime.sendMessage({
            action: 'analyzeForm',
            elements: pass1Elements,  // Only non-dropdown fields
            url: window.location.href,
            companyName: companyName,
            pass: 1
        });

        if (!pass1Response || !pass1Response.success) {
            throw new Error(pass1Response?.error || 'Failed to analyze form (Pass 1)');
        }

        let pass1Actions = pass1Response.actions || [];
        console.log(`[AutoFill] Pass 1: Received ${pass1Actions.length} actions from LLM`);

        // ==================== PASS 2: Resolve Custom Dropdowns ====================
        let pass2Actions = [];
        if (customDropdownElements.length > 0) {
            console.log(`[AutoFill] ========== PASS 2: Resolving ${customDropdownElements.length} Custom Dropdowns ==========`);
            updateButtonState(`Opening dropdowns (${customDropdownElements.length})`, null, true);

            // Extract options from EACH custom dropdown (one by one)
            const dropdownOptionsData = [];
            for (const dropdownEl of customDropdownElements) {
                const elementId = dropdownEl.elementId;
                if (!elementId) {
                    console.warn('[AutoFill] Dropdown element missing elementId, skipping');
                    continue;
                }

                const elementData = elementRegistry.get(elementId);
                if (!elementData) {
                    console.warn(`[AutoFill] Registry entry not found for dropdown ${elementId}`);
                    continue;
                }

                const dropdown = elementData.domElement;
                const dropdownLabel = dropdownEl.a11yName || 'Unknown';

                console.log(`[AutoFill] Pass 2: Opening dropdown "${dropdownLabel}" (ID: ${elementId})`);

                // Extract options with increased wait time
                const options = await extractOptionsFromDropdown(dropdown);

                if (options.length > 0) {
                    dropdownOptionsData.push({
                        elementId: elementId,
                        label: dropdownLabel,
                        options: options.map(opt => ({
                            text: opt.text,
                            value: opt.value
                        }))
                    });

                    // Add options as synthetic elements to registry for later clicking
                    let optionCounter = 0;
                    options.forEach(opt => {
                        const syntheticId = `${elementId}_option_${optionCounter++}`;
                        elementRegistry.set(syntheticId, {
                            domElement: opt.element,
                            a11yName: opt.text,
                            a11yRole: 'option',
                            parentDropdownId: elementId,
                            optionValue: opt.value,
                            optionText: opt.text,
                            groupLabel: dropdownLabel,
                            optionLabel: opt.text,
                            multiSelect: Boolean(elementData.isMultiSelect),
                            selector: '',
                            serialized: {
                                id: syntheticId,
                                role: 'option',
                                label: opt.text,
                                type: '',
                                required: false,
                                currentValue: '',
                                description: `Option for ${dropdownLabel}`,
                                context: '',
                                groupLabel: dropdownLabel,
                                optionLabel: opt.text,
                                multiSelect: Boolean(elementData.isMultiSelect),
                                selector: ''
                            }
                        });
                    });
                } else {
                    console.warn(`[AutoFill] Pass 2: No options found for "${dropdownLabel}"`);
                }
            }

            if (dropdownOptionsData.length > 0) {
                console.log(`[AutoFill] Pass 2: Extracted options for ${dropdownOptionsData.length} dropdowns`);
                updateButtonState('Analyzing (2/2)', null, true);

                // Send dropdown options to LLM for Pass 2
                const pass2Response = await chrome.runtime.sendMessage({
                    action: 'analyzeDropdowns',
                    dropdownOptions: dropdownOptionsData,
                    url: window.location.href,
                    companyName: companyName
                });

                if (pass2Response && pass2Response.success) {
                    pass2Actions = pass2Response.actions || [];
                    console.log(`[AutoFill] Pass 2: Received ${pass2Actions.length} actions from LLM`);
                }
            } else {
                console.warn('[AutoFill] Pass 2: No options extracted from any dropdown');
            }
        } else {
            console.log('[AutoFill] Pass 2: No custom dropdowns detected, skipping');
        }

        // ==================== MERGE & EXECUTE ====================
        // Remove "need_options" actions and merge with Pass 2 actions
        const finalActions = [
            ...pass1Actions.filter(a => a.interaction !== 'need_options'),
            ...pass2Actions
        ];

        console.log(`[AutoFill] ========== Executing ${finalActions.length} Total Actions ==========`);
        console.log(`[AutoFill] (Pass 1: ${pass1Actions.filter(a => a.interaction !== 'need_options').length}, Pass 2: ${pass2Actions.length})`);

        // Execute all actions at once
        updateButtonState('Filling', null, true);
        await executeActions(finalActions);

        // Show completion
        isAutoFillActive = false;
        updateButtonState('✓ Done', '#10b981', false);

        setTimeout(() => {
            updateButtonState('AI Auto-Fill', null, false);
        }, 3000);

        const highConfCount = finalActions.filter(a => a.confidence === 'high').length;
        const lowConfCount = finalActions.filter(a => a.confidence === 'low').length;

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
 * Get implicit ARIA role for an element
 */
function getImplicitRole(element) {
    if (element?.isContentEditable) {
        return 'textbox';
    }

    const tag = element.tagName.toLowerCase();
    const type = element.type?.toLowerCase();

    if (tag === 'input') {
        if (type === 'text' || type === 'email' || type === 'tel' || type === 'url' || type === 'password' || !type) return 'textbox';
        if (type === 'number') return 'spinbutton';
        if (type === 'checkbox') return 'checkbox';
        if (type === 'radio') return 'radio';
        if (type === 'button') return 'button';
        if (type === 'search') return 'searchbox';
        if (type === 'range') return 'slider';
        if (type === 'date' || type === 'datetime-local' || type === 'time') return 'textbox';
    }
    if (tag === 'textarea') return 'textbox';
    if (tag === 'select') return 'combobox';
    if (tag === 'button') return 'button';

    return '';
}

/**
 * Get accessible name for an element (following ARIA spec)
 */
function getAccessibleName(element) {
    // Check aria-label first
    if (element.getAttribute('aria-label')) {
        return cleanText(element.getAttribute('aria-label'));
    }

    // Check aria-labelledby
    const labelledBy = element.getAttribute('aria-labelledby');
    if (labelledBy) {
        const labelEl = document.getElementById(labelledBy);
        if (labelEl) return cleanText(labelEl.textContent);
    }

    // Check for <label> association
    if (element.id) {
        const label = document.querySelector(`label[for="${element.id}"]`);
        if (label) return cleanText(label.textContent);
    }

    // Check if wrapped in label
    const parentLabel = element.closest('label');
    if (parentLabel) return cleanText(parentLabel.textContent);

    // For buttons, use text content
    if (element.tagName.toLowerCase() === 'button') {
        return cleanText(element.textContent);
    }

    // NEW FALLBACK STRATEGY (for Lever, Workday, etc.)
    // Strategy 6: Check for a sibling label in a common wrapper
    const wrapper = element.closest('.application-question,.form-field,.form-group, .form-item, .field-wrapper, [class*="question"], [class*="field"]');
    if (wrapper) {
        const labelEl = wrapper.querySelector('.application-label,.form-label,.form-label-text, .field-label, .question-label, label, [class*="label"]:not(label)');
        if (labelEl && labelEl !== element) {
            const labelText = cleanText(labelEl.textContent);
            if (labelText && labelText.length > 0 && labelText.length < 100) {
                console.log(`[AutoFill] Found sibling label: "${labelText}"`);
                return labelText;
            }
        }
    }

    // Fallback to placeholder or title
    return cleanText(element.placeholder || element.title || '');
}

/**
 * Get accessible description for an element
 */
function getAccessibleDescription(element) {
    // Check aria-describedby
    const describedBy = element.getAttribute('aria-describedby');
    if (describedBy) {
        const descEl = document.getElementById(describedBy);
        if (descEl) return cleanText(descEl.textContent);
    }

    // Check title attribute
    if (element.title) {
        return cleanText(element.title);
    }

    return '';
}

/**
 * Approximate best label using weighted heuristics
 */
function findBestLabel(element) {
    const candidateScores = new Map();
    const addCandidate = (text, score) => {
        const cleaned = cleanText(text || '');
        if (!cleaned) {
            return;
        }
        const current = candidateScores.get(cleaned) || 0;
        if (score > current) {
            candidateScores.set(cleaned, score);
        }
    };

    addCandidate(element.getAttribute('aria-label'), 100);

    const labelledBy = element.getAttribute('aria-labelledby');
    if (labelledBy) {
        labelledBy.split(/\s+/).forEach(id => {
            const labelEl = document.getElementById(id);
            if (labelEl) {
                addCandidate(labelEl.textContent, 100);
            }
        });
    }

    if (element.id) {
        const explicitLabel = document.querySelector(`label[for="${element.id}"]`);
        if (explicitLabel) {
            addCandidate(explicitLabel.textContent, 90);
        }
    }

    const wrappedLabel = element.closest('label');
    if (wrappedLabel) {
        addCandidate(wrappedLabel.textContent, 90);
    }

    const datasetLabel = element.getAttribute('data-label') || element.getAttribute('data-question');
    addCandidate(datasetLabel, 80);

    const accessibleName = getAccessibleName(element);
    addCandidate(accessibleName, 80);

    const previousSibling = element.previousElementSibling;
    if (previousSibling) {
        addCandidate(previousSibling.textContent, 50);
    }

    // Wrapper text (div soup)
    const wrapper = element.closest('.application-question, .question, .form-field, .form-group, .field-wrapper, [class*="question"], [class*="field"], [data-testid*="question"], [data-test*="question"]');
    if (wrapper) {
        addCandidate(wrapper.textContent, 60);
    }

    addCandidate(element.placeholder, 40);
    addCandidate(element.getAttribute('title'), 35);

    if (candidateScores.size === 0) {
        return { label: '', score: 0 };
    }

    const [bestLabel, bestScore] = Array.from(candidateScores.entries())
        .sort((a, b) => b[1] - a[1])[0];

    return { label: bestLabel, score: bestScore };
}

/**
 * Capture nearby context to help LLM understand unlabeled fields
 */
function getSurroundingContext(element, maxLength = 150) {
    if (!element) {
        return '';
    }

    const wrapper = element.closest('.application-question, .question, .form-field, .form-group, .field-wrapper, [class*="question"], [class*="field"], [data-testid*="question"], [data-test*="question"]') || element.parentElement;
    if (!wrapper) {
        return '';
    }

    const clone = wrapper.cloneNode(true);
    clone.querySelectorAll('input, textarea, select, button, option').forEach(node => node.remove());
    clone.querySelectorAll('script, style').forEach(node => node.remove());

    const text = cleanText(clone.textContent || '');
    return text.substring(0, maxLength);
}

/**
 * Extract A11y-enhanced form elements with Shadow DOM support
 * ENHANCED: Recursively walks DOM including Shadow DOM
 */
function extractA11yEnhancedElements() {
    const elements = [];
    let totalScanned = 0;
    let skippedReasons = {
        navigation: 0,
        hidden: 0,
        fileInput: 0,
        submitReset: 0,
        actionButton: 0,
        preFilled: 0,
        noLabel: 0
    };

    // Selectors for both native and custom interactive elements
    const selectors = [
        'input:not([type="hidden"])',
        'textarea',
        'select',
        'button',
        '[role="button"]',      // Custom buttons
        '[role="combobox"]',    // Custom dropdowns
        '[role="listbox"]',
        '[role="option"]',      // Dropdown options (visible after pre-opening)
        '[role="radio"]',
        '[role="checkbox"]',
        '[role="textbox"]',
        '[contenteditable="true"]'
    ];

    // Recursive function to walk DOM including Shadow DOM
    function walkDOM(rootNode, depth = 0) {
        const indent = '  '.repeat(depth);

        // Find all interactive elements in current root
        rootNode.querySelectorAll(selectors.join(',')).forEach(el => {
            totalScanned++;

            // Skip navigation/header/footer elements
            if (el.closest('nav, header, footer, [role="navigation"]')) {
                skippedReasons.navigation++;
                console.log(`${indent}[AutoFill] Skipping (navigation): ${el.tagName} ${el.type || ''}`);
                return;
            }

            // Skip if hidden
            if (el.offsetParent === null && el.type !== 'file') {
                skippedReasons.hidden++;
                console.log(`${indent}[AutoFill] Skipping (hidden): ${el.tagName} ${el.type || ''}`);
                return;
            }

            // Skip file upload inputs
            if (el.type === 'file') {
                skippedReasons.fileInput++;
                console.log(`${indent}[AutoFill] Skipping (file input): ${el.tagName}`);
                return;
            }

            // Skip submit and reset inputs
            if (el.type === 'submit' || el.type === 'reset' || el.type === 'image') {
                skippedReasons.submitReset++;
                console.log(`${indent}[AutoFill] Skipping (submit/reset): ${el.tagName} type=${el.type}`);
                return;
            }

            // Skip dropdown control buttons (buttons that open/close dropdowns)
            if (el.tagName.toLowerCase() === 'button') {
                const controlsId = el.getAttribute('aria-controls');
                if (controlsId) {
                    const controlledElement = document.getElementById(controlsId);
                    // If button controls a listbox/menu, it's a dropdown button - skip it
                    if (controlledElement && controlledElement.getAttribute('role') === 'listbox') {
                        skippedReasons.actionButton++;
                        console.log(`${indent}[AutoFill] Skipping (dropdown button): controls ${controlsId}`);
                        return;
                    }
                }

                // Skip other action/navigation buttons (but keep choice buttons)
                if (isActionButton(el)) {
                    skippedReasons.actionButton++;
                    console.log(`${indent}[AutoFill] Skipping (action button): "${el.textContent.trim().substring(0, 30)}"`);
                    return;
                }
            }

            const hasValue = hasMeaningfulValue(el);
            let computedRole = (el.getAttribute('role') || '').toLowerCase() || getImplicitRole(el);
            const multiSelect = detectMultiSelect(el);
            if (shouldForceComboboxRole(el) || multiSelect) {
                computedRole = 'combobox';
            }

            const isCustomDropdown = (computedRole === 'combobox' || computedRole === 'listbox') &&
                el.tagName.toLowerCase() !== 'select';

            // Skip pre-filled fields (except buttons) BUT keep custom dropdowns (combobox/listbox)
            if (hasValue && el.type !== 'button' && !isCustomDropdown) {
                skippedReasons.preFilled++;
                console.log(`${indent}[AutoFill] Skipping (pre-filled): ${el.tagName} ${el.type || ''} value="${el.value.substring(0, 20)}"`);
                return;
            }

            // Get semantic info
            const { label: scoredLabel, score: labelScore } = findBestLabel(el);
            const needsContext = labelScore < 70;
            let contextSnippet = needsContext ? getSurroundingContext(el) : '';
            const groupLabel = getGroupLegendLabel(el);
            let optionLabel = '';
            const roleLower = (computedRole || '').toLowerCase();
            const isChoiceControl = ['radio', 'checkbox', 'option'].includes(roleLower) ||
                el.type === 'radio' || el.type === 'checkbox';
            if (isChoiceControl) {
                optionLabel = getChoiceOptionLabel(el);
                const normalizedGroup = normalizeText(groupLabel);
                if (optionLabel && normalizedGroup && normalizeText(optionLabel) === normalizedGroup) {
                    const fallbackValue = cleanText(
                        el.value ||
                        el.getAttribute('data-value') ||
                        el.getAttribute('aria-label') ||
                        ''
                    );
                    if (fallbackValue && normalizeText(fallbackValue) !== normalizedGroup) {
                        optionLabel = fallbackValue;
                    } else {
                        optionLabel = '';
                    }
                }
                if (!optionLabel && scoredLabel && (!normalizedGroup || normalizeText(scoredLabel) !== normalizedGroup)) {
                    optionLabel = scoredLabel;
                }
            }

            // SHADOW DOM HOST FIX:
            // If we're on a custom element host (has shadowRoot) and no name found,
            // try to get label from host's own attributes
            let computedName = scoredLabel;
            if ((!computedName || computedName === 'Unknown Field') && el.shadowRoot) {
                const shadowLabel = cleanText(
                    el.getAttribute('label') ||
                    el.getAttribute('placeholder') ||
                    el.getAttribute('aria-label') ||
                    ''
                );
                if (shadowLabel) {
                    computedName = shadowLabel;
                    console.log(`${indent}[AutoFill] Found label on Shadow DOM host: "${computedName}"`);
                }
            }

            if ((!computedName || computedName === 'Unknown Field') && contextSnippet) {
                console.log(`${indent}[AutoFill] Using context snippet for unlabeled field`);
            }

            if (!computedName && !contextSnippet) {
                skippedReasons.noLabel++;
                console.log(`${indent}[AutoFill] Skipping (no label/context): ${el.tagName} ${el.type || ''} id=${el.id || 'none'}`);
                return;
            }

            let finalLabel = computedName || contextSnippet || 'Unknown Field';
            if (groupLabel && isChoiceControl) {
                finalLabel = optionLabel
                    ? `${groupLabel} (${optionLabel})`
                    : groupLabel;
            }

            console.log(`${indent}[AutoFill] ✓ Found: ${computedRole} "${finalLabel}" (${el.tagName}${el.type ? ':' + el.type : ''})`);

            elements.push({
                tag: el.tagName.toLowerCase(),
                type: el.type || '',
                id: el.id || '',
                name: el.name || '',
                placeholder: el.placeholder || '',
                value: el.value || '',
                required: el.required || false,
                a11yRole: computedRole,
                a11yName: finalLabel,
                a11yDescription: getAccessibleDescription(el),
                context: contextSnippet || '',
                groupLabel: groupLabel || '',
                optionLabel: optionLabel || '',
                isMultiSelect: multiSelect,
                labelScore,
                element: el  // Store DOM reference
            });
        });

        // SHADOW DOM PIERCER:
        // Find ALL elements in this root and check if they have shadowRoot
        rootNode.querySelectorAll('*').forEach(el => {
            if (el.shadowRoot) {
                console.log(`${indent}[AutoFill] 🔍 Found Shadow DOM in: ${el.tagName.toLowerCase()}`);
                walkDOM(el.shadowRoot, depth + 1);  // Recurse into shadow root!
            }
        });
    }

    // Start the recursive walk from document body
    console.log('[AutoFill] ========== Starting Form Element Extraction ==========');
    walkDOM(document.body);

    console.log('[AutoFill] ========== Extraction Complete ==========');
    console.log(`[AutoFill] Total scanned: ${totalScanned}`);
    console.log(`[AutoFill] Found: ${elements.length}`);
    console.log(`[AutoFill] Skipped breakdown:`, skippedReasons);

    return elements;
}

/**
 * Build element registry and return serialized data for backend
 * Maps element IDs to actual DOM references
 * ENHANCED: Handles Shadow DOM - stores the REAL input inside custom elements
 */
function buildElementRegistry(elements) {
    elementRegistry.clear();

    elements.forEach((elementData, index) => {
        const id = `elem_${index}`;
        let domElementToStore = elementData.element;

        // SHADOW DOM FIX:
        // If element is a custom element host (has shadowRoot),
        // find the REAL input/textarea/select/button inside it
        if (elementData.element.shadowRoot) {
            const internalInput = elementData.element.shadowRoot.querySelector(
                'input, textarea, select, button'
            );
            if (internalInput) {
                console.log(`[AutoFill] Found internal input in ${elementData.element.tagName}: ${internalInput.tagName}:${internalInput.type || ''}`);
                domElementToStore = internalInput;  // Use the real input!
            } else {
                console.warn(`[AutoFill] Shadow DOM host has no internal form element: ${elementData.element.tagName}`);
            }
        }

        const selector = domElementToStore ? generateSelector(domElementToStore) : '';

        // Store the mapping
        elementRegistry.set(id, {
            domElement: domElementToStore,  // Now points to actual input (not host)
            a11yName: elementData.a11yName,
            a11yRole: elementData.a11yRole,
            context: elementData.context || '',
            groupLabel: elementData.groupLabel || '',
            optionLabel: elementData.optionLabel || '',
            multiSelect: Boolean(elementData.isMultiSelect),
            selector,
            // For serialization to backend
            serialized: {
                id: id,
                role: elementData.a11yRole,
                label: elementData.a11yName,
                type: elementData.type,
                required: elementData.required,
                currentValue: elementData.value,
                description: elementData.a11yDescription,
                context: elementData.context || '',
                groupLabel: elementData.groupLabel || '',
                optionLabel: elementData.optionLabel || '',
                multiSelect: Boolean(elementData.isMultiSelect),
                selector
            }
        });

        // Attach registry metadata back onto element data for later lookups
        elementData.elementId = id;
        elementData.domRef = domElementToStore;
        elementData.selector = selector;
    });

    return Array.from(elementRegistry.values()).map(v => v.serialized);
}

/**
 * Find label for an element using multiple strategies
 * DEPRECATED: Use getAccessibleName() instead for A11y approach
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

function normalizeText(text) {
    return cleanText(text || '').toLowerCase();
}

function escapeForAttribute(value) {
    if (!value) {
        return '';
    }
    if (window.CSS && typeof window.CSS.escape === 'function') {
        return window.CSS.escape(value);
    }
    return value.replace(/["\\]/g, '\\$&');
}

function textMatches(target, candidate) {
    const normalizedTarget = normalizeText(target);
    const normalizedCandidate = normalizeText(candidate);
    if (!normalizedTarget || !normalizedCandidate) {
        return false;
    }
    return normalizedTarget === normalizedCandidate ||
        normalizedCandidate.includes(normalizedTarget) ||
        normalizedTarget.includes(normalizedCandidate);
}

function isGenericPlaceholder(text) {
    const normalized = normalizeText(text);
    if (!normalized) {
        return false;
    }
    return GENERIC_PLACEHOLDER_PATTERNS.some(pattern => pattern.test(normalized));
}

function getBooleanCategory(value) {
    const normalized = normalizeText(value);
    if (!normalized) {
        return null;
    }
    if (YES_VALUE_SET.has(normalized)) {
        return 'yes';
    }
    if (NO_VALUE_SET.has(normalized)) {
        return 'no';
    }
    return null;
}

function hasMeaningfulValue(element) {
    if (!element || element.type === 'button') {
        return false;
    }

    const controlType = (element.type || element.getAttribute('type') || '').toLowerCase();
    if (controlType === 'checkbox' || controlType === 'radio') {
        return false;
    }

    const tag = element.tagName.toLowerCase();
    const rawValue = element.value ?? '';

    if (!rawValue.trim()) {
        return false;
    }

    if (isGenericPlaceholder(rawValue)) {
        return false;
    }

    if (tag === 'select') {
        const selectedOption = element.options?.[element.selectedIndex];
        if (selectedOption) {
            const optionText = cleanText(selectedOption.textContent || '');
            if (!optionText) {
                return false;
            }
            if (isGenericPlaceholder(optionText) || isGenericPlaceholder(selectedOption.value)) {
                return false;
            }
        }
    }

    return true;
}

function shouldForceComboboxRole(element) {
    if (!element) {
        return false;
    }

    const explicitRole = (element.getAttribute('role') || '').toLowerCase();
    if (explicitRole === 'combobox' || explicitRole === 'listbox') {
        return true;
    }

    const tag = element.tagName?.toLowerCase();
    if (tag === 'select') {
        return false;
    }

    const ariaHasPopup = (element.getAttribute('aria-haspopup') || '').toLowerCase();
    if (ariaHasPopup === 'listbox' || ariaHasPopup === 'tree') {
        return true;
    }

    const ariaAutocomplete = (element.getAttribute('aria-autocomplete') || '').toLowerCase();
    if (ariaAutocomplete === 'list' || ariaAutocomplete === 'both') {
        return true;
    }

    const ariaControls = element.getAttribute('aria-controls');
    if (ariaControls) {
        const controlled = document.getElementById(ariaControls);
        if (controlled) {
            const controlledRole = (controlled.getAttribute('role') || '').toLowerCase();
            if (controlledRole === 'listbox' || controlledRole === 'tree') {
                return true;
            }
        }
    }

    const automationId = (element.getAttribute('data-automation-id') || '').toLowerCase();
    if (automationId.includes('multiselect') || automationId.includes('select') || automationId.includes('autocomplete')) {
        return true;
    }

    return false;
}

function detectMultiSelect(element) {
    if (!element) {
        return false;
    }

    if (element.tagName?.toLowerCase() === 'select' && element.multiple) {
        return true;
    }

    if ((element.getAttribute('aria-multiselectable') || '').toLowerCase() === 'true') {
        return true;
    }

    const automationId = (element.getAttribute('data-automation-id') || '').toLowerCase();
    if (automationId.includes('multiselect')) {
        return true;
    }

    const ownerId = element.getAttribute('aria-owns') || element.getAttribute('aria-controls');
    if (ownerId) {
        const ownedNode = document.getElementById(ownerId);
        if (ownedNode && (ownedNode.getAttribute('aria-multiselectable') || '').toLowerCase() === 'true') {
            return true;
        }
    }

    const multiselectContainer = element.closest('[aria-multiselectable="true"], [data-automation-id*="multiSelect"]');
    return Boolean(multiselectContainer);
}

function getGroupLegendLabel(element) {
    if (!element) {
        return '';
    }

    const fieldset = element.closest('fieldset');
    if (fieldset) {
        const legend = fieldset.querySelector('legend');
        const legendText = cleanText(legend?.textContent || '');
        if (legendText) {
            return legendText;
        }
    }

    const ariaGroup = element.closest('[role="group"], [role="radiogroup"], [data-automation-id*="group"]');
    if (ariaGroup) {
        const ariaLabel = cleanText(ariaGroup.getAttribute('aria-label') || '');
        if (ariaLabel) {
            return ariaLabel;
        }

        const labelledBy = ariaGroup.getAttribute('aria-labelledby');
        if (labelledBy) {
            const ids = labelledBy.split(/\s+/);
            for (const id of ids) {
                const labelNode = document.getElementById(id);
                const nodeText = cleanText(labelNode?.textContent || '');
                if (nodeText) {
                    return nodeText;
                }
            }
        }

        const groupLegend = ariaGroup.querySelector('legend');
        const groupLegendText = cleanText(groupLegend?.textContent || '');
        if (groupLegendText) {
            return groupLegendText;
        }
    }

    const wrapper = element.closest('[class*="question"], [class*="form-group"], [data-testid*="question"], [data-test*="question"]');
    if (wrapper) {
        const heading = wrapper.querySelector('legend, h2, h3, .question-label, [data-test*="label"]');
        const headingText = cleanText(heading?.textContent || '');
        if (headingText) {
            return headingText;
        }
    }

    return '';
}

function getChoiceOptionLabel(element) {
    if (!element) {
        return '';
    }

    const wrappedLabel = element.closest('label');
    if (wrappedLabel) {
        const text = cleanText(wrappedLabel.textContent || '');
        if (text) {
            return text;
        }
    }

    if (element.id) {
        const explicitLabel = document.querySelector(`label[for="${element.id}"]`);
        const text = cleanText(explicitLabel?.textContent || '');
        if (text) {
            return text;
        }
    }

    const ariaLabel = cleanText(element.getAttribute('aria-label') || '');
    if (ariaLabel) {
        return ariaLabel;
    }

    const labelledBy = element.getAttribute('aria-labelledby');
    if (labelledBy) {
        const ids = labelledBy.split(/\s+/);
        for (const id of ids) {
            const labelEl = document.getElementById(id);
            const text = cleanText(labelEl?.textContent || '');
            if (text) {
                return text;
            }
        }
    }

    const sibling = element.nextElementSibling;
    if (sibling) {
        const text = cleanText(sibling.textContent || '');
        if (text) {
            return text;
        }
    }

    const prev = element.previousElementSibling;
    if (prev) {
        const text = cleanText(prev.textContent || '');
        if (text) {
            return text;
        }
    }

    const dataValue = element.getAttribute('data-value') ||
        element.getAttribute('data-text') ||
        element.getAttribute('value');
    if (dataValue) {
        return cleanText(dataValue);
    }

    return '';
}

function isNodeVisible(node) {
    if (!node) {
        return false;
    }
    if (node.offsetParent !== null) {
        return true;
    }
    const rect = node.getBoundingClientRect?.();
    return Boolean(rect && rect.width > 0 && rect.height > 0);
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
 * Execute actions returned by LLM (using element registry)
 * ENHANCED: Awaits popup decisions to prevent stacking
 */
async function executeActions(actions) {
    for (const action of actions) {
        // Show popup for low confidence actions - WAIT for user decision
        if (action.confidence === 'low') {
            const decision = await showUserPrompt(action);

            if (decision.type === 'skip') {
                continue; // User skipped, move to next action
            }

            // Execute based on user's choice
            if (decision.targetElement && decision.role) {
                await executeManualAction(
                    decision.targetElement,
                    decision.value,
                    action.interaction,
                    decision.role
                );
            }

            // Save to memory if requested
            if (decision.type === 'save-global' && decision.label) {
                saveAnswer(decision.label, decision.value, 'global');
            } else if (decision.type === 'save-company' && decision.label) {
                saveAnswer(decision.label, decision.value, 'company');
            }

            continue; // Move to next action
        }

        // High confidence - execute automatically
        try {
            const elementData = await ensureLiveElementData(action);
            if (!elementData) {
                continue;
            }

            const element = elementData.domElement;
            const role = elementData.a11yRole;

            console.log(`[AutoFill] Executing: ${action.label} (role: ${role}, value: ${action.value})`);

            // Execute based on interaction type (more robust than role-based)
            if (action.interaction === 'fill_text') {
                setNativeValue(element, action.value ?? '');
                console.log(`✓ Filled: ${action.label}`);
            }
            else if (action.interaction === 'select_option') {
                // Validate it's actually a select element
                if (element.tagName.toLowerCase() === 'select') {
                    await selectOption(element, action.value, action.label);
                } else {
                    console.warn(`[AutoFill] select_option called on ${element.tagName}, treating as fill_text`);
                    setNativeValue(element, action.value ?? '');
                }
            }
            else if (action.interaction === 'check') {
                const shouldCheck = action.value === 'true' || action.value.toLowerCase() === 'yes' || action.value === '1' || action.value === true;
                element.checked = shouldCheck;
                element.dispatchEvent(new Event('change', { bubbles: true }));
                element.dispatchEvent(new Event('click', { bubbles: true }));
                console.log(`✓ ${shouldCheck ? 'Checked' : 'Unchecked'}: ${action.label}`);
            }
            else if (action.interaction === 'click') {
                clickElement(element, action.value, action.label);
            }
            else {
                console.warn(`[AutoFill] Unhandled interaction: ${action.interaction} for ${action.label}`);
            }

            await new Promise(resolve => setTimeout(resolve, 50));

        } catch (error) {
            console.error(`[AutoFill] Error: ${action.label}:`, error);
        }
    }
}

function focusAndOpenDropdown(element) {
    try {
        element.focus?.();
        element.click?.();
        element.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
        element.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
        element.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true }));
    } catch (err) {
        console.warn('[AutoFill] Failed to open dropdown via element interactions', err);
    }

    const toggleSelectors = [
        'button[aria-haspopup="listbox"]',
        'button[aria-expanded]',
        '[role="button"][aria-haspopup="listbox"]',
        '.select-arrow',
        '.ant-select-arrow',
        '.MuiSelect-icon',
        '.chakra-select__icon'
    ];

    const immediateToggle = element.nextElementSibling && toggleSelectors.some(sel => element.nextElementSibling.matches(sel))
        ? element.nextElementSibling
        : null;

    let toggle = immediateToggle;
    if (!toggle) {
        const wrapper = element.closest('[role="combobox"], .select, .dropdown, [class*="select"], [class*="Dropdown"]');
        if (wrapper) {
            toggle = toggleSelectors
                .map(sel => wrapper.querySelector(sel))
                .find(Boolean);
        }
    }

    if (toggle && toggle !== element) {
        toggle.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
        toggle.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
        toggle.click();
    }
}

function getVisibleOptionNodes(root = document) {
    const nodes = new Set();
    DROPDOWN_OPTION_SELECTORS.forEach(selector => {
        root.querySelectorAll(selector).forEach(node => {
            if (isNodeVisible(node)) {
                nodes.add(node);
            }
        });
    });
    return Array.from(nodes);
}

function collectOptionNodes() {
    return getVisibleOptionNodes(document);
}

function buildOptionDescriptor(node) {
    const text = cleanText(
        node.getAttribute('data-display') ||
        node.getAttribute('data-text') ||
        node.getAttribute('aria-label') ||
        node.textContent ||
        ''
    );
    const value = cleanText(
        node.getAttribute('data-value') ||
        node.getAttribute('data-id') ||
        node.getAttribute('data-option-value') ||
        text
    );

    return {
        element: node,
        text: text || value,
        value: value || text
    };
}

function findMatchingOptionNode(targetText) {
    const normalizedTarget = cleanText(targetText || '').toLowerCase();
    if (!normalizedTarget) {
        return null;
    }

    return collectOptionNodes().find(node => {
        const candidates = [
            node.getAttribute('data-text'),
            node.getAttribute('data-display'),
            node.getAttribute('data-value'),
            node.getAttribute('aria-label'),
            node.textContent
        ].map(value => cleanText(value || '').toLowerCase()).filter(Boolean);

        if (candidates.length === 0) {
            return false;
        }

        return candidates.some(text => text === normalizedTarget || text.includes(normalizedTarget) || normalizedTarget.includes(text));
    }) || null;
}

function getRadioGroupElements(element) {
    if (!element) {
        return [];
    }

    if (element.type === 'radio' && element.name) {
        const escapedName = escapeForAttribute(element.name);
        if (escapedName) {
            return Array.from(document.querySelectorAll(`input[type="radio"][name="${escapedName}"]`));
        }
    }

    const group = element.closest?.('[role="radiogroup"], [role="group"], [data-testid*="radio"], [data-test*="radio"]');
    if (group) {
        const radios = group.querySelectorAll('input[type="radio"], [role="radio"]');
        if (radios.length > 0) {
            return Array.from(radios);
        }
    }

    if (element.type === 'radio' || element.getAttribute?.('role') === 'radio') {
        return [element];
    }

    return [];
}

function getRadioCandidateTexts(radio) {
    if (!radio) {
        return [];
    }

    const texts = [];
    const attributeSources = ['aria-label', 'data-label', 'data-value', 'data-text', 'title'];
    attributeSources.forEach(attr => {
        const value = radio.getAttribute?.(attr);
        if (value) {
            texts.push(value);
        }
    });

    const attrValue = radio.getAttribute?.('value') ?? radio.value;
    if (attrValue) {
        texts.push(attrValue);
    }

    if (radio.id) {
        const explicitLabel = document.querySelector(`label[for="${radio.id}"]`);
        if (explicitLabel) {
            texts.push(explicitLabel.textContent);
        }
    }

    const wrappingLabel = radio.closest?.('label');
    if (wrappingLabel) {
        texts.push(wrappingLabel.textContent);
    }

    if (radio.textContent) {
        texts.push(radio.textContent);
    }

    if (radio.nextElementSibling) {
        texts.push(radio.nextElementSibling.textContent);
    }

    return texts.map(cleanText).filter(Boolean);
}

function findMatchingRadioOption(element, targetValue) {
    const normalizedTarget = normalizeText(targetValue);
    if (!element || !normalizedTarget) {
        return null;
    }

    const desiredBoolean = getBooleanCategory(targetValue);
    const candidates = getRadioGroupElements(element);

    for (const candidate of candidates) {
        const texts = getRadioCandidateTexts(candidate);
        if (texts.some(text => textMatches(targetValue, text))) {
            return candidate;
        }

        if (desiredBoolean) {
            const candidateBoolean = getBooleanCategory(candidate.getAttribute?.('data-value')) ||
                getBooleanCategory(candidate.value) ||
                texts.map(getBooleanCategory).find(Boolean);
            if (candidateBoolean && candidateBoolean === desiredBoolean) {
                return candidate;
            }
        }
    }

    return null;
}

async function waitForDropdownOption(targetText, timeout = 2500) {
    const immediate = findMatchingOptionNode(targetText);
    if (immediate) {
        return immediate;
    }

    return new Promise(resolve => {
        const start = Date.now();
        const observer = new MutationObserver(() => {
            const match = findMatchingOptionNode(targetText);
            if (match) {
                observer.disconnect();
                clearInterval(pollInterval);
                resolve(match);
            }
        });

        observer.observe(document.body, { childList: true, subtree: true });

        const pollInterval = setInterval(() => {
            const match = findMatchingOptionNode(targetText);
            if (match) {
                observer.disconnect();
                clearInterval(pollInterval);
                resolve(match);
            } else if (Date.now() - start > timeout) {
                observer.disconnect();
                clearInterval(pollInterval);
                resolve(null);
            }
        }, 120);
    });
}

async function universalDropdownFill(element, value, label) {
    const targetText = (value || '').trim();
    focusAndOpenDropdown(element);

    const typingTarget = element.matches('input, textarea')
        ? element
        : element.querySelector?.('input, textarea');

    if (typingTarget && targetText) {
        setNativeValue(typingTarget, targetText);
    } else if (targetText && element.isContentEditable) {
        element.textContent = targetText;
    }

    const optionNode = await waitForDropdownOption(targetText);
    if (optionNode) {
        clickElement(optionNode, targetText, label || targetText);
        return true;
    }

    console.warn(`[AutoFill] universalDropdownFill: Option "${targetText}" not found for ${label}`);
    return false;
}

/**
 * Select option in dropdown (helper function)
 * ENHANCED: Handles native <select>, datalist, and custom combobox/listbox
 */
async function selectOption(element, value, label) {
    const tagName = element.tagName.toLowerCase();

    // Case 1: Native <select> dropdown
    if (tagName === 'select') {
        const options = Array.from(element.options);
        let match = null;

        // 1. Exact match
        match = options.find(opt => opt.text.toLowerCase() === value.toLowerCase());

        // 2. Value contains option
        if (!match) {
            match = options.find(opt => value.toLowerCase().includes(opt.text.toLowerCase()));
        }

        // 3. Option contains value
        if (!match) {
            match = options.find(opt => opt.text.toLowerCase().includes(value.toLowerCase()));
        }

        // 4. Word-level matching
        if (!match) {
            const valueWords = value.toLowerCase().split(/\s+/);
            match = options.find(opt => {
                const optWords = opt.text.toLowerCase().split(/\s+/);
                return valueWords.some(vw => optWords.some(ow => ow.includes(vw) || vw.includes(ow)));
            });
        }

        if (match) {
            setNativeValue(element, match.value);
            console.log(`✓ Selected: ${label} = ${match.text}`);
        } else {
            console.warn(`[AutoFill] No matching option for: ${label} = "${value}"`);
            console.warn(`Available: ${options.map(o => o.text).join(', ')}`);
        }
        return;
    }

    // Case 2: Input with datalist
    if (tagName === 'input' && element.hasAttribute('list')) {
        setNativeValue(element, value ?? '');
        console.log(`✓ Filled datalist: ${label} = ${value}`);
        return;
    }

    // Case 3: Custom dropdowns / combos
    const success = await universalDropdownFill(element, value, label);
    if (!success) {
        setNativeValue(element, value ?? '');
    }
}

/**
 * Click element (helper function)
 */
function clickElement(element, value, label) {
    // For radio buttons, try to find the specific option by value
    if (element.type === 'radio') {
        const targetRadio = findMatchingRadioOption(element, value);
        if (targetRadio) {
            element = targetRadio;
        }
    } else if (element.getAttribute && element.getAttribute('role') === 'radio') {
        const targetRadio = findMatchingRadioOption(element, value);
        if (targetRadio) {
            element = targetRadio;
        }
    }

    // For choice buttons, find the specific button by text
    if (element.tagName.toLowerCase() === 'button' && isChoiceButton(element)) {
        const buttonText = element.textContent.trim().toLowerCase();
        const targetValue = value.toLowerCase();

        if (buttonText !== targetValue) {
            const parent = element.closest('[role="radiogroup"], [role="list"], [role="group"]');
            if (parent) {
                const buttons = parent.querySelectorAll('button');
                for (const btn of buttons) {
                    if (btn.textContent.trim().toLowerCase() === targetValue) {
                        element = btn;
                        break;
                    }
                }
            }
        }
    }

    // Execute click with multiple methods
    element.click();
    element.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
    element.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
    element.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    element.dispatchEvent(new Event('change', { bubbles: true }));
    element.focus();
    element.dispatchEvent(new Event('focus', { bubbles: true }));

    // Special handling for dropdown options - update hidden postback field
    // Many custom dropdowns use a hidden field with -postback suffix
    if (element.getAttribute('role') === 'option') {
        const optionValue = element.getAttribute('data-value') || element.textContent.trim();

        // Try to find the parent combobox and its postback field
        const listbox = element.closest('[role="listbox"]');
        if (listbox) {
            const listboxId = listbox.id; // e.g., "sTitle-list"
            const baseId = listboxId.replace('-list', ''); // e.g., "sTitle"
            const postbackField = document.getElementById(`${baseId}-postback`);

            if (postbackField) {
                setNativeValue(postbackField, optionValue);
                console.log(`✓ Updated postback field ${baseId}-postback = "${optionValue}"`);
            }

            // Also update the display input
            const displayInput = document.getElementById(`${baseId}-edit`);
            if (displayInput) {
                setNativeValue(displayInput, element.textContent.trim());
            }
        }
    }

    console.log(`✓ Clicked: ${label} = ${value}`);
}

/**
 * DEPRECATED - OLD Execute actions function
 * Kept for reference only - use registry-based version above
 */
async function executeActionsOld(actions) {
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
                    setNativeValue(element, action.value ?? '');
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
                            setNativeValue(element, match.value);
                            console.log(`✓ Selected: ${action.label} = ${match.text}`);
                        } else {
                            console.warn(`[AutoFill Agent] No matching option for: ${action.label} = "${action.value}"`);
                            console.warn(`Available: ${options.map(o => o.text).join(', ')}`);
                            showUserPrompt(action);
                        }
                    } else if (element.tagName === 'INPUT' && element.hasAttribute('list')) {
                        // Input with datalist
                        setNativeValue(element, action.value ?? '');
                        console.log(`✓ Filled datalist: ${action.label} = ${action.value}`);
                    } else {
                        // Custom dropdown fallback
                        setNativeValue(element, action.value ?? '');
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
 * ENHANCED: Returns Promise, generates dynamic input, prevents stacking
 */
function showUserPrompt(action) {
    return new Promise((resolve) => {
        const elementData = elementRegistry.get(action.elementId);
        let targetElement = null;

        if (elementData) {
            targetElement = elementData.domElement;
        } else {
            console.warn(`[AutoFill] Element not found in registry: ${action.elementId}`);
        }

        const role = elementData?.a11yRole;
        const companyName = extractCompanyName();

        // Generate dynamic input based on element type
        let inputHtml = '';
        let getValueFunction = null;

        // Check if it's a native <select> element (regardless of role)
        if (targetElement?.tagName.toLowerCase() === 'select') {
            // Native <select> dropdown - show actual dropdown in popup
            console.log(`[AutoFill] Creating dropdown popup for: ${action.label}`);
            inputHtml = '<select id="user-input" style="width: 100%; padding: 8px; border: 2px solid #ddd; border-radius: 4px; font-size: 13px;">';
            const options = targetElement.querySelectorAll('option');
            let hasOptions = false;
            options.forEach(opt => {
                if (opt.value || opt.text.trim()) {
                    hasOptions = true;
                    const selected = opt.value === action.value || opt.text === action.value ? 'selected' : '';
                    inputHtml += `<option value="${opt.value}" ${selected}>${opt.text}</option>`;
                }
            });
            inputHtml += '</select>';

            if (!hasOptions) {
                // Fallback to text input if no options found
                console.warn(`[AutoFill] No options found in select, using text input`);
                inputHtml = `<input type="text" id="user-input" value="${action.value || ''}" placeholder="Enter value..." style="width: 100%; padding: 8px; border: 2px solid #ddd; border-radius: 4px; font-size: 13px; box-sizing: border-box;">`;
            }
            getValueFunction = (popup) => popup.querySelector('#user-input').value;
        }
        else if (role === 'radio' && targetElement?.type === 'radio') {
            // Radio button group - show radio buttons in popup
            console.log(`[AutoFill] Creating radio popup for: ${action.label}`);
            inputHtml = '<div id="user-input" style="border: 1px solid #ddd; padding: 8px; border-radius: 4px; max-height: 180px; overflow-y: auto;">';
            const radioGroup = document.querySelectorAll(`input[type="radio"][name="${targetElement.name}"]`);
            radioGroup.forEach(radio => {
                const radioLabel = getAccessibleName(radio) || radio.value;
                const checked = radio.value === action.value ? 'checked' : '';
                inputHtml += `
                    <label style="display: block; margin-bottom: 6px; cursor: pointer;">
                        <input type="radio" name="popup-radio" value="${radio.value}" ${checked} style="margin-right: 6px;">
                        <span style="font-size: 13px;">${radioLabel}</span>
                    </label>
                `;
            });
            inputHtml += '</div>';
            getValueFunction = (popup) => {
                const checked = popup.querySelector('input[name="popup-radio"]:checked');
                return checked ? checked.value : '';
            };
        }
        else {
            // Default: text input
            console.log(`[AutoFill] Creating text input popup for: ${action.label} (role: ${role})`);
            inputHtml = `<input type="text" id="user-input" value="${action.value || ''}" placeholder="Enter value..." style="width: 100%; padding: 8px; border: 2px solid #ddd; border-radius: 4px; font-size: 13px; box-sizing: border-box;">`;
            getValueFunction = (popup) => popup.querySelector('#user-input').value;
        }

        // Create tooltip-style popup (compact and unobtrusive)
        const popup = document.createElement('div');
        popup.id = `autofill-popup-${action.label.replace(/\s+/g, '-')}`;
        popup.style.cssText = `
            position: fixed;
            z-index: 999999;
            background: white;
            padding: 12px;
            border-radius: 6px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.25);
            min-width: 250px;
            max-width: 320px;
            border: 1px solid #667eea;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        `;

        popup.innerHTML = `
            <div style="margin: 0 0 8px 0; font-size: 13px; font-weight: 600; color: #333;">${action.label}</div>
            ${action.reasoning ? `<div style="margin: 0 0 8px 0; color: #888; font-size: 11px;">${action.reasoning}</div>` : ''}
            ${inputHtml}
            <div style="display: flex; gap: 4px; margin-top: 8px;">
                <button id="fill-once" style="
                    flex: 1;
                    padding: 6px 8px;
                    background: #22c55e;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 11px;
                    font-weight: 600;
                ">Fill</button>
                <button id="save-global" style="
                    flex: 1;
                    padding: 6px 8px;
                    background: #667eea;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 11px;
                    font-weight: 600;
                ">Save All</button>
                <button id="skip" style="
                    padding: 6px 8px;
                    background: #f3f4f6;
                    color: #666;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 11px;
                ">Skip</button>
            </div>
            <details style="margin-top: 6px;">
                <summary style="cursor: pointer; font-size: 10px; color: #888; user-select: none;">More options</summary>
                <button id="save-company" style="
                    width: 100%;
                    margin-top: 4px;
                    padding: 6px 8px;
                    background: #f093fb;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 11px;
                    font-weight: 600;
                ">Save for ${companyName}</button>
            </details>
        `;

        document.body.appendChild(popup);

        // Position tooltip-style popup near the field
        if (targetElement) {
            const rect = targetElement.getBoundingClientRect();
            const popupHeight = 180; // Smaller estimate for tooltip
            const popupWidth = 280;

            let top = rect.bottom + 8;
            let left = rect.left;

            const spaceBelow = window.innerHeight - rect.bottom;
            if (spaceBelow < popupHeight && rect.top > spaceBelow) {
                top = rect.top - popupHeight - 8;
            }

            if (left + popupWidth > window.innerWidth) {
                left = window.innerWidth - popupWidth - 10;
            }

            top = Math.max(10, Math.min(top, window.innerHeight - popupHeight - 10));
            left = Math.max(10, left);

            popup.style.top = `${top}px`;
            popup.style.left = `${left}px`;

            targetElement.style.outline = '2px solid #667eea';
            targetElement.style.outlineOffset = '1px';
            targetElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        } else {
            popup.style.top = '50%';
            popup.style.left = '50%';
            popup.style.transform = 'translate(-50%, -50%)';
        }

        // Focus input
        setTimeout(() => {
            const firstInput = popup.querySelector('#user-input input, #user-input, select');
            if (firstInput) firstInput.focus();
        }, 100);

        // Cleanup and resolve function
        const cleanupAndResolve = (decision) => {
            popup.remove();
            if (targetElement) {
                targetElement.style.outline = '';
                targetElement.style.outlineOffset = '';
            }
            document.removeEventListener('keydown', escapeHandler);
            resolve(decision);
        };

        // Button handlers
        popup.querySelector('#fill-once').addEventListener('click', () => {
            const answer = getValueFunction(popup);
            cleanupAndResolve({
                type: 'fill-once',
                value: answer || action.value || '',
                targetElement: targetElement,
                role: role
            });
        });

        popup.querySelector('#save-global').addEventListener('click', () => {
            const answer = getValueFunction(popup);
            cleanupAndResolve({
                type: 'save-global',
                value: answer || action.value || '',
                targetElement: targetElement,
                role: role,
                label: action.label
            });
        });

        popup.querySelector('#save-company').addEventListener('click', () => {
            const answer = getValueFunction(popup);
            cleanupAndResolve({
                type: 'save-company',
                value: answer || action.value || '',
                targetElement: targetElement,
                role: role,
                label: action.label
            });
        });

        popup.querySelector('#skip').addEventListener('click', () => {
            cleanupAndResolve({ type: 'skip' });
        });

        // Escape key
        const escapeHandler = (e) => {
            if (e.key === 'Escape') {
                cleanupAndResolve({ type: 'skip' });
            }
        };
        document.addEventListener('keydown', escapeHandler);
    });
}

/**
 * Execute action manually from user prompt popup (using element directly)
 */
function executeManualAction(element, value, interaction, role) {
    try {
        console.log(`[AutoFill] Executing manual action: ${interaction} with value: ${value}`);

        if (role === 'textbox' || role === 'searchbox' || role === 'spinbutton') {
            setNativeValue(element, value ?? '');
            console.log(`✓ Filled: ${value}`);
        }
        else if (role === 'combobox' || role === 'listbox') {
            selectOption(element, value, '(manual)');
        }
        else if (role === 'checkbox' || role === 'switch') {
            const shouldCheck = value === 'true' || value.toLowerCase() === 'yes' || value === '1' || value === true;
            element.checked = shouldCheck;
            element.dispatchEvent(new Event('change', { bubbles: true }));
            element.dispatchEvent(new Event('click', { bubbles: true }));
            console.log(`✓ ${shouldCheck ? 'Checked' : 'Unchecked'}`);
        }
        else if (role === 'button' || role === 'radio') {
            clickElement(element, value, '(manual)');
        }
        else {
            console.warn(`[AutoFill] Unknown role for manual action: ${role}`);
        }
    } catch (error) {
        console.error('[AutoFill] Error in manual action:', error);
    }
}

/**
 * DEPRECATED: Try to fill field with value (improved for all field types)
 * Use executeManualAction instead for registry-based approach
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

/**
 * Observe DOM mutations and inject the button once a form/input appears
 */
function startAutoFillButtonObserver() {
    const targetSelectors = [
        'form',
        'input:not([type="hidden"])',
        'textarea',
        'select',
        '[role="textbox"]',
        '[role="combobox"]',
        '[role="listbox"]'
    ].join(',');

    const maybeInject = () => {
        if (autoFillButton || (window.location.hostname === 'localhost' && window.location.port === '5173')) {
            return true;
        }

        if (!document.body) {
            return false;
        }

        const hasFormControls = document.querySelector(targetSelectors);
        if (hasFormControls) {
            injectAutoFillButton();
            return true;
        }

        return false;
    };

    if (maybeInject()) {
        return;
    }

    const observer = new MutationObserver(() => {
        if (maybeInject()) {
            observer.disconnect();
        }
    });

    const startObserving = () => {
        if (!document.body) {
            return false;
        }
        observer.observe(document.body, { childList: true, subtree: true });
        return true;
    };

    if (!startObserving()) {
        document.addEventListener('DOMContentLoaded', () => {
            if (!maybeInject()) {
                startObserving();
            }
        });
    }
}

startAutoFillButtonObserver();

// Listen for messages from background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'scrapeCurrentPage') {
        handleAutoFillClick();
        sendResponse({ success: true });
    }
    return true;
});
