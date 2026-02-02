/**
 * API Client for Authentication and Data Operations
 */

const API_BASE_URL = 'http://localhost:8000';

class APIClient {
    constructor() {
        this.baseURL = API_BASE_URL;
        this.token = localStorage.getItem('token');
    }

    // Helper method for making requests
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers,
        };

        if (this.token && !options.skipAuth) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        try {
            const response = await fetch(url, {
                ...options,
                headers,
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Request failed');
            }

            return await response.json();
        } catch (error) {
            console.error('API Request Error:', error);
            throw error;
        }
    }

    // Auth methods
    async login(email, password) {
        const data = await this.request('/api/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password }),
        });
        
        this.token = data.access_token;
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        
        return data;
    }

    async signup(email, password, full_name) {
        const data = await this.request('/api/auth/signup', {
            method: 'POST',
            body: JSON.stringify({ email, password, full_name, role: 'user' }),
        });
        
        this.token = data.access_token;
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        
        return data;
    }

    logout() {
        this.token = null;
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = 'landing.html';
    }

    getCurrentUser() {
        const userStr = localStorage.getItem('user');
        return userStr ? JSON.parse(userStr) : null;
    }

    isAuthenticated() {
        return !!this.token;
    }

    isAdmin() {
        const user = this.getCurrentUser();
        return user && user.role === 'admin';
    }

    // Product methods
    async getProducts(page = 1, pageSize = 20) {
        return this.request(`/api/admin/products?page=${page}&page_size=${pageSize}`);
    }

    async createProduct(formData) {
        const url = `${this.baseURL}/api/admin/products`;
        const headers = {
            'Authorization': `Bearer ${this.token}`,
        };

        const response = await fetch(url, {
            method: 'POST',
            headers,
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create product');
        }

        return await response.json();
    }

    // Analysis methods
    async scanProduct(productId, imageFile) {
        const formData = new FormData();
        formData.append('product_id', productId);
        formData.append('image', imageFile);

        const url = `${this.baseURL}/api/analysis/scan`;
        const headers = {
            'Authorization': `Bearer ${this.token}`,
        };

        const response = await fetch(url, {
            method: 'POST',
            headers,
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Scan failed');
        }

        return await response.json();
    }

    async getScanHistory(page = 1, pageSize = 20) {
        return this.request(`/api/analysis/history?page=${page}&page_size=${pageSize}`);
    }

    async getScanResult(scanId) {
        return this.request(`/api/analysis/results/${scanId}`);
    }

    async shareLocation(scanId, locationData) {
        return this.request('/api/analysis/location/share', {
            method: 'POST',
            body: JSON.stringify({
                scan_id: scanId,
                ...locationData,
                consent: true
            }),
        });
    }

    // Analytics methods
    async getDashboardStats() {
        return this.request('/api/analytics/dashboard');
    }

    async getTemporalTrends(days = 30) {
        return this.request(`/api/analytics/trends?days=${days}`);
    }

    async getProductAnalytics() {
        return this.request('/api/analytics/products');
    }

    async getLocationHeatmap() {
        return this.request('/api/analytics/locations/heatmap');
    }

    async getCompleteAnalytics(days = 30) {
        return this.request(`/api/analytics/complete?days=${days}`);
    }

    // User management (admin only)
    async getUsers(page = 1, pageSize = 50) {
        return this.request(`/api/admin/users?page=${page}&page_size=${pageSize}`);
    }

    async updateUser(email, updateData) {
        return this.request(`/api/admin/users/${email}`, {
            method: 'PATCH',
            body: JSON.stringify(updateData),
        });
    }
}

// Global API client instance
const apiClient = new APIClient();

// Utility functions
function showError(message) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-danger';
    alert.innerHTML = `<strong>Error:</strong> ${message}`;
    
    const container = document.querySelector('.container') || document.body;
    container.insertBefore(alert, container.firstChild);
    
    setTimeout(() => alert.remove(), 5000);
}

function showSuccess(message) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-success';
    alert.innerHTML = `<strong>Success:</strong> ${message}`;
    
    const container = document.querySelector('.container') || document.body;
    container.insertBefore(alert, container.firstChild);
    
    setTimeout(() => alert.remove(), 5000);
}

function showLoading(element) {
    element.disabled = true;
    element.innerHTML = '<span class="spinner"></span> Processing...';
}

function hideLoading(element, originalText) {
    element.disabled = false;
    element.innerHTML = originalText;
}

// Check authentication on protected pages
function requireAuth() {
    if (!apiClient.isAuthenticated()) {
        window.location.href = 'login.html';
        return false;
    }
    return true;
}

function requireAdmin() {
    if (!apiClient.isAuthenticated() || !apiClient.isAdmin()) {
        window.location.href = 'landing.html';
        return false;
    }
    return true;
}
