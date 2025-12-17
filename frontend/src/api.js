import axios from 'axios';

// Create an Axios instance with dynamic base URL
let baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:5000';

// Render env var 'host' comes without protocol, so we add it if missing
if (baseUrl && !baseUrl.startsWith('http')) {
    baseUrl = `https://${baseUrl}`;
}

const api = axios.create({
    baseURL: baseUrl,
    headers: {
        'Content-Type': 'application/json',
    },
});
console.log("API Base URL:", baseUrl);

export default api;
