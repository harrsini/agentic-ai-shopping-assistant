import type { ComparisonData } from '../types/chat'
import ProductCard from './ProductCard'

interface ComparisonCardProps {
  data: ComparisonData
}

/**
 * Renders a side-by-side product comparison.
 *
 * Layout:
 *  - Two ProductCards displayed side by side (stacked on mobile).
 *  - AI-generated comparison text below both cards.
 */
export default function ComparisonCard({ data }: ComparisonCardProps) {
  const { products, comparison } = data

  return (
    <div className="flex flex-col gap-4 w-full animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-2">
        <span className="text-blue-500 text-lg" aria-hidden="true">⚖️</span>
        <h3 className="font-semibold text-gray-800 text-sm">Product Comparison</h3>
      </div>

      {/* Side-by-side cards */}
      {products.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {products.map((product, i) => (
            <div key={product.asin ?? i} className="flex flex-col gap-1">
              <span className="text-xs font-semibold text-blue-600 uppercase tracking-wide pl-1">
                {i === 0 ? 'Option A' : 'Option B'}
              </span>
              <ProductCard product={product} />
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-gray-400 italic">No products available for comparison.</p>
      )}

      {/* AI comparison text */}
      {comparison && (
        <div className="bg-blue-50 border border-blue-100 rounded-2xl p-4">
          <div className="flex items-start gap-2">
            <span className="text-blue-500 mt-0.5 flex-shrink-0" aria-hidden="true">💡</span>
            <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">
              {comparison}
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
