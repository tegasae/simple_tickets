// Load all clients
async function loadClients() {
    try {
        const response = await apiRequest('/clients/');

        if (response.ok) {
            const clients = await response.json();
            displayClients(clients);
        } else {
            showNotification('Failed to load clients', 'danger');
        }
    } catch (error) {
        showNotification('Network error', 'danger');
    }
}

// Display clients in table
function displayClients(clients) {
    const tableBody = document.getElementById('clientsTableBody');

    if (!clients || clients.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center text-muted">
                    <i class="bi bi-people display-6"></i>
                    <p class="mt-2">No clients found</p>
                </td>
            </tr>
        `;
        return;
    }

    tableBody.innerHTML = clients.map(client => `
        <tr>
            <td>${client.client_id}</td>
            <td>
                <strong>${client.name}</strong>
                ${client.is_deleted ? '<span class="badge bg-secondary ms-2">Deleted</span>' : ''}
            </td>
            <td>${client.email}</td>
            <td>${client.phones || '-'}</td>
            <td>
                <span class="badge ${client.enabled ? 'bg-success' : 'bg-danger'}">
                    ${client.enabled ? 'Active' : 'Inactive'}
                </span>
            </td>
            <td>${client.admin_id || '-'}</td>
            <td>${formatDate(client.date_created)}</td>
            <td>
                <div class="btn-group btn-group-sm" role="group">
                    <a href="/clients/edit/${client.client_id}" class="btn btn-outline-primary">
                        <i class="bi bi-pencil"></i>
                    </a>
                    <button type="button" class="btn btn-outline-danger" onclick="deleteClient(${client.client_id})">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

// Create new client
async function createClient(clientData) {
    return await apiRequest('/clients/', {
        method: 'POST',
        body: JSON.stringify(clientData)
    });
}

// Update client
async function updateClient(clientId, clientData) {
    return await apiRequest(`/clients/${clientId}`, {
        method: 'PUT',
        body: JSON.stringify(clientData)
    });
}

// Delete client
async function deleteClient(clientId) {
    const confirmed = await confirmDialog(
        'Are you sure you want to delete this client?',
        'Delete',
        'Cancel'
    );

    if (!confirmed) return;

    try {
        const response = await apiRequest(`/clients/${clientId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showNotification('Client deleted successfully');
            loadClients(); // Refresh the list
        } else {
            showNotification('Failed to delete client', 'danger');
        }
    } catch (error) {
        showNotification('Network error', 'danger');
    }
}

// Get single client
async function getClient(clientId) {
    const response = await apiRequest(`/clients/${clientId}`);
    if (response.ok) {
        return await response.json();
    }
    return null;
}

// Format date for display
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit'
    });
}