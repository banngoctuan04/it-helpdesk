document.addEventListener('DOMContentLoaded', () => {
    if (!document.querySelector('.nav-user')) return;

    const chatHTML = `
        <div id="chat-bubble" class="chat-bubble-toggle"><i class="fas fa-robot"></i></div>
        <div id="chatbox" class="chatbox hidden">
            <div class="chatbox-header">Trợ lý ảo AI</div>
            <div id="chatbox-messages" class="chatbox-messages"></div>
            <div class="chatbox-input">
                <input type="text" id="user-input" placeholder="Hỏi AI về sự cố của bạn...">
                <button id="send-btn"><i class="fas fa-paper-plane"></i></button>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', chatHTML);

    const chatBubble = document.getElementById('chat-bubble');
    const chatbox = document.getElementById('chatbox');
    const messagesContainer = document.getElementById('chatbox-messages');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    
    // Nút đóng không có sẵn trong HTML ban đầu, phải query sau khi tạo
    document.body.addEventListener('click', function(event) {
        if (event.target.id === 'close-chat-btn-dynamic') {
             chatbox.classList.add('hidden');
             chatBubble.classList.remove('hidden');
        }
    });

    chatBubble.addEventListener('click', () => {
        chatbox.classList.toggle('hidden');
        chatBubble.classList.toggle('hidden');
        if (!chatbox.classList.contains('hidden')) {
            userInput.focus();
        }
    });

    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    // --- LOGIC MỚI BẮT ĐẦU TỪ ĐÂY ---

    // Xử lý khi nhấn vào các nút trong menu
    messagesContainer.addEventListener('click', function(event) {
        if (event.target.classList.contains('chat-menu-button')) {
            const userText = event.target.getAttribute('data-query');
            appendMessage(userText, 'user-message'); // Hiển thị lựa chọn của user
            userInput.value = '';
            showTypingIndicator();
            // Gọi AI với lựa chọn của user
            fetchAiResponse(userText);
        }
    });

    async function sendMessage() {
        const userText = userInput.value.trim();
        if (userText === '') return;
        appendMessage(userText, 'user-message');
        userInput.value = '';
        showTypingIndicator();
        await fetchAiResponse(userText);
    }

    async function fetchAiResponse(userText) {
        try {
            const response = await fetch('/api/chatbot', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: userText }),
            });
            if (!response.ok) throw new Error('Network response was not ok.');

            const data = await response.json();
            let botReply = data.reply;

            // Xử lý logic nếu AI yêu cầu tạo ticket
            const ticketMatch = botReply.match(/\[CREATE_TICKET:(.*?)\]/);
            if (ticketMatch && ticketMatch[1]) {
                const ticketTitle = ticketMatch[1].trim();
                botReply = botReply.replace(/\[CREATE_TICKET:.*?\]/, ''); // Xóa chuỗi đặc biệt
                
                // Mã hóa tiêu đề để truyền qua URL an toàn
                const encodedTitle = encodeURIComponent(ticketTitle);
                botReply += `<br><br><a href="/ticket/new?title=${encodedTitle}" class="btn btn-primary">Nhấn vào đây để tạo ticket</a>`;
            }

            removeTypingIndicator();
            appendMessage(botReply, 'bot-message');

        } catch (error) {
            console.error('Error:', error);
            removeTypingIndicator();
            appendMessage('Xin lỗi, đã có lỗi kết nối. Vui lòng thử lại.', 'bot-message');
        }
    }

    function appendMessage(html, className) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', className);
        messageDiv.innerHTML = html;
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.classList.add('message', 'bot-message', 'typing-indicator');
        typingDiv.innerHTML = '<span></span><span></span><span></span>';
        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function removeTypingIndicator() {
        const indicator = document.querySelector('.typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }
    
    // Tin nhắn chào mừng ban đầu của bot với các nút bấm
    const welcomeMessage = `Chào bạn! Tôi là Trợ lý ảo IT. Vui lòng chọn một vấn đề phổ biến bên dưới hoặc mô tả sự cố của bạn:
        <br><br>
        <button class="btn btn-secondary btn-sm chat-menu-button" data-query="Không vào được mạng">Sự cố Mạng</button>
        <button class="btn btn-secondary btn-sm chat-menu-button" data-query="Máy tính bị chậm">Máy tính chậm</button>
        <button class="btn btn-secondary btn-sm chat-menu-button" data-query="Không in được">Lỗi máy in</button>
    `;
    appendMessage(welcomeMessage, 'bot-message');
});