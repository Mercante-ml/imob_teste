// static/js/script.js (VERSÃO COM BOTÃO "RESET" REMOVIDO DA INTERFACE)

document.addEventListener('DOMContentLoaded', function() {
    const chatBox = document.getElementById('chat-box');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const buttonsContainer = document.getElementById('buttons-container');
    const chatInputArea = document.getElementById('chat-input-area');
    // Referência ao botão fixo do Menu Principal
    const mainMenuFixedButton = document.getElementById('main-menu-fixed-button');
    // REMOVIDO: const resetFixedButton = document.getElementById('reset-fixed-button');


    // Função para adicionar mensagem ao chat
    function addMessage(sender, message) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', sender);
        messageElement.innerHTML = message.replace(/\n/g, '<br>');
        
        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // Função para renderizar botões dinâmicos
    function renderButtons(buttons) {
        buttonsContainer.innerHTML = '';
        if (buttons && buttons.length > 0) {
            buttons.forEach(buttonData => {
                // IGNORAR botões de navegação global se eles estiverem na lista (eles serão fixos)
                // O botão 'reset' e 'start_main_menu' não serão mais gerados dinamicamente
                if (buttonData.value === 'start_main_menu' || buttonData.value === 'reset' || buttonData.value.includes('back_to_')) {
                    return;
                }

                const button = document.createElement('button');
                button.classList.add('chat-button');
                
                if (buttonData.value.includes('cancel')) {
                    button.classList.add('cancel-button');
                } else if (buttonData.value.includes('rebook')) {
                    button.classList.add('rebook-button');
                } else if (buttonData.value.includes('confirm')) {
                    button.classList.add('confirm-button');
                } else if (buttonData.value === 'start_chat') {
                    button.classList.add('action-button');
                } else {
                    button.classList.add('default-option-button');
                }
                
                button.textContent = buttonData.text;
                button.value = buttonData.value;
                button.addEventListener('click', () => {
                    sendMessage(buttonData.value, buttonData.text);
                    buttonsContainer.innerHTML = '';
                    chatInputArea.style.display = 'flex';
                    messageInput.focus();
                });
                buttonsContainer.appendChild(button);
            });
            buttonsContainer.style.display = 'flex';
            chatInputArea.style.display = 'flex';
            messageInput.focus();
        } else {
            buttonsContainer.style.display = 'none';
            chatInputArea.style.display = 'flex';
            messageInput.focus();
        }
    }

    // Função para enviar mensagem
    function sendMessage(message, displayMessage = null) {
        if (!message.trim() && displayMessage === null) {
            if (chatBox.children.length > 0 && messageInput.value.trim() === '' && message !== 'start_chat') return;
        }

        addMessage('user', displayMessage || message);
        messageInput.value = '';

        buttonsContainer.style.display = 'none';
        chatInputArea.style.display = 'flex';
        messageInput.focus();

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
        })
        .catch(error => {
            console.error('Erro na comunicação com o backend:', error);
            // Mensagem de erro que sugere o botão "Menu Principal" ou recarregar
            addMessage('bot', 'Desculpe, houve um erro na comunicação. Por favor, tente o botão "Menu Principal" ou recarregue a página.');
            // Garante que o input de texto e o botão do Menu Principal fixo estejam visíveis
            buttonsContainer.style.display = 'none'; // Não deve ter botões dinâmicos aqui
            chatInputArea.style.display = 'flex'; 
            messageInput.focus();
        });
    }

    // Event listeners para os botões fixos
    mainMenuFixedButton.addEventListener('click', () => {
        sendMessage(mainMenuFixedButton.value, mainMenuFixedButton.textContent);
    });

    // REMOVIDO: resetFixedButton.addEventListener('click', () => {
    // REMOVIDO:    sendMessage(resetFixedButton.value, resetFixedButton.textContent);
    // REMOVIDO: });

    sendButton.addEventListener('click', () => {
        sendMessage(messageInput.value);
    });

    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage(messageInput.value);
        }
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