import axios from 'axios'
import type { ChatApiResponse } from '../types/chat'

// ---------------------------------------------------------------------------
// Axios instance
// ---------------------------------------------------------------------------

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60_000, // 60 s — LLM calls can be slow
})

// ---------------------------------------------------------------------------
// Request / response interceptors
// ---------------------------------------------------------------------------

api.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    if (axios.isAxiosError(error)) {
      const status = error.response?.status
      const detail =
        (error.response?.data as { detail?: string } | undefined)?.detail ??
        error.message

      console.error(`[API] ${status ?? 'network'} — ${detail}`)
    }
    return Promise.reject(error)
  },
)

// ---------------------------------------------------------------------------
// Chat endpoint
// ---------------------------------------------------------------------------

/**
 * POST /chat
 *
 * Send a user message to the FastAPI backend and receive a typed response.
 * The backend routes to recommendation, comparison, or information internally.
 *
 * @param message - The user's raw shopping query.
 * @returns A fully-typed ChatApiResponse envelope.
 */
export async function sendMessage(message: string): Promise<ChatApiResponse> {
  const { data } = await api.post<ChatApiResponse>('/chat', { message })
  return data
}

export default api
