// static/js/script.js (VERSÃO COM BOTÕES FIXOS DE NAVEGAÇÃO GLOBAL)

document.addEventListener('DOMContentLoaded', function() {
    const chatBox = document.getElementById('chat-box');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const buttonsContainer = document.getElementById('buttons-container');
    const chatInputArea = document.getElementById('chat-input-area');
    // Novos elementos para botões fixos
    const mainMenuFixedButton = document.getElementById('main-menu-fixed-button');
    const resetFixedButton = document.getElementById('reset-fixed-button');


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
        buttonsContainer.innerHTML = ''; // Limpa botões anteriores
        if (buttons && buttons.length > 0) {
            buttons.forEach(buttonData => {
                // IGNORAR botões de navegação global se eles estiverem na lista (eles serão fixos)
                if (buttonData.value === 'start_main_menu' || buttonData.value === 'reset' || buttonData.value.includes('back_to_')) {
                    return; // Pula este botão, pois ele será gerenciado pelo elemento fixo
                }

                const button = document.createElement('button');
                button.classList.add('chat-button');
                
                // Adiciona classes para estilização por tipo de botão (para botões dinâmicos de fluxo)
                if (buttonData.value.includes('cancel')) {
                    button.classList.add('cancel-button');
                } else if (buttonData.value.includes('rebook')) {
                    button.classList.add('rebook-button');
                } else if (buttonData.value.includes('confirm')) {
                    button.classList.add('confirm-button');
                } else if (buttonData.value === 'start_chat') { // Exclusivo para o botão Iniciar
                    button.classList.add('action-button');
                } else {
                    button.classList.add('default-option-button'); // Nova classe para opções de serviço, etc.
                }
                
                button.textContent = buttonData.text;
                button.value = buttonData.value;
                button.addEventListener('click', () => {
                    sendMessage(buttonData.value, buttonData.text); // Envia o valor do botão, exibe o texto
                    buttonsContainer.innerHTML = ''; // Esconde os botões dinâmicos após o clique
                    // Garante que o input de texto esteja visível para o próximo passo
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

    // Função para enviar mensagem
    function sendMessage(message, displayMessage = null) {
        if (!message.trim() && displayMessage === null) {
            // Permite a primeira chamada vazia para iniciar o fluxo
            if (chatBox.children.length > 0 && messageInput.value.trim() === '' && message !== 'start_chat') return; // Ajustado para permitir start_chat inicial
        }

        addMessage('user', displayMessage || message);
        messageInput.value = '';

        buttonsContainer.style.display = 'none'; // Oculta botões dinâmicos ao enviar
        chatInputArea.style.display = 'flex'; // Garante input visível
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
            renderButtons(data.buttons); // Renderiza os botões dinâmicos
        })
        .catch(error => {
            console.error('Erro na comunicação com o backend:', error);
            addMessage('bot', 'Desculpe, houve um erro na comunicação. Por favor, digite "reset" para reiniciar.');
            renderButtons([]); // Garante que o input de texto reapareça em caso de erro
        });
    }

    // Event listeners para os botões fixos
    mainMenuFixedButton.addEventListener('click', () => {
        sendMessage(mainMenuFixedButton.value, mainMenuFixedButton.textContent);
    });

    resetFixedButton.addEventListener('click', () => {
        sendMessage(resetFixedButton.value, resetFixedButton.textContent);
    });

    // Event listener para o botão de enviar mensagem (do input de texto)
    sendButton.addEventListener('click', () => {
        sendMessage(messageInput.value);
    });

    // Event listener para a tecla Enter no input de mensagem
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

    // Inicia a conversa enviando uma mensagem vazia para o backend para carregar o primeiro estado/botões
    sendMessage(''); 
});