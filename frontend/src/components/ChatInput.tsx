import { useRef, useEffect } from 'react'

interface ChatInputProps {
  value: string
  onChange: (value: string) => void
  onSend: () => void
  isLoading: boolean
}

/**
 * Chat input bar pinned to the bottom of the viewport.
 *
 * - Enter sends the message.
 * - Shift+Enter inserts a newline.
 * - Send button is disabled while a request is in flight.
 * - Textarea auto-focuses on mount.
 * - Textarea grows up to 5 lines then scrolls.
 */
export default function ChatInput({
  value,
  onChange,
  onSend,
  isLoading,
}: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-focus on mount
  useEffect(() => {
    textareaRef.current?.focus()
  }, [])

  // Auto-resize textarea height as content grows
  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 140)}px`
  }, [value])

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (!isLoading && value.trim()) onSend()
    }
  }

  const canSend = !isLoading && value.trim().length > 0

  return (
    <div className="border-t border-gray-100 bg-white px-4 py-3">
      <div className="max-w-3xl mx-auto">
        <div className="flex items-end gap-3 bg-gray-50 border border-gray-200 rounded-2xl px-4 py-3 focus-within:border-blue-400 focus-within:ring-2 focus-within:ring-blue-100 transition-all">
          {/* Textarea */}
          <textarea
            ref={textareaRef}
            rows={1}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            placeholder="Ask me about beauty products..."
            aria-label="Chat message input"
            className="
              flex-1 resize-none bg-transparent text-sm text-gray-800
              placeholder-gray-400 outline-none leading-relaxed
              disabled:opacity-50 max-h-[140px] overflow-y-auto
            "
          />

          {/* Send button */}
          <button
            onClick={onSend}
            disabled={!canSend}
            aria-label="Send message"
            className="
              flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center
              transition-all duration-150
              bg-blue-600 text-white shadow-sm
              hover:bg-blue-700 active:scale-95
              disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-blue-600
            "
          >
            {isLoading ? (
              /* Spinner */
              <svg
                className="w-4 h-4 animate-spin"
                viewBox="0 0 24 24"
                fill="none"
                aria-hidden="true"
              >
                <circle
                  className="opacity-25"
                  cx="12" cy="12" r="10"
                  stroke="currentColor" strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
                />
              </svg>
            ) : (
              /* Send arrow */
              <svg
                className="w-4 h-4"
                viewBox="0 0 24 24"
                fill="currentColor"
                aria-hidden="true"
              >
                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
              </svg>
            )}
          </button>
        </div>

        <p className="text-center text-xs text-gray-400 mt-2">
          Press <kbd className="px-1 py-0.5 bg-gray-100 rounded text-gray-500 font-mono text-xs">Enter</kbd> to send
          &nbsp;·&nbsp;
          <kbd className="px-1 py-0.5 bg-gray-100 rounded text-gray-500 font-mono text-xs">Shift+Enter</kbd> for new line
        </p>
      </div>
    </div>
  )
}
