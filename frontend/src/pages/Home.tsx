import { useState, useRef, useEffect, useCallback } from 'react'
import ChatMessage from '../components/ChatMessage'
import ChatInput from '../components/ChatInput'
import Loading from '../components/Loading'
import { sendMessage } from '../services/api'
import type {
  ChatMessage as ChatMessageType,
  ComparisonData,
  RecommendationData,
  InformationData,
  ErrorData,
} from '../types/chat'

// ---------------------------------------------------------------------------
// Empty state shown before the first message
// ---------------------------------------------------------------------------

function EmptyState({ onExample }: { onExample: (text: string) => void }) {
  const examples = [
    'Recommend a moisturizer for dry skin',
    'Compare CeraVe and Cetaphil moisturizers',
    'What is niacinamide?',
    'Best sunscreen under ₹500',
  ]

  return (
    <div className="flex flex-col items-center justify-center flex-1 gap-8 px-4 py-12 animate-fade-in">
      {/* Hero */}
      <div className="flex flex-col items-center gap-3 text-center">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center text-3xl shadow-lg">
          🤖
        </div>
        <h2 className="text-xl font-semibold text-gray-800">
          AI Shopping Assistant
        </h2>
        <p className="text-sm text-gray-500 max-w-sm">
          Ask me anything about beauty products. I'll recommend, compare, and
          explain — powered by AI and machine learning.
        </p>
      </div>

      {/* Example prompts */}
      <div className="flex flex-col gap-2 w-full max-w-sm">
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide text-center">
          Try asking
        </p>
        {examples.map((ex) => (
          <button
            key={ex}
            onClick={() => onExample(ex)}
            className="
              text-left text-sm text-gray-700 bg-white border border-gray-200
              rounded-xl px-4 py-3 hover:border-blue-300 hover:bg-blue-50
              hover:text-blue-700 transition-all duration-150 shadow-sm
            "
          >
            <span className="text-blue-400 mr-2">•</span>
            {ex}
          </button>
        ))}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Home page — chat orchestration
// ---------------------------------------------------------------------------

export default function Home() {
  const [messages, setMessages]   = useState<ChatMessageType[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const bottomRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to the latest message whenever the list changes.
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  // Append a message to the thread.
  const appendMessage = useCallback((msg: ChatMessageType) => {
    setMessages((prev) => [...prev, msg])
  }, [])

  // Handle send — called by ChatInput on Enter or button click.
  const handleSend = useCallback(async () => {
    const text = inputValue.trim()
    if (!text || isLoading) return

    // Optimistically append the user bubble.
    appendMessage({
      id:        crypto.randomUUID(),
      role:      'user',
      text,
      timestamp: new Date(),
    })
    setInputValue('')
    setIsLoading(true)

    try {
      const response = await sendMessage(text)

      if (!response.success || response.type === 'error') {
        const errData = response.data as ErrorData
        appendMessage({
          id:        crypto.randomUUID(),
          role:      'assistant',
          type:      'error',
          text:      errData?.message ?? response.error ?? 'Something went wrong. Please try again.',
          timestamp: new Date(),
        })
        return
      }

      // Build the assistant ChatMessage from the API envelope.
      const assistantMsg: ChatMessageType = {
        id:        crypto.randomUUID(),
        role:      'assistant',
        type:      response.type,
        timestamp: new Date(),
      }

      if (response.type === 'recommendation') {
        const d = response.data as RecommendationData
        assistantMsg.recommendations = d.products
      } else if (response.type === 'comparison') {
        const d = response.data as ComparisonData
        assistantMsg.comparison = d
      } else {
        // information or anything else
        const d = response.data as InformationData
        assistantMsg.text = d.message
      }

      appendMessage(assistantMsg)
    } catch {
      appendMessage({
        id:        crypto.randomUUID(),
        role:      'assistant',
        type:      'error',
        text:      'Something went wrong. Please try again.',
        timestamp: new Date(),
      })
    } finally {
      setIsLoading(false)
    }
  }, [inputValue, isLoading, appendMessage])

  // Clicking an example prompt fills the input and sends immediately.
  const handleExample = useCallback((text: string) => {
    setInputValue(text)
    // Use a microtask so state updates before handleSend reads inputValue.
    setTimeout(() => {
      setMessages((prev) => {
        // Build user message directly to avoid stale closure on inputValue.
        const userMsg: ChatMessageType = {
          id:        crypto.randomUUID(),
          role:      'user',
          text,
          timestamp: new Date(),
        }
        return [...prev, userMsg]
      })
      setInputValue('')
      setIsLoading(true)

      sendMessage(text)
        .then((response) => {
          if (!response.success || response.type === 'error') {
            const errData = response.data as ErrorData
            setMessages((prev) => [
              ...prev,
              {
                id:        crypto.randomUUID(),
                role:      'assistant',
                type:      'error' as const,
                text:      errData?.message ?? response.error ?? 'Something went wrong.',
                timestamp: new Date(),
              },
            ])
            return
          }

          const assistantMsg: ChatMessageType = {
            id:        crypto.randomUUID(),
            role:      'assistant',
            type:      response.type,
            timestamp: new Date(),
          }

          if (response.type === 'recommendation') {
            assistantMsg.recommendations = (response.data as RecommendationData).products
          } else if (response.type === 'comparison') {
            assistantMsg.comparison = response.data as ComparisonData
          } else {
            assistantMsg.text = (response.data as InformationData).message
          }

          setMessages((prev) => [...prev, assistantMsg])
        })
        .catch(() => {
          setMessages((prev) => [
            ...prev,
            {
              id:        crypto.randomUUID(),
              role:      'assistant',
              type:      'error' as const,
              text:      'Something went wrong. Please try again.',
              timestamp: new Date(),
            },
          ])
        })
        .finally(() => setIsLoading(false))
    }, 0)
  }, [])

  const hasMessages = messages.length > 0

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <header className="flex-shrink-0 flex items-center justify-between px-6 py-4 bg-white border-b border-gray-100 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center text-white text-sm shadow-sm">
            🤖
          </div>
          <div>
            <h1 className="text-sm font-semibold text-gray-900 leading-none">
              AI Shopping Assistant
            </h1>
            <p className="text-xs text-gray-400 mt-0.5">
              Powered by Groq · XGBoost · MongoDB
            </p>
          </div>
        </div>

        {/* Clear chat button — only when there are messages */}
        {hasMessages && (
          <button
            onClick={() => setMessages([])}
            className="text-xs text-gray-400 hover:text-gray-600 transition-colors px-3 py-1.5 rounded-lg hover:bg-gray-100"
          >
            Clear chat
          </button>
        )}
      </header>

      {/* ── Chat body ──────────────────────────────────────────────────── */}
      <main className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-3xl mx-auto flex flex-col gap-6">
          {!hasMessages ? (
            <EmptyState onExample={handleExample} />
          ) : (
            <>
              {messages.map((msg) => (
                <ChatMessage key={msg.id} message={msg} />
              ))}
              {isLoading && <Loading />}
            </>
          )}
          {/* Scroll anchor */}
          <div ref={bottomRef} />
        </div>
      </main>

      {/* ── Input bar ──────────────────────────────────────────────────── */}
      <ChatInput
        value={inputValue}
        onChange={setInputValue}
        onSend={handleSend}
        isLoading={isLoading}
      />
    </div>
  )
}
