const chatbox = document.getElementById('chatbox');
const chatForm = document.getElementById('chat-form');
const amountInput = document.getElementById('amount');
const timestampInput = document.getElementById('timestamp');

function appendMessage(sender, text) {
    const messageElem = document.createElement('div');
    messageElem.classList.add('message', sender);
    const textElem = document.createElement('div');
    textElem.classList.add('text');
    textElem.textContent = text;
    messageElem.appendChild(textElem);
    chatbox.appendChild(messageElem);
    chatbox.scrollTop = chatbox.scrollHeight;
}

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const amount = parseFloat(amountInput.value);
    const timestamp = timestampInput.value;

    if (!amount || !timestamp) {
        alert('Please enter valid amount and timestamp.');
        return;
    }

    appendMessage('user', `Transaction Amount: ₹${amount}, Timestamp: ${timestamp}`);

    try {
        const response = await fetch('http://localhost:5001/api/check_fraud', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ amount, timestamp: timestamp.replace('T', ' ') })
        });

        if (!response.ok) {
            throw new Error('Error from server');
        }

        const result = await response.json();

        if (result.error) {
            appendMessage('bot', `Error: ${result.error}`);
        } else {
            const fraudStatus = result.fraud_detected ? '🚨 Potential Fraud Detected!' : '✅ Transaction is Normal.';
            const details = 
                `Isolation Forest: ${result.isolation_forest}\n` +
                `One-Class SVM: ${result.svm}\n` +
                `XGBoost: ${result.xgboost}`;
            appendMessage('bot', `${fraudStatus}\n${details}`);
        }
    } catch (error) {
        appendMessage('bot', 'Error communicating with the server.');
    }

    amountInput.value = '';
    timestampInput.value = '';
});
