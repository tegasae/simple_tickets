// Load all admins
async function loadAdmins() {
    try {
        const response = await apiRequest('/admins/');

        if (response.ok) {
            const admins = await response.json();
            displayAdmins(admins);
        } else {
            showNotification('Failed to load admins', 'danger');
        }
    } catch (error) {
        showNotification('Network error', 'danger');
    }
}

// Display admins in table
function displayAdmins(admins) {
    const tableBody = document.getElementById('adminsTableBody');

    if (!admins || admins.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-muted">
                    <i class="bi bi-people display-6"></i>
                    <p class="mt-2">No admins found</p>
                </td>
            </tr>
        `;
        return;
    }

    tableBody.innerHTML = admins.map(admin => `
        <tr>
            <td>${admin.admin_id}</td>
            <td>
                <strong>${admin.name}</strong>
            </td>
            <td>${admin.email}</td>
            <td>
                <span class="badge ${admin.enabled ? 'bg-success' : 'bg-danger'}">
                    ${admin.enabled ? 'Active' : 'Inactive'}
                </span>
            </td>
            <td>${formatDate(admin.date_created)}</td>
            <td>
                <div class="btn-group btn-group-sm" role="group">
                    <a href="/admins/edit/${admin.admin_id}" class="btn btn-outline-primary">
                        <i class="bi bi-pencil"></i>
                    </a>
                    <button type="button" class="btn btn-outline-danger" onclick="deleteAdmin(${admin.admin_id})">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

// Create new admin
async function createAdmin(adminData) {
    return await apiRequest('/admins/', {
        method: 'POST',
        body: JSON.stringify(adminData)
    });
}

// Update admin
async function updateAdmin(adminId, adminData) {
    return await apiRequest(`/admins/${adminId}`, {
        method: 'PUT',
        body: JSON.stringify(adminData)
    });
}

// Delete admin
async function deleteAdmin(adminId) {
    const confirmed = await confirmDialog(
        'Are you sure you want to delete this admin? This action cannot be undone.',
        'Delete',
        'Cancel'
    );

    if (!confirmed) return;

    try {
        const response = await apiRequest(`/admins/${adminId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showNotification('Admin deleted successfully');
            loadAdmins(); // Refresh the list
        } else {
            showNotification('Failed to delete admin', 'danger');
        }
    } catch (error) {
        showNotification('Network error', 'danger');
    }
}

// Get single admin
async function getAdmin(adminId) {
    const response = await apiRequest(`/admins/${adminId}`);
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
