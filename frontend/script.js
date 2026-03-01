document.addEventListener('DOMContentLoaded', () => {
    console.log('✅ Script loaded');

    // DOM elements
    const uploadBtn = document.getElementById('uploadBtn');
    const chatFile = document.getElementById('chatFile');
    const fileNameSpan = document.getElementById('fileName');
    const uploadStatus = document.getElementById('uploadStatus');
    const uploadSection = document.getElementById('uploadSection');
    const chatSection = document.getElementById('chatSection');
    const personSelect = document.getElementById('personSelect');
    const questionInput = document.getElementById('question');
    const askBtn = document.getElementById('askBtn');
    const chatHistory = document.getElementById('chatHistory');
    const useOpenAICheckbox = document.getElementById('useOpenAI');
    const chatList = document.getElementById('chatList');
    const newChatBtn = document.getElementById('newChatBtn');

    // Data structures
    let chats = [];
    let currentChatId = null;

    // Open file dialog
    uploadBtn.addEventListener('click', () => {
        chatFile.click();
    });

    // Upload file
    chatFile.addEventListener('change', async () => {
        const file = chatFile.files[0];
        if (!file) {
            fileNameSpan.textContent = 'No file chosen';
            return;
        }

        fileNameSpan.textContent = file.name;
        uploadStatus.innerText = 'Uploading...';

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();

            if (response.ok) {
                uploadStatus.innerText = `Uploaded ${data.message_count} messages.`;
                
                // Prompt for custom name
                let customName = prompt('Give this conversation a name (e.g., Mom, Saavi❤️):', file.name.replace('.txt', ''));
                if (!customName) customName = file.name.replace('.txt', '') || 'Unnamed';
                
                const newChat = {
                    id: 'chat-' + Date.now(),
                    name: customName,
                    collectionId: data.collection_id,
                    senders: data.senders,
                    messages: data.messages,
                    history: []
                };
                chats.push(newChat);
                renderChatList();
                
                // Switch to this chat
                switchToChat(newChat.id);
                
                // Clear file input
                chatFile.value = '';
                fileNameSpan.textContent = 'No file chosen';
            } else {
                uploadStatus.innerText = `Error: ${data.error}`;
            }
        } catch (err) {
            uploadStatus.innerText = `Network error: ${err.message}`;
        }
    });

    // New chat button
    newChatBtn.addEventListener('click', () => {
        uploadSection.style.display = 'block';
        chatSection.style.display = 'none';
    });

    // Render chat list
    function renderChatList() {
        chatList.innerHTML = '';
        chats.forEach(chat => {
            const chatItem = document.createElement('div');
            chatItem.classList.add('chat-item');
            if (chat.id === currentChatId) {
                chatItem.classList.add('active');
            }
            chatItem.dataset.id = chat.id;
            
            chatItem.innerHTML = `
                <div class="chat-item-name">${chat.name}</div>
                <div class="chat-item-meta">${chat.senders.length} participants</div>
            `;
            
            chatItem.addEventListener('click', () => {
                switchToChat(chat.id);
            });
            
            chatList.appendChild(chatItem);
        });
    }

    // Switch chat
    function switchToChat(chatId) {
        const chat = chats.find(c => c.id === chatId);
        if (!chat) return;
        
        currentChatId = chatId;
        renderChatList();
        populateSenders(chat.senders);
        
        // Load history
        chatHistory.innerHTML = '';
        chat.history.forEach(msg => {
            if (msg.isUser) {
                appendMessage('You', msg.text, true);
            } else {
                appendMessage(`If ${msg.person} were here`, msg.text, false, msg.sources);
            }
        });
        
        uploadSection.style.display = 'none';
        chatSection.style.display = 'block';
    }

    function populateSenders(senders) {
        personSelect.innerHTML = '';
        senders.forEach(sender => {
            const option = document.createElement('option');
            option.value = sender;
            option.textContent = sender;
            personSelect.appendChild(option);
        });
    }

    // Append message
    function appendMessage(sender, text, isUser = false, sources = null) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        messageDiv.classList.add(isUser ? 'user' : 'bot');

        const bubble = document.createElement('div');
        bubble.classList.add('message-bubble');
        bubble.innerText = text;
        messageDiv.appendChild(bubble);

        const time = document.createElement('div');
        time.classList.add('message-time');
        const now = new Date();
        time.innerText = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        messageDiv.appendChild(time);

        if (!isUser && sources && sources.length > 0) {
            const sourcesDiv = document.createElement('div');
            sourcesDiv.classList.add('sources');
            sourcesDiv.innerHTML = '<strong>Based on past words:</strong>';
            sources.forEach(src => {
                const srcItem = document.createElement('div');
                srcItem.classList.add('source-item');
                srcItem.innerText = `“${src.text}” — ${src.timestamp}`;
                sourcesDiv.appendChild(srcItem);
            });
            messageDiv.appendChild(sourcesDiv);
        }

        chatHistory.appendChild(messageDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    // Ask button
    askBtn.addEventListener('click', async () => {
        const person = personSelect.value;
        const question = questionInput.value.trim();
        const useOpenAI = useOpenAICheckbox.checked;

        if (!person || !question) {
            alert('Please select a person and enter a question.');
            return;
        }

        const currentChat = chats.find(c => c.id === currentChatId);
        if (!currentChat) return;

        // User message
        appendMessage('You', question, true);
        currentChat.history.push({ isUser: true, text: question, person: null });
        questionInput.value = '';

        // Thinking indicator
        const thinkingId = 'thinking-' + Date.now();
        const thinkingDiv = document.createElement('div');
        thinkingDiv.classList.add('message', 'bot');
        thinkingDiv.id = thinkingId;
        thinkingDiv.innerHTML = '<div class="message-bubble">Thinking...</div>';
        chatHistory.appendChild(thinkingDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;

        try {
            const response = await fetch('/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    collection_id: currentChat.collectionId,
                    person: person,
                    question: question,
                    use_openai: useOpenAI
                })
            });
            const data = await response.json();

            document.getElementById(thinkingId)?.remove();

            if (!response.ok) {
                appendMessage('Ghost Time', `Error: ${data.error}`, false);
                currentChat.history.push({ isUser: false, text: `Error: ${data.error}`, person: person, sources: [] });
                return;
            }

            let botMessage = '';
            let sources = data.sources || [];

            if (data.type === 'generated') {
                botMessage = data.answer;
            } else if (data.type === 'retrieval') {
                botMessage = "Here are some of their past words that might comfort you:";
            } else if (data.type === 'no_results') {
                botMessage = data.message;
                sources = [];
            }

            appendMessage(`If ${person} were here`, botMessage, false, sources);
            currentChat.history.push({ isUser: false, text: botMessage, person: person, sources: sources });
        } catch (err) {
            document.getElementById(thinkingId)?.remove();
            appendMessage('Ghost Time', `Network error: ${err.message}`, false);
            currentChat.history.push({ isUser: false, text: `Network error: ${err.message}`, person: person, sources: [] });
        }
    });

    // Enter to send
    questionInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            askBtn.click();
        }
    });
});