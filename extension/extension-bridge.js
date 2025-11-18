// Extension Bridge - Injected into web pages to communicate with the extension
// This makes the extension auto-detectable without hardcoding the ID

(function () {
    // Notify the page that the extension is installed
    window.postMessage({
        type: 'AUTOFILL_EXTENSION_INSTALLED',
        extensionId: chrome.runtime.id
    }, '*');

    // Auto-sync auth token from web app to extension
    if (window.location.hostname === 'localhost' && window.location.port === '5173') {
        // Check for token periodically
        const syncToken = () => {
            const token = localStorage.getItem('access_token');
            if (token) {
                chrome.runtime.sendMessage({
                    action: 'setAuthToken',
                    token: token
                }, (response) => {
                    if (response && response.success) {
                        console.log('[AutoFill] Auth token synced automatically ✅');
                    }
                });
            }
        };

        // Sync immediately on page load
        setTimeout(syncToken, 1000);

        // Sync when user logs in
        window.addEventListener('storage', (e) => {
            if (e.key === 'access_token') {
                syncToken();
            }
        });
    }

})();
