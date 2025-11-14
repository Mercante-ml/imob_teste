// static/js/script.js (VERSÃO PARA CHATBOT DE BOTÕES E INTERAÇÃO DINÂMICA)

document.addEventListener('DOMContentLoaded', function() {
    const chatBox = document.getElementById('chat-box');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const buttonsContainer = document.getElementById('buttons-container');
    const chatInputArea = document.getElementById('chat-input-area');

    // Função para adicionar mensagem ao chat
    function addMessage(sender, message) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', sender);
        // Garante que quebras de linha sejam interpretadas como HTML <br>
        messageElement.innerHTML = message.replace(/\n/g, '<br>');
        
        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // Função para renderizar botões
    function renderButtons(buttons) {
        buttonsContainer.innerHTML = ''; // Limpa botões anteriores
        if (buttons && buttons.length > 0) {
            buttons.forEach(buttonData => {
                const button = document.createElement('button');
                button.classList.add('chat-button');
                // Adiciona classes para estilização por tipo de botão
                if (buttonData.value.includes('cancel')) {
                    button.classList.add('cancel-button');
                } else if (buttonData.value.includes('rebook')) {
                    button.classList.add('rebook-button');
                } else if (buttonData.value.includes('confirm')) {
                    button.classList.add('confirm-button');
                } else if (buttonData.value === 'start_chat' || buttonData.value === 'reset') {
                    button.classList.add('action-button'); // Botões de ação geral
                } else if (buttonData.value === 'start_main_menu' || buttonData.value === 'start_booking' || buttonData.value === 'start_rebooking') {
                    button.classList.add('menu-button'); // Botões de menu
                }
                
                button.textContent = buttonData.text;
                button.value = buttonData.value;
                button.addEventListener('click', () => {
                    sendMessage(buttonData.value, buttonData.text); // Envia o valor do botão, exibe o texto
                    buttonsContainer.innerHTML = ''; // Esconde os botões após o clique
                    // Oculta/Exibe a área de input dependendo da necessidade no próximo passo
                    // Idealmente, o backend controlaria se o próximo passo é texto ou botões
                    // Por simplicidade aqui, sempre reativa o input após clique de botão.
                    chatInputArea.style.display = 'flex'; // Reativa o input para permitir digitação
                    messageInput.focus(); // Coloca o foco no input
                });
                buttonsContainer.appendChild(button);
            });
            buttonsContainer.style.display = 'flex'; // Exibe o container de botões
            // Não oculta chatInputArea aqui, permite que o usuário digite E clique em botões
            // chatInputArea.style.display = 'none'; // REMOVIDO PARA PERMITIR INPUT MISTO
        } else {
            buttonsContainer.style.display = 'none'; // Oculta o container de botões
            chatInputArea.style.display = 'flex'; // Exibe a área de input de texto
            messageInput.focus(); // Coloca o foco no input de mensagem
        }
    }

    // Função para enviar mensagem
    function sendMessage(message, displayMessage = null) {
        if (!message.trim() && displayMessage === null) {
            // Permite a primeira chamada vazia para iniciar o fluxo, mas impede envios vazios depois
            if (chatBox.children.length > 0) return; 
        }

        addMessage('user', displayMessage || message);
        messageInput.value = '';

        // Mostra um estado de "digitando" ou "processando" se desejar
        // Por agora, apenas esconde os botões para evitar cliques duplos enquanto aguarda
        buttonsContainer.style.display = 'none'; 
        // Não esconde chatInputArea aqui, pois pode ser necessário para a próxima entrada (ex: número do agendamento)

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
            addMessage('bot', 'Desculpe, houve um erro na comunicação. Por favor, digite "reset" para reiniciar.');
            renderButtons([]); // Garante que o input de texto reapareça em caso de erro
        });
    }

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

    // Inicia a conversa enviando uma mensagem vazia para o backend para carregar o primeiro estado/botões
    // O backend agora deve começar com a tela de boas-vindas com o botão "Iniciar"
    sendMessage(''); 
});