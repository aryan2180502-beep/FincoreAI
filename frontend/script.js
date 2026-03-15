document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('query-form');
    const input = document.getElementById('query-input');
    const messagesContainer = document.getElementById('chat-messages');
    const reasoningLogs = document.getElementById('reasoning-logs');
    const loadingIndicator = document.getElementById('loading-indicator');

    const API_URL = 'http://localhost:8001/ask';

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const query = input.value.trim();
        if (!query) return;

        // Add User Message
        addMessage(query, 'user-message');
        input.value = '';

        // Show Loading
        loadingIndicator.classList.remove('hidden');
        clearReasoning();
        addReasoning('Planning execution path...', 'info');

        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    customer_id: "CUST-0042",
                    scenario: "general"
                }),
            });

            const data = await response.json();

            if (response.ok) {
                // Add AI Message
                addMessage(data.response, 'ai-message');

                // Add Final Reasoning Logs
                addReasoning(`Task completed in ${data.iterations} iterations.`, 'final');
                if (data.intents && data.intents.length > 0) {
                    addReasoning(`Detected Intents: ${data.intents.join(', ')}`, 'info');
                }
            } else {
                addMessage(`Error: ${data.detail || 'Failed to get response'}`, 'ai-message');
            }
        } catch (error) {
            console.error('API Error:', error);
            addMessage('System Error: Could not connect to the assistant backend. Please ensure the API is running.', 'ai-message');
        } finally {
            loadingIndicator.classList.add('hidden');
        }
    });

    function addMessage(text, className) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${className}`;
        msgDiv.textContent = text;
        messagesContainer.appendChild(msgDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function addReasoning(text, type = 'info') {
        const logDiv = document.createElement('div');
        logDiv.className = `log-entry ${type}`;
        logDiv.textContent = text;

        // Remove empty state if present
        const emptyState = reasoningLogs.querySelector('.empty-state');
        if (emptyState) emptyState.remove();

        reasoningLogs.appendChild(logDiv);
        reasoningLogs.scrollTop = reasoningLogs.scrollHeight;
    }

    function clearReasoning() {
        reasoningLogs.innerHTML = '';
    }
});
