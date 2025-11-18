// Popup script for extension UI

let isAuthenticated = false;

/**
 * Initialize popup
 */
async function init() {
    // Check if already authenticated
    const result = await chrome.storage.local.get(['authToken']);
    if (result.authToken) {
        isAuthenticated = true;
        showMainSection();
    }

    // Event listeners
    document.getElementById('loginBtn').addEventListener('click', handleLogin);
    document.getElementById('startBtn').addEventListener('click', handleStartAutoFill);
    document.getElementById('viewMemoryBtn').addEventListener('click', handleViewMemory);
}

/**
 * Show status message
 */
function showStatus(message, type = 'info') {
    const statusEl = document.getElementById('status');
    statusEl.textContent = message;
    statusEl.className = `status ${type}`;
    statusEl.classList.remove('hidden');

    // Auto-hide after 5 seconds
    setTimeout(() => {
        statusEl.classList.add('hidden');
    }, 5000);
}

/**
 * Show main section after login
 */
function showMainSection() {
    document.getElementById('authSection').classList.add('hidden');
    document.getElementById('mainSection').classList.remove('hidden');
}

/**
 * Handle login
 */
async function handleLogin() {
    const token = document.getElementById('apiToken').value.trim();

    if (!token) {
        showStatus('Please enter your API token', 'error');
        return;
    }

    // Save token
    chrome.runtime.sendMessage({
        action: 'setAuthToken',
        token: token
    }, response => {
        if (response.success) {
            isAuthenticated = true;
            showMainSection();
            showStatus('Connected successfully!', 'success');
        } else {
            showStatus('Failed to save token', 'error');
        }
    });
}

/**
 * Handle start auto-fill
 */
async function handleStartAutoFill() {
    showStatus('Analyzing page...', 'info');
    document.getElementById('startBtn').disabled = true;

    try {
        // Get current tab
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

        // Detect page type
        const pageTypeResult = await sendMessageToTab(tab.id, { action: 'detectPageType' });

        if (pageTypeResult.pageType === 'login') {
            showStatus('⚠️ Login page detected. Cannot auto-fill.', 'warning');
            document.getElementById('startBtn').disabled = false;
            return;
        }

        if (pageTypeResult.pageType !== 'application_form') {
            const proceed = confirm('This doesn\'t look like an application form. Proceed anyway?');
            if (!proceed) {
                document.getElementById('startBtn').disabled = false;
                return;
            }
        }

        // Scrape fields
        showStatus('Scraping form fields...', 'info');
        const fieldsResult = await sendMessageToTab(tab.id, { action: 'scrapeFields' });

        if (!fieldsResult.fields || fieldsResult.fields.length === 0) {
            showStatus('No form fields found on this page', 'error');
            document.getElementById('startBtn').disabled = false;
            return;
        }

        // Get URL
        const jobUrl = document.getElementById('jobUrl').value.trim() || tab.url;
        const companyName = extractCompanyName(jobUrl);

        // Analyze fields with backend
        showStatus(`Analyzing ${fieldsResult.fields.length} fields...`, 'info');
        chrome.runtime.sendMessage({
            action: 'analyzeFields',
            url: jobUrl,
            fields: fieldsResult.fields,
            companyName: companyName
        }, async response => {
            if (response.success) {
                const analysis = response.result;

                // Update stats
                document.getElementById('totalFields').textContent = analysis.total_fields;
                document.getElementById('autoFilled').textContent = analysis.auto_fill_count;
                document.getElementById('needInput').textContent = analysis.ask_user_count;
                document.getElementById('stats').classList.remove('hidden');

                // Create field labels map
                const fieldLabels = {};
                fieldsResult.fields.forEach(f => {
                    fieldLabels[f.id] = f.label;
                });

                // Send strategies to content script
                await sendMessageToTab(tab.id, {
                    action: 'fillFields',
                    strategies: analysis.strategies,
                    fieldLabels: fieldLabels
                });

                showStatus(
                    `✅ Filled ${analysis.auto_fill_count} fields. ${analysis.ask_user_count} need your input.`,
                    'success'
                );
            } else {
                showStatus(`Error: ${response.error}`, 'error');
            }

            document.getElementById('startBtn').disabled = false;
        });

    } catch (error) {
        showStatus(`Error: ${error.message}`, 'error');
        document.getElementById('startBtn').disabled = false;
    }
}

/**
 * Handle view memory
 */
function handleViewMemory() {
    // Open memory management page in new tab
    chrome.tabs.create({
        url: 'http://localhost:5173/auto-apply'  // Will create this page
    });
}

/**
 * Send message to tab
 */
function sendMessageToTab(tabId, message) {
    return new Promise((resolve, reject) => {
        chrome.tabs.sendMessage(tabId, message, response => {
            if (chrome.runtime.lastError) {
                reject(new Error(chrome.runtime.lastError.message));
            } else {
                resolve(response);
            }
        });
    });
}

/**
 * Extract company name from URL
 */
function extractCompanyName(url) {
    try {
        const hostname = new URL(url).hostname;
        const parts = hostname.split('.');

        // Get main domain (e.g., "google" from "jobs.google.com")
        if (parts.length >= 2) {
            return parts[parts.length - 2].charAt(0).toUpperCase() + parts[parts.length - 2].slice(1);
        }

        return hostname;
    } catch {
        return 'Unknown';
    }
}

// Initialize on load
document.addEventListener('DOMContentLoaded', init);


