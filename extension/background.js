// Background service worker for API communication
// Handles all API requests to the backend

// Load config (note: can't use imports in service worker yet)
const CONFIG = {
    API_BASE_URL: 'http://localhost:8000',
    API_ENDPOINTS: {
        ANALYZE_FORM: '/api/autofill/analyze-form',  // NEW LLM-based endpoint
        ANALYZE_FIELDS: '/api/autofill/analyze-fields',  // OLD (deprecated)
        SAVE_ANSWER: '/api/autofill/save-answer',
        GET_MEMORY: '/api/autofill/memory'
    }
};

/**
 * Get auth token from storage
 */
async function getAuthToken() {
    const result = await chrome.storage.local.get(['authToken']);
    return result.authToken || null;
}

/**
 * Save auth token to storage
 */
async function saveAuthToken(token) {
    await chrome.storage.local.set({ authToken: token });
}

/**
 * Make API request with auth
 */
async function apiRequest(endpoint, method = 'GET', body = null) {
    const token = await getAuthToken();

    if (!token) {
        throw new Error('Not authenticated. Please log in first.');
    }

    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        }
    };

    if (body) {
        options.body = JSON.stringify(body);
    }

    const url = `${CONFIG.API_BASE_URL}${endpoint}`;
    console.log(`[Background] API Request: ${method} ${url}`);

    const response = await fetch(url, options);

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return await response.json();
}

/**
 * Analyze form elements (NEW structured extraction approach)
 */
async function analyzeForm(elements, url, companyName) {
    return await apiRequest(CONFIG.API_ENDPOINTS.ANALYZE_FORM, 'POST', {
        elements,  // Send structured element list
        url,
        company_name: companyName
    });
}

/**
 * Analyze form fields (OLD approach - deprecated)
 */
async function analyzeFields(url, fields, companyName) {
    return await apiRequest(CONFIG.API_ENDPOINTS.ANALYZE_FIELDS, 'POST', {
        url,
        company_name: companyName,
        fields
    });
}

/**
 * Save user answer
 */
async function saveAnswer(data) {
    return await apiRequest(CONFIG.API_ENDPOINTS.SAVE_ANSWER, 'POST', data);
}

/**
 * Get user memory
 */
async function getUserMemory(companyName = null) {
    let url = CONFIG.API_ENDPOINTS.GET_MEMORY;
    if (companyName) {
        url += `?company_name=${encodeURIComponent(companyName)}`;
    }
    return await apiRequest(url, 'GET');
}

/**
 * Listen for messages from content script and popup
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log('[Background] Received message:', message.action);

    if (message.action === 'startAutoFill') {
        // Handle auto-fill trigger from web page
        const url = message.url;
        // Open current tab with the URL and trigger auto-fill
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (tabs[0]) {
                chrome.tabs.update(tabs[0].id, { url: url }, () => {
                    // Wait for page load then scrape
                    setTimeout(() => {
                        chrome.tabs.sendMessage(tabs[0].id, { action: 'scrapeFields' }, (response) => {
                            if (response && response.fields) {
                                // Trigger field analysis
                                analyzeFields(url, response.fields, null)
                                    .then(result => {
                                        chrome.tabs.sendMessage(tabs[0].id, {
                                            action: 'fillFields',
                                            strategies: result.result.strategies
                                        });
                                    });
                            }
                        });
                    }, 2000);
                });
            }
        });
        sendResponse({ success: true });
        return true;
    }

    if (message.action === 'setAuthToken') {
        saveAuthToken(message.token)
            .then(() => sendResponse({ success: true }))
            .catch(error => sendResponse({ success: false, error: error.message }));
        return true;
    }

    if (message.action === 'analyzeForm') {
        // NEW structured extraction approach
        console.log('[Background] Analyzing form elements:', {
            url: message.url,
            elementCount: message.elements?.length,
            companyName: message.companyName
        });

        analyzeForm(message.elements, message.url, message.companyName)
            .then(result => {
                console.log('[Background] Analysis success:', result);
                sendResponse({ success: true, actions: result.actions });
            })
            .catch(error => {
                console.error('[Background] Analysis error:', error);
                sendResponse({ success: false, error: error.message });
            });
        return true;
    }

    if (message.action === 'analyzeFields') {
        // OLD approach (deprecated but kept for backward compatibility)
        console.log('[Background] Analyzing fields:', {
            url: message.url,
            fieldCount: message.fields?.length,
            companyName: message.companyName
        });

        analyzeFields(message.url, message.fields, message.companyName)
            .then(result => {
                console.log('[Background] Analysis success:', result);
                sendResponse({ success: true, result });
            })
            .catch(error => {
                console.error('[Background] Analysis error:', error);
                console.error('[Background] Error details:', {
                    message: error.message,
                    stack: error.stack
                });
                sendResponse({ success: false, error: error.message });
            });
        return true;
    }

    if (message.action === 'saveAnswer') {
        saveAnswer(message.data)
            .then(result => sendResponse({ success: true, result }))
            .catch(error => sendResponse({ success: false, error: error.message }));
        return true;
    }

    if (message.action === 'getMemory') {
        getUserMemory(message.companyName)
            .then(result => sendResponse({ success: true, result }))
            .catch(error => sendResponse({ success: false, error: error.message }));
        return true;
    }

    if (message.action === 'scrapeCurrentPage') {
        // Forward to content script in the active tab
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (tabs[0]) {
                chrome.tabs.sendMessage(tabs[0].id, {
                    action: 'scrapeCurrentPage'
                }, (response) => {
                    if (response && response.success) {
                        sendResponse({ success: true });
                    } else {
                        sendResponse({ success: false, reason: response?.reason });
                    }
                });
            } else {
                sendResponse({ success: false, reason: 'no_tab' });
            }
        });
        return true;
    }

    return true;
});

console.log('[Background] Service worker loaded');

