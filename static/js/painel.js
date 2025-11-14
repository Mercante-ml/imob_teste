// static/js/painel.js (VERSÃO COMPLETA COM FILTRO DE STATUS E FUNÇÃO DE POLLING PARA RECARGA DA PÁGINA)
document.addEventListener('DOMContentLoaded', () => {
    console.log("painel.js carregado e DOMContentLoaded disparado.");

    const dateInput = document.getElementById('appointmentDate');
    const barbeiroFilter = document.getElementById('barbeiroFilter');
    const statusFilter = document.getElementById('statusFilter'); // Pega o elemento do dropdown de status

    const urlParams = new URLSearchParams(window.location.search);
    const currentViewType = urlParams.get('view') || 'daily';
    console.log("Tipo de visão atual:", currentViewType);

    // Função para recarregar a página com os parâmetros atuais
    function reloadPanel() {
        const currentDateValue = dateInput ? dateInput.value : '';
        const currentBarbeiroId = barbeiroFilter ? barbeiroFilter.value : '';
        const currentStatus = statusFilter ? statusFilter.value : '';
        const currentUrl = `?data=${currentDateValue}&barbeiro=${currentBarbeiroId}&view=${currentViewType}&status=${currentStatus}`;
        window.location.href = currentUrl; // Recarrega a página
    }

    // --- Lógica para o Input de Data ---
    if (dateInput) {
        console.log("Elemento dateInput encontrado.");
        const initialDate = dateInput.dataset.selectedDate;
        console.log("data-selected-date do input (do HTML):", initialDate);

        if (initialDate) {
            dateInput.value = initialDate;
            console.log("dateInput.value definido para:", dateInput.value);
        } else {
            console.log("data-selected-date não encontrado ou vazio, usando data atual como fallback.");
            const today = new Date();
            const year = today.getFullYear();
            const month = String(today.getMonth() + 1).padStart(2, '0');
            const day = String(today.getDate()).padStart(2, '0');
            dateInput.value = year + '-' + month + '-' + day;
            console.log("dateInput.value fallback definido para:", dateInput.value);
        }

        dateInput.addEventListener('change', function() {
            console.log("Evento 'change' (data) disparado. Nova data selecionada:", this.value);
            reloadPanel(); // Usa a função de recarga
        });
    } else {
        console.error("Erro: Elemento com ID 'appointmentDate' não encontrado no DOM.");
    }

    // --- Lógica para o Dropdown do Barbeiro ---
    if (barbeiroFilter) {
        console.log("Elemento barbeiroFilter encontrado.");
        barbeiroFilter.addEventListener('change', function() {
            console.log("Evento 'change' (barbeiro) disparado. Novo barbeiro ID:", this.value);
            reloadPanel(); // Usa a função de recarga
        });
    } else {
        console.error("Erro: Elemento com ID 'barbeiroFilter' não encontrado no DOM.");
    }

    // --- NOVO: Lógica para o Dropdown de Status ---
    if (statusFilter) {
        console.log("Elemento statusFilter encontrado.");
        statusFilter.addEventListener('change', function() {
            console.log("Evento 'change' (status) disparado. Novo status:", this.value);
            reloadPanel(); // Usa a função de recarga
        });
    } else {
        console.error("Erro: Elemento com ID 'statusFilter' não encontrado no DOM.");
    }

    // --- IMPLEMENTAÇÃO DO POLLING ---
    // Define o intervalo de atualização em milissegundos (ex: 30 segundos = 30000ms)
    const POLLING_INTERVAL = 30000; // 30 segundos

    // Inicia o polling
    setInterval(reloadPanel, POLLING_INTERVAL);
    console.log(`Polling iniciado para recarregar a cada ${POLLING_INTERVAL / 1000} segundos.`);
});