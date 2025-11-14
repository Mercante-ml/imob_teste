// static/js/script.js (VERSÃO FINAL E AJUSTADA COM RECARGA AUTOMÁTICA)

document.addEventListener('DOMContentLoaded', function() {
    const chatBox = document.getElementById('chat-box');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const buttonsContainer = document.getElementById('buttons-container');
    const chatInputArea = document.getElementById('chat-input-area');
    const mainMenuFixedButton = document.getElementById('main-menu-fixed-button'); // Botão fixo do Menu Principal

    // Função para adicionar mensagem ao chat
    function addMessage(sender, message) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', sender);
        // Garante que quebras de linha sejam interpretadas como HTML <br>
        messageElement.innerHTML = message.replace(/\n/g, '<br>');
        
        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // Função para renderizar botões dinâmicos
    function renderButtons(buttons) {
        buttonsContainer.innerHTML = ''; // Limpa botões anteriores
        if (buttons && buttons.length > 0) {
            buttons.forEach(buttonData => {
                // Ignorar botões que agora são fixos ou foram removidos do fluxo dinâmico
                if (buttonData.value === 'start_main_menu' || buttonData.value === 'reset') {
                    return; 
                }

                const button = document.createElement('button');
                button.classList.add('chat-button');
                
                // Adiciona classes para estilização por tipo de botão
                if (buttonData.value.includes('cancel')) {
                    button.classList.add('cancel-button');
                } else if (buttonData.value.includes('rebook')) {
                    button.classList.add('rebook-button');
                } else if (buttonData.value.includes('confirm')) {
                    button.classList.add('confirm-button');
                } else if (buttonData.value === 'start_chat') {
                    button.classList.add('action-button');
                } else if (buttonData.value.includes('yes_retry_phone') || buttonData.value === 'start_booking' || buttonData.value === 'start_rebooking') {
                    button.classList.add('menu-button'); // Botões de 'Sim' ou 'Agendar/Gerenciar' que são azuis
                }
                else {
                    button.classList.add('default-option-button'); // Cor padrão para opções de serviço, mês, dia, horário
                }
                
                button.textContent = buttonData.text;
                button.value = buttonData.value;
                button.addEventListener('click', () => {
                    sendMessage(buttonData.value, buttonData.text); // Envia o valor do botão, exibe o texto
                    buttonsContainer.innerHTML = ''; // Esconde os botões dinâmicos após o clique
                    chatInputArea.style.display = 'flex'; // Garante que a área de input TAMBÉM esteja visível
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
            // Permite a primeira chamada vazia para iniciar o fluxo (vinda do DOMContentLoaded)
            // Ou o 'start_chat' quando o usuário clica no botão Iniciar.
            if (chatBox.children.length > 0 && messageInput.value.trim() === '' && message !== 'start_chat') {
                 // Não envia mensagens vazias após o início do chat, a menos que seja um clique em botão.
                return; 
            }
        }

        addMessage('user', displayMessage || message); // Adiciona a mensagem do usuário ao histórico
        messageInput.value = ''; // Limpa o input

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
            renderButtons(data.buttons);

            // NOVO: Recarrega a página se a resposta indica uma ação final e não há botões específicos para continuar o fluxo.
            const messageLower = data.message.toLowerCase();
            const shouldReload = (
                messageLower.includes('recarregar a página') || 
                messageLower.includes('recarregue a página') || 
                (messageLower.includes('sucesso') && data.buttons.length === 0) || // Ex: agendamento salvo com sucesso, e não tem botões para seguir o fluxo
                (messageLower.includes('cancelado com sucesso') && data.buttons.length === 0)
            );

            if (shouldReload) {
                // Pequeno atraso para o usuário ler a mensagem
                setTimeout(() => {
                    location.reload(); 
                }, 1500); // Recarrega após 1.5 segundos
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

    // Event listener para o botão fixo do Menu Principal
    mainMenuFixedButton.addEventListener('click', () => {
        sendMessage(mainMenuFixedButton.value, mainMenuFixedButton.textContent);
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

    // Função para pegar o CSRF token do cookie
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