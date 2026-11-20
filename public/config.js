/*
 * Same-origin Flask deployment: leave API_BASE_URL empty.
 * Separate Vercel frontend + Render API: set API_BASE_URL to your public
 * Render service URL, e.g. https://upi-sentinel-api.onrender.com
 * Configure CORS_ORIGINS on your API to allow your exact Vercel domain.
 */
window.UPI_CONFIG = { API_BASE_URL: "" };
