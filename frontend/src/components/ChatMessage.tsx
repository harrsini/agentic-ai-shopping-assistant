import type { ChatMessage as ChatMessageType, ComparisonData } from '../types/chat'
import ProductCard from './ProductCard'
import ComparisonCard from './ComparisonCard'

interface ChatMessageProps {
  message: ChatMessageType
}

// ---------------------------------------------------------------------------
// User bubble
// ---------------------------------------------------------------------------

function UserBubble({ text }: { text: string }) {
  return (
    <div className="flex items-end justify-end gap-2 animate-fade-in">
      <div className="max-w-[75%] bg-blue-600 text-white px-4 py-3 rounded-2xl rounded-br-sm shadow-sm">
        <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">{text}</p>
      </div>
      {/* User avatar */}
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-sm">
        👤
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Assistant bubble wrapper — shared chrome for all assistant responses
// ---------------------------------------------------------------------------

function AssistantBubble({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-start gap-3 animate-fade-in">
      {/* Bot avatar */}
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center text-white text-sm shadow-sm">
        🤖
      </div>
      <div className="flex-1 min-w-0">{children}</div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Information response
// ---------------------------------------------------------------------------

function InformationMessage({ text }: { text: string }) {
  return (
    <AssistantBubble>
      <div className="bg-white border border-gray-100 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
        <p className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap break-words">
          {text}
        </p>
      </div>
    </AssistantBubble>
  )
}

// ---------------------------------------------------------------------------
// Recommendation response
// ---------------------------------------------------------------------------

function RecommendationMessage({
  products,
}: {
  products: ChatMessageType['recommendations']
}) {
  if (!products || products.length === 0) {
    return (
      <AssistantBubble>
        <div className="bg-white border border-gray-100 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
          <p className="text-sm text-gray-500 italic">
            No recommendations found. Try rephrasing your query.
          </p>
        </div>
      </AssistantBubble>
    )
  }

  return (
    <AssistantBubble>
      <div className="flex flex-col gap-4">
        {/* Header */}
        <div className="bg-white border border-gray-100 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
          <p className="text-sm text-gray-800">
            Here are the top <span className="font-semibold text-blue-600">{products.length}</span>{' '}
            recommendations based on your query:
          </p>
        </div>

        {/* Product grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {products.map((product, i) => (
            <ProductCard key={product.asin ?? i} product={product} />
          ))}
        </div>
      </div>
    </AssistantBubble>
  )
}

// ---------------------------------------------------------------------------
// Comparison response
// ---------------------------------------------------------------------------

function ComparisonMessage({ data }: { data: ComparisonData }) {
  return (
    <AssistantBubble>
      <ComparisonCard data={data} />
    </AssistantBubble>
  )
}

// ---------------------------------------------------------------------------
// Error response
// ---------------------------------------------------------------------------

function ErrorMessage({ text }: { text: string }) {
  return (
    <AssistantBubble>
      <div className="bg-red-50 border border-red-100 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
        <div className="flex items-start gap-2">
          <span className="text-red-400 flex-shrink-0" aria-hidden="true">⚠️</span>
          <p className="text-sm text-red-700 leading-relaxed">{text}</p>
        </div>
      </div>
    </AssistantBubble>
  )
}

// ---------------------------------------------------------------------------
// Main dispatcher component
// ---------------------------------------------------------------------------

/**
 * Renders a single chat thread entry.
 *
 * Routes to the correct sub-component based on role + type:
 *  - role=user              → UserBubble
 *  - role=assistant, type=recommendation → RecommendationMessage
 *  - role=assistant, type=comparison     → ComparisonMessage
 *  - role=assistant, type=information    → InformationMessage
 *  - role=assistant, type=error          → ErrorMessage
 */
export default function ChatMessage({ message }: ChatMessageProps) {
  const { role, type, text, recommendations, comparison } = message

  if (role === 'user') {
    return <UserBubble text={text ?? ''} />
  }

  switch (type) {
    case 'recommendation':
      return <RecommendationMessage products={recommendations} />

    case 'comparison':
      return comparison ? (
        <ComparisonMessage data={comparison} />
      ) : (
        <InformationMessage text={text ?? ''} />
      )

    case 'error':
      return (
        <ErrorMessage
          text={text ?? 'Something went wrong. Please try again.'}
        />
      )

    case 'information':
    default:
      return <InformationMessage text={text ?? ''} />
  }
}
