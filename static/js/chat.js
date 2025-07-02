class ChatClient {
    constructor(sessionId = null) {
        this.sessionId = sessionId;
        this.socket = null;
        this.isConnected = false;
        this.currentAIMessage = '';
        this.messageQueue = [];
        
        // DOM elements
        this.chatContainer = document.getElementById('chat-container');
        this.messagesContainer = document.getElementById('messages');
        this.messageInput = document.getElementById('message-input');
        this.sendButton = document.getElementById('send-button');
        this.typingIndicator = document.getElementById('typing-indicator');
        
        this.initializeEventListeners();
        this.connect();
    }

    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = this.sessionId 
            ? `${protocol}//${window.location.host}/ws/chat/${this.sessionId}/`
            : `${protocol}//${window.location.host}/ws/chat/`;
        
        this.socket = new WebSocket(wsUrl);
        
        this.socket.onopen = (event) => {
            console.log('WebSocket connected');
            this.isConnected = true;
            this.updateConnectionStatus(true);
        };
        
        this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };
        
        this.socket.onclose = (event) => {
            console.log('WebSocket disconnected');
            this.isConnected = false;
            this.updateConnectionStatus(false);
            
            // Attempt to reconnect after 3 seconds
            setTimeout(() => {
                if (!this.isConnected) {
                    this.connect();
                }
            }, 3000);
        };
        
        this.socket.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.addErrorMessage('Connection error occurred');
        };
    }

    initializeEventListeners() {
        // Send message on button click
        if (this.sendButton) {
            this.sendButton.addEventListener('click', () => {
                this.sendMessage();
            });
        }
        
        // Send message on Enter key press
        if (this.messageInput) {
            this.messageInput.addEventListener('keypress', (event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault();
                    this.sendMessage();
                }
            });
        }
    }

    handleMessage(data) {
        console.log('Received message:', data);
        
        switch (data.type) {
            case 'session_info':
                this.sessionId = data.session_id;
                this.addSystemMessage(data.message);
                break;
                
            case 'message_saved':
                // User message was saved - already displayed
                break;
                
            case 'ai_typing':
                this.showTypingIndicator();
                break;
                
            case 'ai_response_start':
                this.hideTypingIndicator();
                this.currentAIMessage = '';
                this.createAIMessageElement();
                break;
                
            case 'ai_response_token':
                this.currentAIMessage += data.token;
                this.updateCurrentAIMessage(data.token);
                break;
                
            case 'ai_response_end':
                this.finalizeAIMessage();
                break;
                
            case 'ai_message_saved':
                // AI message was saved - already finalized
                break;
                
            case 'error':
                this.addErrorMessage(data.message);
                this.hideTypingIndicator();
                break;
                
            case 'pong':
                // Heartbeat response
                break;
                
            default:
                console.warn('Unknown message type:', data.type);
        }
    }

    sendMessage() {
        if (!this.isConnected) {
            this.addErrorMessage('Not connected to server');
            return;
        }
        
        const message = this.messageInput.value.trim();
        if (!message) {
            return;
        }
        
        // Clear input
        this.messageInput.value = '';
        
        // Display user message immediately
        this.addUserMessage(message);
        
        // Send to server
        const data = {
            type: 'chat_message',
            message: message
        };
        
        this.socket.send(JSON.stringify(data));
        
        // Disable input while processing
        this.setInputEnabled(false);
    }

    addUserMessage(message) {
        const messageElement = this.createMessageElement('user', message);
        this.messagesContainer.appendChild(messageElement);
        this.scrollToBottom();
    }

    createAIMessageElement() {
        this.currentAIMessageElement = this.createMessageElement('ai', '');
        this.messagesContainer.appendChild(this.currentAIMessageElement);
        this.scrollToBottom();
    }

    updateCurrentAIMessage(token) {
        if (this.currentAIMessageElement) {
            const messageContent = this.currentAIMessageElement.querySelector('.message-content');
            messageContent.textContent = this.currentAIMessage;
            
            // Add typing cursor effect
            messageContent.classList.add('typing');
            this.scrollToBottom();
        }
    }

    finalizeAIMessage() {
        if (this.currentAIMessageElement) {
            const messageContent = this.currentAIMessageElement.querySelector('.message-content');
            messageContent.classList.remove('typing');
            this.currentAIMessageElement = null;
        }
        
        // Re-enable input
        this.setInputEnabled(true);
        this.messageInput.focus();
    }

    createMessageElement(sender, message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.textContent = message;
        
        const messageTime = document.createElement('div');
        messageTime.className = 'message-time';
        messageTime.textContent = new Date().toLocaleTimeString();
        
        messageDiv.appendChild(messageContent);
        messageDiv.appendChild(messageTime);
        
        return messageDiv;
    }

    addSystemMessage(message) {
        const messageElement = this.createMessageElement('system', message);
        this.messagesContainer.appendChild(messageElement);
        this.scrollToBottom();
    }

    addErrorMessage(message) {
        const messageElement = this.createMessageElement('error', `Error: ${message}`);
        this.messagesContainer.appendChild(messageElement);
        this.scrollToBottom();
    }

    showTypingIndicator() {
        if (this.typingIndicator) {
            this.typingIndicator.style.display = 'block';
            this.scrollToBottom();
        }
    }

    hideTypingIndicator() {
        if (this.typingIndicator) {
            this.typingIndicator.style.display = 'none';
        }
    }

    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            statusElement.textContent = connected ? 'Connected' : 'Disconnected';
            statusElement.className = connected ? 'connected' : 'disconnected';
        }
    }

    setInputEnabled(enabled) {
        if (this.messageInput) {
            this.messageInput.disabled = !enabled;
        }
        if (this.sendButton) {
            this.sendButton.disabled = !enabled;
        }
    }

    scrollToBottom() {
        if (this.messagesContainer) {
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }
    }

    // Send periodic ping to keep connection alive
    startHeartbeat() {
        setInterval(() => {
            if (this.isConnected) {
                this.socket.send(JSON.stringify({ type: 'ping' }));
            }
        }, 30000); // 30 seconds
    }

    disconnect() {
        if (this.socket) {
            this.socket.close();
        }
    }
}

// Initialize chat when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Get session ID from window variable set in template
    const sessionId = window.chatSessionId || null;
    
    // Initialize chat client
    window.chatClient = new ChatClient(sessionId);
    window.chatClient.startHeartbeat();
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (window.chatClient) {
        window.chatClient.disconnect();
    }
});