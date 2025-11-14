// static/js/script.js (VERSÃO FINAL COM CORREÇÃO DE VISIBILIDADE DO INPUT/ENVIAR)

document.addEventListener('DOMContentLoaded', function() {
    const chatBox = document.getElementById('chat-box');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const buttonsContainer = document.getElementById('buttons-container');
    const chatInputArea = document.getElementById('chat-input-area'); // A área completa do input de texto
    const mainMenuFixedButton = document.getElementById('main-menu-fixed-button');

    function addMessage(sender, message) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', sender);
        // Usa innerHTML para que tags HTML (como as da lista de agendamentos) sejam interpretadas
        messageElement.innerHTML = message.replace(/\n/g, '<br>'); 
        
        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function renderButtons(buttons) {
        buttonsContainer.innerHTML = ''; // Limpa botões existentes
        
        // NOVO: Garante que a área de input de texto esteja SEMPRE visível.
        // Ocultamos apenas se o backend sinalizar que a próxima ação é EXCLUSIVAMENTE por botão.
        // Por padrão, ela estará visível para permitir digitação.
        chatInputArea.style.display = 'flex'; //

        if (buttons && buttons.length > 0) {
            buttons.forEach(buttonData => {
                if (buttonData.value === 'start_main_menu') {
                    return; 
                }

                const button = document.createElement('button');
                button.classList.add('chat-button');
                
                if (buttonData.value === 'start_chat' || buttonData.value === 'yes_retry_phone') {
                    button.classList.add('action-button'); 
                } else if (buttonData.value === 'start_booking' || buttonData.value === 'start_rebooking') {
                    button.classList.add('menu-button'); 
                } else if (buttonData.value.includes('cancel')) {
                    button.classList.add('cancel-button'); 
                } else if (buttonData.value.includes('rebook')) {
                    button.classList.add('rebook-button'); 
                } else if (buttonData.value.includes('confirm')) {
                    button.classList.add('confirm-button'); 
                } else {
                    button.classList.add('default-option-button'); 
                }
                
                button.textContent = buttonData.text;
                button.value = buttonData.value;
                button.addEventListener('click', () => {
                    sendMessage(buttonData.value, buttonData.text);
                    buttonsContainer.innerHTML = ''; // Limpa botões dinâmicos após o clique
                    buttonsContainer.style.display = 'none'; // Esconde o container de botões
                    chatInputArea.style.display = 'flex'; // Garante que o input esteja visível após o clique
                    messageInput.focus();
                });
                buttonsContainer.appendChild(button);
            });
            buttonsContainer.style.display = 'flex'; // Exibe o container de botões dinâmicos
            messageInput.focus(); 
        } else {
            buttonsContainer.style.display = 'none'; // Oculta o container de botões dinâmicos
            // chatInputArea.style.display já está definido como 'flex' no início da função.
            messageInput.focus();
        }
    }

    function sendMessage(message, displayMessage = null) {
        if (!message.trim() && displayMessage === null && message !== 'start_chat' && message !== 'start_main_menu' && message !== 'start_booking' && message !== 'start_rebooking') {
            if (chatBox.children.length > 0 && messageInput.value.trim() === '') {
                return; 
            }
        }

        addMessage('user', displayMessage || message);
        messageInput.value = '';

        buttonsContainer.style.display = 'none'; // Oculta botões dinâmicos ao enviar
        chatInputArea.style.display = 'flex'; // Garante input visível novamente
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
            addMessage('bot', 'Desculpe, houve um erro na comunicação. Por favor, tente o botão "Menu Principal".');
            // Em caso de erro, garante que o input de texto e o botão do Menu Principal fixo estejam visíveis
            buttonsContainer.style.display = 'none';
            chatInputArea.style.display = 'flex';
            messageInput.focus();
        });
    }

    // Event listeners para os botões fixos
    mainMenuFixedButton.addEventListener('click', () => {
        // Quando um botão fixo é clicado, limpa os botões dinâmicos (se houver)
        buttonsContainer.innerHTML = ''; 
        buttonsContainer.style.display = 'none';
        chatInputArea.style.display = 'flex'; // Garante que o input esteja visível
        sendMessage(mainMenuFixedButton.value, mainMenuFixedButton.textContent);
    });

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

    // Dispara a mensagem inicial para carregar a tela de boas-vindas
    sendMessage(''); 
});