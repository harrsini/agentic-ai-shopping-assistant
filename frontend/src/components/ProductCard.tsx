import type { Product } from '../types/chat'

interface ProductCardProps {
  product: Product
}

/** Renders star icons for a given numeric rating (0–5). */
function StarRating({ rating }: { rating: number }) {
  const full  = Math.floor(rating)
  const half  = rating % 1 >= 0.5
  const empty = 5 - full - (half ? 1 : 0)

  return (
    <span className="flex items-center gap-0.5" aria-label={`${rating} out of 5 stars`}>
      {Array.from({ length: full  }).map((_, i) => (
        <span key={`f${i}`} className="text-amber-400 text-sm">★</span>
      ))}
      {half && <span className="text-amber-400 text-sm">½</span>}
      {Array.from({ length: empty }).map((_, i) => (
        <span key={`e${i}`} className="text-gray-300 text-sm">★</span>
      ))}
    </span>
  )
}

/** Formats a price number. Falls back to "N/A" when null. */
function formatPrice(price: number | null): string {
  if (price === null) return 'N/A'
  return `₹${price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`
}

/**
 * A rich product card showing image, title, brand, rating, reviews,
 * price, ML score and AI explanation.
 */
export default function ProductCard({ product }: ProductCardProps) {
  const {
    title,
    brand,
    price,
    average_rating,
    rating_number,
    image,
    features,
    ml_score,
    ai_explanation,
  } = product

  return (
    <article className="
      group flex flex-col bg-white border border-gray-100 rounded-2xl shadow-sm
      overflow-hidden transition-all duration-200
      hover:shadow-md hover:-translate-y-0.5
    ">
      {/* Product image */}
      <div className="w-full h-44 bg-gray-50 flex items-center justify-center overflow-hidden">
        {image ? (
          <img
            src={image}
            alt={title}
            className="h-full w-full object-contain p-3 transition-transform duration-200 group-hover:scale-105"
            loading="lazy"
          />
        ) : (
          <span className="text-4xl opacity-30" aria-hidden="true">🛍️</span>
        )}
      </div>

      {/* Card body */}
      <div className="flex flex-col gap-2 p-4 flex-1">
        {/* Title */}
        <h3 className="font-semibold text-gray-900 text-sm leading-snug line-clamp-2">
          {title}
        </h3>

        {/* Brand */}
        {brand && (
          <p className="text-xs text-gray-500">
            Brand: <span className="font-medium text-gray-700">{brand}</span>
          </p>
        )}

        {/* Rating row */}
        {average_rating !== null && (
          <div className="flex items-center gap-2">
            <StarRating rating={average_rating} />
            <span className="text-xs font-semibold text-gray-700">{average_rating}</span>
            {rating_number !== null && (
              <span className="text-xs text-gray-400">
                ({rating_number.toLocaleString()} reviews)
              </span>
            )}
          </div>
        )}

        {/* Price + ML score row */}
        <div className="flex items-center justify-between mt-1">
          <span className="text-base font-bold text-blue-600">
            {formatPrice(price)}
          </span>
          <span
            className="text-xs font-medium bg-blue-50 text-blue-600 border border-blue-100 rounded-full px-2 py-0.5"
            title="ML relevance score"
          >
            ML {ml_score.toFixed(2)}
          </span>
        </div>

        {/* Top features */}
        {features && features.length > 0 && (
          <ul className="mt-1 space-y-0.5">
            {features.slice(0, 3).map((f, i) => (
              <li key={i} className="flex items-start gap-1.5 text-xs text-gray-500">
                <span className="mt-0.5 text-blue-400 flex-shrink-0">•</span>
                <span className="line-clamp-1">{f}</span>
              </li>
            ))}
          </ul>
        )}

        {/* AI explanation */}
        {ai_explanation && (
          <div className="mt-2 pt-2 border-t border-gray-50">
            <p className="text-xs text-gray-600 italic leading-relaxed line-clamp-3">
              {ai_explanation}
            </p>
          </div>
        )}
      </div>
    </article>
  )
}
