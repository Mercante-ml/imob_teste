// static/js/painel.js (VERSÃO COMPLETA COM FILTRO DE STATUS)
document.addEventListener('DOMContentLoaded', () => {
    console.log("painel.js carregado e DOMContentLoaded disparado."); 

    const dateInput = document.getElementById('appointmentDate');
    const barbeiroFilter = document.getElementById('barbeiroFilter'); 
    const statusFilter = document.getElementById('statusFilter'); // NOVO: Pega o elemento do dropdown de status

    const urlParams = new URLSearchParams(window.location.search);
    const currentViewType = urlParams.get('view') || 'daily'; 
    console.log("Tipo de visão atual:", currentViewType);

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

            const currentBarbeiroId = barbeiroFilter ? barbeiroFilter.value : '';
            const currentStatus = statusFilter ? statusFilter.value : ''; // NOVO: Pega o status atual
            console.log("ID do barbeiro atual (no evento de data):", currentBarbeiroId); 
            console.log("Status atual (no evento de data):", currentStatus); // NOVO LOG

            window.location.href = '?data=' + this.value + '&barbeiro=' + currentBarbeiroId + '&view=' + currentViewType + '&status=' + currentStatus; // Inclui status
        });
    } else {
        console.error("Erro: Elemento com ID 'appointmentDate' não encontrado no DOM."); 
    }

    // --- Lógica para o Dropdown do Barbeiro ---
    if (barbeiroFilter) {
        console.log("Elemento barbeiroFilter encontrado.");
        barbeiroFilter.addEventListener('change', function() {
            console.log("Evento 'change' (barbeiro) disparado. Novo barbeiro ID:", this.value);

            const currentDateValue = dateInput ? dateInput.value : ''; 
            const currentStatus = statusFilter ? statusFilter.value : ''; // NOVO: Pega o status atual
            console.log("Data do input (no evento de barbeiro):", currentDateValue); 
            console.log("Status atual (no evento de barbeiro):", currentStatus); // NOVO LOG

            window.location.href = '?data=' + currentDateValue + '&barbeiro=' + this.value + '&view=' + currentViewType + '&status=' + currentStatus; // Inclui status
        });
    } else {
        console.error("Erro: Elemento com ID 'barbeiroFilter' não encontrado no DOM.");
    }

    // --- NOVO: Lógica para o Dropdown de Status ---
    if (statusFilter) {
        console.log("Elemento statusFilter encontrado.");
        statusFilter.addEventListener('change', function() {
            console.log("Evento 'change' (status) disparado. Novo status:", this.value);

            const currentDateValue = dateInput ? dateInput.value : '';
            const currentBarbeiroId = barbeiroFilter ? barbeiroFilter.value : '';
            console.log("Data do input (no evento de status):", currentDateValue);
            console.log("ID do barbeiro atual (no evento de status):", currentBarbeiroId);

            window.location.href = '?data=' + currentDateValue + '&barbeiro=' + currentBarbeiroId + '&view=' + currentViewType + '&status=' + this.value; // Inclui todos
        });
    } else {
        console.error("Erro: Elemento com ID 'statusFilter' não encontrado no DOM.");
    }
});