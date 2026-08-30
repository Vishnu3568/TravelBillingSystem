import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:9000/api",
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("jwtToken");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

const MAX_RETRIES = 2;

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const config = error.config;

    // Handle 401 Unauthorized
    if (error.response && error.response.status === 401) {
      localStorage.removeItem("jwtToken");
      localStorage.removeItem("username");
      localStorage.removeItem("role");

      if (!window.location.pathname.endsWith("/login")) {
        window.location.href = "/login";
      }
      return Promise.reject(error);
    }

    // Auto-retry transient network/server errors (502, 503, 504, network timeout) on GET requests
    const isGetRequest = config && config.method && config.method.toLowerCase() === "get";
    const isTransientError =
      !error.response ||
      [502, 503, 504].includes(error.response.status) ||
      error.code === "ECONNABORTED";

    if (isGetRequest && isTransientError) {
      config.__retryCount = config.__retryCount || 0;
      if (config.__retryCount < MAX_RETRIES) {
        config.__retryCount += 1;
        const delay = Math.pow(2, config.__retryCount) * 500;
        await new Promise((resolve) => setTimeout(resolve, delay));
        return api(config);
      }
    }

    return Promise.reject(error);
  }
);

export default api;
