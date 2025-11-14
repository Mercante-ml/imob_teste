// static/js/script.js (VERSÃO CORRIGIDA - LÊ A MENSAGEM DO ADMIN)

document.addEventListener('DOMContentLoaded', function() {
    // --- Elementos do DOM ---
    const chatBox = document.getElementById('chat-box');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const buttonsContainer = document.getElementById('buttons-container');
    const chatInputArea = document.getElementById('chat-input-area');
    const mainMenuFixedButton = document.getElementById('main-menu-fixed-button');

    // ================================================
    // --- LÓGICA DO ÍCONE DE COMPARTILHAR (DINÂMICA) ---
    // ================================================
    const shareIconButton = document.getElementById('share-icon-button'); 
    
    if (shareIconButton) { 
        shareIconButton.addEventListener('click', () => {
            // 1. Pega a URL atual do site (automático)
            const appUrl = "https://barbearia-mf4q.onrender.com"; 
            
            // 2. AQUI ESTÁ A CORREÇÃO:
            // Pega a frase que veio do banco de dados (Admin) e está escondida no HTML
            const adminMessage = shareIconButton.getAttribute('data-share-message');
            
            // Usa a mensagem do admin ou um padrão se estiver vazia
            const finalMessage = adminMessage ? adminMessage : "Agende seu horário na Barbearia:";
            
            // 3. Monta o texto final: Frase + Link
            const fullText = `${finalMessage} ${appUrl}`;
            
            const encodedMessage = encodeURIComponent(fullText);
            const whatsappUrl = `https://api.whatsapp.com/send?text=${encodedMessage}`;
            
            window.open(whatsappUrl, '_blank');
        });
    }
    // ================================================


    // --- Função para Adicionar Mensagem ---
    function addMessage(sender, message) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', sender);
        messageElement.innerHTML = message.replace(/\n/g, '<br>'); 
        chatBox.appendChild(messageElement);
        setTimeout(() => { chatBox.scrollTop = chatBox.scrollHeight; }, 0);
    }

    // --- Renderização de Botões ---
    function renderButtons(buttons) {
        buttonsContainer.innerHTML = ''; 
        buttonsContainer.classList.remove('grid-4-columns');

        if (buttons && buttons.length > 0) {
            // Detecção inteligente de dias (números curtos)
            const isDayList = buttons[0].text.length <= 2 && !isNaN(buttons[0].text);
            
            if (isDayList) {
                buttonsContainer.classList.add('grid-4-columns');
            }

            buttons.forEach(buttonData => {
                if (buttonData.value === 'start_main_menu') { return; }

                const button = document.createElement('button');
                button.classList.add('chat-button');
                
                if (buttonData.value === 'start_chat' || buttonData.value === 'start_booking' || buttonData.value.includes('confirm') || buttonData.value.startsWith('sim_')) {
                    button.classList.add('confirm-button'); 
                } else if (buttonData.value.includes('cancel') || buttonData.value.startsWith('nao_')) {
                    button.classList.add('cancel-button'); 
                }
                
                button.textContent = buttonData.text;
                button.value = buttonData.value;
                button.addEventListener('click', () => {
                    sendMessage(buttonData.value, buttonData.text);
                });
                buttonsContainer.appendChild(button);
            });
            
            buttonsContainer.style.display = isDayList ? 'grid' : 'flex';
            chatInputArea.style.display = 'none'; 
            
        } else {
            buttonsContainer.style.display = 'none'; 
            chatInputArea.style.display = 'flex'; 
            messageInput.focus(); 
        }
    }

    // --- Envio de Mensagem ---
    function sendMessage(message, displayMessage = null) {
        if (!message.trim() && displayMessage === null && message !== 'start_chat' && message !== 'start_main_menu' && message !== 'start_booking' && message !== 'start_rebooking') {
            if (chatBox.children.length > 0 && messageInput.value.trim() === '') return; 
        }

        addMessage('user', displayMessage || message);
        messageInput.value = '';

        buttonsContainer.innerHTML = ''; 
        buttonsContainer.style.display = 'none';
        messageInput.disabled = true;
        sendButton.disabled = true;
        chatInputArea.style.display = 'none'; 

        fetch('/chat/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ message: message })
        })
        .then(response => response.json())
        .then(data => {
            addMessage('bot', data.message);
            renderButtons(data.buttons); 
            messageInput.disabled = false;
            sendButton.disabled = false;
        })
        .catch(error => {
            console.error('Erro:', error);
            addMessage('bot', 'Desculpe, houve um erro na comunicação. Por favor, tente o botão "Menu Principal".');
            buttonsContainer.style.display = 'none';
            chatInputArea.style.display = 'flex';
            messageInput.disabled = false;
            sendButton.disabled = false;
            messageInput.focus();
        });
    }

    mainMenuFixedButton.addEventListener('click', () => {
        sendMessage(mainMenuFixedButton.value, mainMenuFixedButton.textContent);
    });

    sendButton.addEventListener('click', () => {
        sendMessage(messageInput.value);
    });

    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage(messageInput.value);
    });

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    sendMessage(''); 
});