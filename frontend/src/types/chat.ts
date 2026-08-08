// ---------------------------------------------------------------------------
// Product
// ---------------------------------------------------------------------------

/** A single product returned by the recommendation or comparison pipeline. */
export interface Product {
  id: string | null
  asin: string | null
  title: string
  brand: string | null
  category: string | null
  price: number | null
  average_rating: number | null
  rating_number: number | null
  image: string | null
  features: string[] | null
  ml_score: number
  ai_explanation: string | null
}

// ---------------------------------------------------------------------------
// API response shapes  (mirrors ChatResponse in backend/schemas/response_models.py)
// ---------------------------------------------------------------------------

/** Payload when type === "recommendation" */
export interface RecommendationData {
  products: Product[]
}

/** Payload when type === "comparison" */
export interface ComparisonData {
  comparison: string
  products: Product[]
}

/** Payload when type === "information" */
export interface InformationData {
  message: string
}

/** Payload when type === "error" */
export interface ErrorData {
  message?: string
}

/** Union of all possible data payloads */
export type ChatResponseData =
  | RecommendationData
  | ComparisonData
  | InformationData
  | ErrorData

/** The envelope returned by POST /chat */
export interface ChatApiResponse {
  success: boolean
  type: 'recommendation' | 'comparison' | 'information' | 'error'
  data: ChatResponseData
  error: string | null
}

// ---------------------------------------------------------------------------
// Chat history
// ---------------------------------------------------------------------------

/** A single entry in the chat thread rendered in the UI */
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  /** Raw text shown for user bubbles and information/error responses */
  text?: string
  /** Populated when type === "recommendation" */
  recommendations?: Product[]
  /** Populated when type === "comparison" */
  comparison?: ComparisonData
  /** The intent type the assistant resolved to */
  type?: 'recommendation' | 'comparison' | 'information' | 'error'
  timestamp: Date
}
