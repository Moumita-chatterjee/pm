// In production (the Docker container) the backend serves the frontend from
// the same origin, so relative paths work. Under `next dev` (port 3000) the
// backend runs separately on :8000 (CORS-enabled for this in
// backend/app/main.py), so requests need an absolute base URL.
export const API_BASE_URL =
  process.env.NODE_ENV === "development" ? "http://localhost:8000" : "";
