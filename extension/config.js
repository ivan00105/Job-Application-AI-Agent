// Extension configuration
// IMPORTANT: Update this before deploying to production
const CONFIG = {
    API_BASE_URL: 'http://localhost:8000',  // Change to production URL when deploying
    API_ENDPOINTS: {
        ANALYZE_FIELDS: '/api/autofill/analyze-fields',
        SAVE_ANSWER: '/api/autofill/save-answer',
        GET_MEMORY: '/api/autofill/memory'
    }
};

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
}


