const messageList = document.getElementById('message-list');
const intentInput = document.getElementById('intent-input');
const sendBtn = document.getElementById('send-btn');
const approvalWidget = document.getElementById('approval-widget');
const approveBtn = document.getElementById('approve-btn');

// Auto-resize textarea
intentInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
});

// Handle enter to submit
intentInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

sendBtn.addEventListener('click', sendMessage);

approveBtn.addEventListener('click', () => {
    approvalWidget.classList.add('hidden');
    sendMessage("APPROVED");
});

function appendMessage(text, isUser = false) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${isUser ? 'user' : 'system'}`;
    
    // Simple markdown code block replacement for display
    const formattedText = text.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
    
    msgDiv.innerHTML = `
        <div class="avatar">${isUser ? '👤' : '🤖'}</div>
        <div class="content">${formattedText}</div>
    `;
    messageList.appendChild(msgDiv);
    messageList.scrollTop = messageList.scrollHeight;
    
    // Check if the agent is asking for approval
    if (!isUser && text.includes("Do you authorize this Maintenance Window?")) {
        approvalWidget.classList.remove('hidden');
    }
}

function appendProgress(text) {
    const progDiv = document.createElement('div');
    progDiv.className = 'progress-msg';
    progDiv.textContent = text;
    messageList.appendChild(progDiv);
    messageList.scrollTop = messageList.scrollHeight;
}

async function sendMessage(overrideText = null) {
    const text = overrideText || intentInput.value.trim();
    if (!text) return;
    
    if (!overrideText) {
        intentInput.value = '';
        intentInput.style.height = 'auto';
    }
    
    appendMessage(text, true);
    sendBtn.disabled = true;
    
    try {
        const response = await fetch('/api/chat_stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: text,
                user_id: "director",
                session_id: "sprint_123"
            })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n').filter(line => line.trim() !== '');
            
            for (const line of lines) {
                try {
                    const data = JSON.parse(line);
                    if (data.type === 'progress') {
                        appendProgress(data.text);
                    } else if (data.type === 'result') {
                        appendMessage(data.text, false);
                    }
                } catch (e) {
                    console.error("Parse error:", e, line);
                }
            }
        }
    } catch (error) {
        appendMessage("⚠️ Connection error to Orchestrator.", false);
        console.error(error);
    } finally {
        sendBtn.disabled = false;
        intentInput.focus();
    }
}
