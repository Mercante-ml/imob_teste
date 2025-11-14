// static/js/script.js (CORREÇÃO FINAL DA DECLARAÇÃO E INICIALIZAÇÃO DE VARIÁVEIS)

// --- VARIÁVEIS GLOBAIS: DECLARE-AS APENAS UMA VEZ NO TOPO DO ARQUIVO ---
let chatMessages;
let userInput;
let sendButton;
let loadingDots; // Declarar loadingDots aqui, no escopo global/superior
let sessionId; 
// --- FIM VARIÁVEIS GLOBAIS ---


document.addEventListener('DOMContentLoaded', () => {
    // --- INICIALIZAÇÃO DAS VARIÁVEIS: APENAS ATRIBUA, NÃO DECLARE NOVAMENTE COM 'let' ou 'const' ---
    chatMessages = document.getElementById('chat-messages');
    userInput = document.getElementById('user-input');
    sendButton = document.getElementById('send-button');
    loadingDots = document.getElementById('loading-dots'); // <--- ATRIBUA AQUI, SEM 'let' OU 'const'
    sessionId = getOrCreateSessionId(); 
    // --- FIM DA INICIALIZAÇÃO ---

    // Verificação de segurança: Se algum elemento não for encontrado
    if (!chatMessages || !userInput || !sendButton || !loadingDots) {
        console.error("ERRO CRÍTICO: Um ou mais elementos HTML não foram encontrados no DOM. Verifique os IDs.");
        const errorMessageDiv = document.createElement('div');
        errorMessageDiv.classList.add('message', 'bot');
        errorMessageDiv.innerHTML = "Erro interno: Componentes da interface não carregados. Por favor, recarregue a página.";
        document.body.appendChild(errorMessageDiv);
        return; 
    }

    // Função para adicionar uma mensagem ao chat
    function addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', sender);

        // Remover a sintaxe de bloco de código (``` e a palavra-chave opcional, ex: ```html)
        let cleanText = text.replace(/```(?:\w+)?\n?([\s\S]*?)```/g, '$1').trim(); 
        cleanText = cleanText.replace(/```/g, '').trim(); 
        
        // Converter quebras de linha de texto (\n) para quebras de linha HTML (<br>)
        cleanText = cleanText.replace(/\n/g, '<br>');

        messageDiv.innerHTML = cleanText; 
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Função para gerar ou recuperar um ID de sessão único para o usuário
    function getOrCreateSessionId() {
        let currentSessionId = localStorage.getItem('chatSessionId');
        if (!currentSessionId) {
            currentSessionId = 'session_' + Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
            localStorage.setItem('chatSessionId', currentSessionId);
        }
        return currentSessionId;
    }

    // Função para enviar a mensagem
    async function sendMessage() {
        const message = userInput.value.trim();
        if (message === '') return;

        addMessage(message, 'user');
        userInput.value = '';

        userInput.disabled = true;
        sendButton.disabled = true;
        // loadingDots deve estar definido aqui
        loadingDots.style.display = 'block'; 
        
        let csrfToken = '';
        const csrfElement = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfElement) {
            csrfToken = csrfElement.value;
        } else {
            console.error("ERRO CRÍTICO: Token CSRF não encontrado no HTML! Verifique o {% csrf_token %} no index.html.");
            addMessage('Erro interno: Token de segurança ausente. Por favor, recarregue a página.', 'bot');
            userInput.disabled = false;
            sendButton.disabled = false;
            loadingDots.style.display = 'none';
            return; 
        }

        try {
            const response = await fetch('/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken 
                },
                body: JSON.stringify({ message: message, session_id: sessionId })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.response || `Erro HTTP! status: ${response.status}`);
            }

            const data = await response.json();
            addMessage(data.response, 'bot'); 
        } catch (error) {
            console.error('Erro ao enviar mensagem:', error);
            addMessage('Desculpe, ocorreu um erro. Por favor, tente novamente mais tarde.', 'bot');
        } finally {
            userInput.disabled = false;
            sendButton.disabled = false;
            loadingDots.style.display = 'none';
            userInput.focus();
        }
    }

    // Função auxiliar para obter o token CSRF dos cookies
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

    // Event listeners para clique e tecla Enter
    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // Mensagem de boas-vindas inicial do bot
    addMessage('Olá! Sou sua secretária virtual da barbearia. Como posso ajudar com seu agendamento ou dúvidas?', 'bot');
});