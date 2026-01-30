// API Base URL (pointing to the existing API server)
const API_BASE_URL = 'http://127.0.0.1:8000';

// Get access token from cookie
function getAccessToken() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'access_token') {
            return value;
        }
    }
    return null;
}

// Make authenticated API request
async function apiRequest(endpoint, options = {}) {
    const token = getAccessToken();
    if (!token && !options.public) {
        window.location.href = '/login';
        return;
    }

    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
    };

    if (token) {
        defaultOptions.headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers,
        },
    });

    // Handle token expiration
    if (response.status === 401 && !options.public) {
        // Try to refresh token
        const refreshToken = getRefreshToken();
        if (refreshToken) {
            try {
                const refreshResponse = await fetch(`${API_BASE_URL}/refresh`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ refresh_token: refreshToken }),
                });

                if (refreshResponse.ok) {
                    const tokens = await refreshResponse.json();
                    // Update cookies (would need server-side help)
                    // For now, redirect to login
                    window.location.href = '/login';
                } else {
                    window.location.href = '/login';
                }
            } catch (error) {
                window.location.href = '/login';
            }
        } else {
            window.location.href = '/login';
        }
    }

    return response;
}

// Get refresh token from cookie
function getRefreshToken() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'refresh_token') {
            return value;
        }
    }
    return null;
}

// Show notification
function showNotification(message, type = 'success') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = `
        top: 20px;
        right: 20px;
        z-index: 1050;
        min-width: 300px;
    `;
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(notification);

    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 5000);
}

// Confirm dialog
function confirmDialog(message, confirmText = 'Confirm', cancelText = 'Cancel') {
    return new Promise((resolve) => {
        const modalHtml = `
            <div class="modal fade" id="confirmModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Confirmation</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            ${message}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" id="cancelBtn">${cancelText}</button>
                            <button type="button" class="btn btn-danger" id="confirmBtn">${confirmText}</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        const modalDiv = document.createElement('div');
        modalDiv.innerHTML = modalHtml;
        document.body.appendChild(modalDiv);

        const modal = new bootstrap.Modal(document.getElementById('confirmModal'));
        modal.show();

        document.getElementById('confirmBtn').onclick = () => {
            modal.hide();
            resolve(true);
            setTimeout(() => modalDiv.remove(), 300);
        };

        document.getElementById('cancelBtn').onclick = () => {
            modal.hide();
            resolve(false);
            setTimeout(() => modalDiv.remove(), 300);
        };
    });
}
