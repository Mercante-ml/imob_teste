// static/js/script.js (VERSÃO COM BOTÕES DE NAVEGAÇÃO FIXOS)

document.addEventListener('DOMContentLoaded', function() {
    const chatBox = document.getElementById('chat-box');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const buttonsContainer = document.getElementById('buttons-container');
    const chatInputArea = document.getElementById('chat-input-area');
    const mainMenuFixedButton = document.getElementById('main-menu-fixed-button');
    const recomecarAgendamentoFixedButton = document.getElementById('recomecar-agendamento-fixed-button'); // Novo botão fixo

    function addMessage(sender, message) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', sender);
        messageElement.innerHTML = message.replace(/\n/g, '<br>');
        
        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function renderButtons(buttons) {
        buttonsContainer.innerHTML = ''; // Limpa botões anteriores
        if (buttons && buttons.length > 0) {
            buttons.forEach(buttonData => {
                // IGNORAR botões que agora são fixos ou foram removidos do fluxo dinâmico
                if (buttonData.value === 'start_main_menu' || buttonData.value === 'reset' || buttonData.value === 'start_booking' || buttonData.value === 'start_rebooking') {
                    return; // Pula estes botões, eles são fixos ou são tratados como menu principal
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
                } else if (buttonData.value.includes('yes_retry_phone')) {
                    button.classList.add('menu-button'); // Sim/Não de retentativa
                }
                else {
                    button.classList.add('default-option-button'); // Cor padrão para opções de serviço, mês, dia, horário
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
            buttonsContainer.style.display = 'flex'; // Exibe o container de botões dinâmicos
            chatInputArea.style.display = 'flex'; // Garante que a área de input TAMBÉM esteja visível
            messageInput.focus();
        } else {
            buttonsContainer.style.display = 'none'; // Oculta o container de botões dinâmicos
            chatInputArea.style.display = 'flex'; // Exibe a área de input de texto
            messageInput.focus();
        }
    }

    function sendMessage(message, displayMessage = null) {
        if (!message.trim() && displayMessage === null) {
            if (chatBox.children.length > 0 && messageInput.value.trim() === '' && message !== 'start_chat') {
                return; 
            }
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

            const messageLower = data.message.toLowerCase();
            const shouldReload = (
                messageLower.includes('recarregar a página') || 
                messageLower.includes('recarregue a página') || 
                (messageLower.includes('sucesso') && data.buttons.length === 0) || 
                (messageLower.includes('cancelado com sucesso') && data.buttons.length === 0)
            );

            if (shouldReload) {
                setTimeout(() => {
                    location.reload(); 
                }, 1500);
            }
        })
        .catch(error => {
            console.error('Erro na comunicação com o backend:', error);
            addMessage('bot', 'Desculpe, houve um erro na comunicação. Por favor, tente o botão "Menu Principal" ou recarregue a página.');
            buttonsContainer.style.display = 'none';
            chatInputArea.style.display = 'flex';
            messageInput.focus();
        });
    }

    // Event listeners para os botões fixos
    mainMenuFixedButton.addEventListener('click', () => {
        sendMessage(mainMenuFixedButton.value, mainMenuFixedButton.textContent);
    });

    recomecarAgendamentoFixedButton.addEventListener('click', () => { // NOVO listener
        sendMessage(recomecarAgendamentoFixedButton.value, recomecarAgendamentoFixedButton.textContent);
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

    sendMessage(''); 
});