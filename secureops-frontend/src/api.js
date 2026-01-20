import axios from "axios";

const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1",
    timeout: 30000,
    withCredentials: true, // Important for HttpOnly Cookies (Refresh Token)
});

// --- Token Management (Memory Only) ---
let _accessToken = null;

export const setAccessToken = (token) => {
    _accessToken = token;
};

export const getAccessToken = () => _accessToken;

// --- Request Interceptor ---
api.interceptors.request.use(
    (config) => {
        if (_accessToken) {
            config.headers.Authorization = `Bearer ${_accessToken}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// --- Response Interceptor (Auto-Refresh) ---
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        // If 401 Unauthorized and not already retrying
        if (error.response?.status === 401 && !originalRequest._retry) {
            // Prevent infinite loops if refresh/login endpoints themselves fail
            if (originalRequest.url.includes("/auth/refresh") || originalRequest.url.includes("/auth/login")) {
                return Promise.reject(error);
            }

            originalRequest._retry = true;

            try {
                // Attempt to refresh (Using HTTP-Only Cookie)
                const { data } = await api.post("/auth/refresh");

                // Save new access token to MEMORY
                setAccessToken(data.access_token);

                // Retry original request with new token
                originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
                return api(originalRequest);

            } catch (refreshError) {
                // Refresh failed (cookie expired/invalid)
                _accessToken = null; // Clear invalid token
                return Promise.reject(refreshError);
            }
        }
        return Promise.reject(error);
    }
);

// --- API Service Wrapper ---
export const SafetyAPI = {
    // Auth
    login: async (email, password) => {
        const response = await api.post("/auth/login", { email, password });
        return response.data;
    },

    signup: async (email, password, role) => {
        const response = await api.post("/auth/signup", { email, password, role });
        return response.data;
    },

    logout: async () => {
        await api.post("/auth/logout");
        setAccessToken(null);
    },

    refreshToken: async () => {
        const response = await api.post("/auth/refresh");
        if (response.data.access_token) {
            setAccessToken(response.data.access_token);
        }
        return response.data;
    },

    getMe: async () => {
        const response = await api.get("/auth/me");
        return response.data;
    },

    // Upload & Results (Protected)
    upload: async (files, uploadType) => {
        const formData = new FormData();
        files.forEach(file => {
            formData.append('files', file);
        });
        formData.append('upload_type', uploadType);
        const response = await api.post('/videos/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return response.data;
    },

    getStatus: async (videoId) => {
        const response = await api.get(`/videos/${videoId}/status`);
        return response.data;
    },

    getSummary: async (uploadId) => {
        const response = await api.get(`/results/summary?upload_id=${uploadId || ''}`);
        return response.data;
    },

    getViolations: async (uploadId) => {
        const response = await api.get(`/results/violations?upload_id=${uploadId || ''}`);
        return response.data;
    },

    getProximityEvents: async (uploadId) => {
        const response = await api.get(`/results/proximity?upload_id=${uploadId || ''}`);
        return response.data;
    },

    getHealth: async () => {
        const response = await api.get("/health");
        return response.data;
    },

    downloadReport: async (uploadId) => {
        const response = await api.get(`/results/report?upload_id=${uploadId}`, {
            responseType: 'blob', // Important for PDF
        });
        return response.data;
    },

    chat: async (message) => {
        try {
            const response = await api.post('/chat/', { message: message });
            return response.data;
        } catch (error) {
            console.error("Chat failed:", error);
            throw error;
        }
    }
};

export { api };
export default SafetyAPI;
